import http.server
import socketserver
import json
import sqlite3
import os
import re
import urllib.parse
import mimetypes
from datetime import datetime

PORT = int(os.environ.get("PORT", 3000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "public")
DB_PATH = os.path.join(BASE_DIR, "data", "bible.db")
STRONG_DICT_PATH = os.path.join(BASE_DIR, "data", "strong_dict.json")

strong_dict = {}
if os.path.exists(STRONG_DICT_PATH):
    try:
        with open(STRONG_DICT_PATH, "r", encoding="utf-8") as f:
            strong_dict = json.load(f)
    except Exception as e:
        print("Strong dict load error:", e)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class BibleRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api_get(path, query)
        else:
            # 정적 파일 또는 SPA fallback
            file_path = os.path.join(PUBLIC_DIR, path.lstrip("/"))
            if not os.path.exists(file_path) or os.path.isdir(file_path):
                # index.html 서빙
                self.serve_file(os.path.join(PUBLIC_DIR, "index.html"), "text/html; charset=utf-8")
            else:
                mime_type, _ = mimetypes.guess_type(file_path)
                if path.endswith(".js"):
                    mime_type = "application/javascript; charset=utf-8"
                elif path.endswith(".css"):
                    mime_type = "text/css; charset=utf-8"
                elif path.endswith(".json") or path.endswith(".manifest"):
                    mime_type = "application/json; charset=utf-8"
                self.serve_file(file_path, mime_type or "application/octet-stream")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body) if body else {}
            except Exception:
                data = {}
            self.handle_api_post(path, data)
        else:
            self.send_error(404, "Not Found")

    def serve_file(self, full_path, content_type):
        if not os.path.exists(full_path):
            self.send_error(404, "File Not Found")
            return
        try:
            with open(full_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

    def send_json(self, data, status=200):
        res_bytes = json.dumps({"success": True, "data": data}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(res_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(res_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def handle_api_get(self, path, query):
        conn = get_db()
        cur = conn.cursor()

        try:
            # 1. 책 목록
            if path == "/api/books":
                cur.execute("SELECT id, name, abbr, eng_name, eng_abbr, testament, category, chapters FROM books ORDER BY id ASC;")
                rows = [dict(r) for r in cur.fetchall()]
                self.send_json(rows)

            # 2. 장별 성경 본문
            elif path.startswith("/api/chapter/"):
                unit_code = int(path.split("/")[-1])
                cur.execute("""
                    SELECT unit_code, book_id, chapter, jeol,
                           stitle_rv, stitle_ko, stitle_nw, stitle_ez, stitle_wr,
                           stitle_nv, stitle_nt, stitle_es, stitle_nb, stitle_kj,
                           phrase_rv, phrase_ko, phrase_nw, phrase_ez, phrase_wr,
                           phrase_nv, phrase_nt, phrase_es, phrase_nb, phrase_kj
                    FROM verses WHERE unit_code = ? ORDER BY jeol ASC;
                """, (unit_code,))
                verses = [dict(r) for r in cur.fetchall()]

                # 하이라이트, 북마크, 메모 매핑
                cur.execute("SELECT jeol, color FROM user_highlights WHERE unit_code = ?;", (unit_code,))
                hl_map = {r["jeol"]: r["color"] for r in cur.fetchall()}

                cur.execute("SELECT id, jeol, label FROM user_bookmarks WHERE unit_code = ?;", (unit_code,))
                bm_map = {r["jeol"]: dict(r) for r in cur.fetchall()}

                cur.execute("SELECT id, jeol, content, updated_at FROM user_notes WHERE unit_code = ?;", (unit_code,))
                note_map = {r["jeol"]: dict(r) for r in cur.fetchall()}

                cur.execute("SELECT read_count, last_read_at FROM user_reading_log WHERE unit_code = ?;", (unit_code,))
                read_row = cur.fetchone()

                for v in verses:
                    j = v["jeol"]
                    v["highlight"] = hl_map.get(j)
                    v["bookmark"] = bm_map.get(j)
                    v["note"] = note_map.get(j)

                self.send_json({
                    "unit_code": unit_code,
                    "is_read": bool(read_row),
                    "read_info": dict(read_row) if read_row else None,
                    "verses": verses
                })

            # 3. 절 상세 (원어 스트롱 분해 + 관주)
            elif path.startswith("/api/verse/"):
                parts = path.strip("/").split("/")
                unit_code = int(parts[2])
                jeol = int(parts[3])

                cur.execute("SELECT * FROM verses WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
                verse_row = cur.fetchone()
                if not verse_row:
                    self.send_json(None, 404)
                    return

                verse_data = dict(verse_row)

                # 스트롱 분해
                cur.execute("""
                    SELECT phrase_order, strong_code, phrase, bracket, space 
                    FROM strong_phrases WHERE unit_code = ? AND jeol = ? ORDER BY phrase_order ASC;
                """, (unit_code, jeol))
                strongs = []
                for s in cur.fetchall():
                    sd = dict(s)
                    code = sd.get("strong_code")
                    dict_info = strong_dict.get(code, {}) if code else {}
                    sd["original"] = dict_info.get("original", code or "")
                    sd["translit"] = dict_info.get("translit", "")
                    sd["pronounce"] = dict_info.get("pronounce", "")
                    sd["meaning"] = dict_info.get("meaning", "")
                    sd["definition"] = dict_info.get("definition", "")
                    strongs.append(sd)

                verse_data["strongs"] = strongs

                # 관주
                cur.execute("SELECT version, kind, mark, explains, link_ids FROM cross_references WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
                verse_data["cross_references"] = [dict(r) for r in cur.fetchall()]

                self.send_json(verse_data)

            # 4. 스트롱 코드 단독 사전 조회
            elif path.startswith("/api/strong/"):
                code = path.split("/")[-1].upper()
                info = strong_dict.get(code)
                if info:
                    self.send_json({"code": code, **info})
                else:
                    self.send_json({
                        "code": code,
                        "original": "원어 어휘",
                        "translit": code,
                        "meaning": f"Strong's {code}",
                        "definition": f"성경 원어 번호 {code} 어휘입니다."
                    })

            # 4.1 연관 성경 구절(병행 본문) 고속 조회 API
            elif path == "/api/lookup-ref":
                ref_param = query.get("ref", [""])[0].strip()
                version = query.get("version", ["rv"])[0]

                # 약어 맵핑 테이블
                abbr_map = {
                    "창": 1, "출": 2, "레": 3, "민": 4, "신": 5, "수": 6, "삿": 7, "룻": 8, "삼상": 9, "삼하": 10,
                    "왕상": 11, "왕하": 12, "대상": 13, "대하": 14, "스": 15, "느": 16, "에": 17, "욥": 18, "시": 19, "잠": 20,
                    "전": 21, "아": 22, "사": 23, "렘": 24, "애": 25, "겔": 26, "단": 27, "호": 28, "욜": 29, "암": 30,
                    "옵": 31, "욘": 32, "미": 33, "나": 34, "합": 35, "습": 36, "학": 37, "슥": 38, "말": 39, "마": 40,
                    "막": 41, "눅": 42, "요": 43, "행": 44, "롬": 45, "고전": 46, "고후": 47, "갈": 48, "엡": 49, "빌": 50,
                    "골": 51, "살전": 52, "살후": 53, "딤전": 54, "딤후": 55, "딛": 56, "몬": 57, "히": 58, "약": 59, "벧전": 60,
                    "벧후": 61, "요일": 62, "요이": 63, "요삼": 64, "유": 65, "계": 66,
                    "Gen": 1, "Exo": 2, "Lev": 3, "Num": 4, "Deu": 5, "Jos": 6, "Jdg": 7, "Rut": 8, "1Sa": 9, "2Sa": 10,
                    "1Ki": 11, "2Ki": 12, "1Ch": 13, "2Ch": 14, "Ezr": 15, "Neh": 16, "Est": 17, "Job": 18, "Psa": 19, "Pro": 20,
                    "Ecc": 21, "Sng": 22, "Isa": 23, "Jer": 24, "Lam": 25, "Ezk": 26, "Dan": 27, "Hos": 28, "Jol": 29, "Amo": 30,
                    "Oba": 31, "Jon": 32, "Mic": 33, "Nam": 34, "Hab": 35, "Zep": 36, "Hag": 37, "Zec": 38, "Mal": 39, "Mat": 40,
                    "Mrk": 41, "Luk": 42, "Jhn": 43, "Act": 44, "Rom": 45, "1Co": 46, "2Co": 47, "Gal": 48, "Eph": 49, "Php": 50,
                    "Col": 51, "1Th": 52, "2Th": 53, "1Ti": 54, "2Ti": 55, "Tit": 56, "Phm": 57, "Heb": 58, "Jas": 59, "1Pe": 60,
                    "2Pe": 61, "1Jn": 62, "2Jn": 63, "3Jn": 64, "Jud": 65, "Rev": 66
                }

                # 세미콜론이나 쉼표로 분할하여 파싱
                parts = re.split(r'[;,]', ref_param)
                verses_result = []
                last_book_id = None
                last_chapter = None

                for p in parts:
                    p = p.strip()
                    if not p:
                        continue
                    
                    # 책 약어와 장:절을 정확하게 분리 (예: 막9:50, 눅14:34-35, 41-42)
                    m = re.match(r'^([1-3]?[가-힣]+|[1-3]?[a-zA-Z]+)?\s*(?:(\d+):)?(\d+)(?:-(\d+))?$', p)
                    if m:
                        b_str, ch_str, j_start_str, j_end_str = m.groups()
                        if b_str and b_str in abbr_map:
                            last_book_id = abbr_map[b_str]
                        if ch_str is not None:
                            last_chapter = int(ch_str)
                        
                        j_start = int(j_start_str) if j_start_str else 1
                        j_end = int(j_end_str) if j_end_str else j_start

                        if last_book_id and last_chapter:
                            unit_code = last_book_id * 1000 + last_chapter
                            cur.execute("""
                                SELECT v.unit_code, v.book_id, v.chapter, v.jeol,
                                       v.phrase_rv, v.phrase_ko, v.phrase_nw, v.phrase_ez, v.phrase_wr,
                                       v.phrase_nv, v.phrase_nt, v.phrase_es, v.phrase_nb, v.phrase_kj,
                                       b.name as book_name, b.eng_name as book_eng_name
                                FROM verses v JOIN books b ON v.book_id = b.id
                                WHERE v.unit_code = ? AND v.jeol >= ? AND v.jeol <= ?
                                ORDER BY v.jeol ASC;
                            """, (unit_code, j_start, j_end))
                            for r in cur.fetchall():
                                verses_result.append(dict(r))

                self.send_json({
                    "ref": ref_param,
                    "version": version,
                    "count": len(verses_result),
                    "verses": verses_result
                })

            # 5. 검색
            elif path == "/api/search":
                q = query.get("q", [""])[0].strip()
                version = query.get("version", ["rv"])[0]
                limit = int(query.get("limit", [50])[0])
                offset = int(query.get("offset", [0])[0])

                if not q:
                    self.send_json({"query": "", "version": version, "total": 0, "items": []})
                    return

                col_map = {
                    "rv": "phrase_rv", "ko": "phrase_ko", "nw": "phrase_nw", "ez": "phrase_ez",
                    "wr": "phrase_wr", "nv": "phrase_nv", "nt": "phrase_nt", "es": "phrase_es",
                    "nb": "phrase_nb", "kj": "phrase_kj"
                }
                col = col_map.get(version, "phrase_rv")

                cur.execute(f"SELECT count(*) as cnt FROM verses WHERE {col} LIKE ?;", (f"%{q}%",))
                total = cur.fetchone()["cnt"]

                cur.execute(f"""
                    SELECT v.unit_code, v.book_id, v.chapter, v.jeol, v.stitle_rv, v.{col} as text,
                           b.name as book_name, b.abbr as book_abbr
                    FROM verses v JOIN books b ON v.book_id = b.id
                    WHERE v.{col} LIKE ?
                    ORDER BY v.unit_code ASC, v.jeol ASC
                    LIMIT ? OFFSET ?;
                """, (f"%{q}%", limit, offset))
                items = [dict(r) for r in cur.fetchall()]

                self.send_json({"query": q, "version": version, "total": total, "items": items})

            # 6. 오늘의 말씀
            elif path == "/api/today":
                day_of_year = datetime.now().timetuple().tm_yday
                cur.execute("SELECT count(*) as cnt FROM today_words;")
                tw_cnt = cur.fetchone()["cnt"] or 1
                cur.execute("SELECT count(*) as cnt FROM one_line_thanks;")
                th_cnt = cur.fetchone()["cnt"] or 1

                word_id = (day_of_year % tw_cnt) + 1
                thank_id = (day_of_year % th_cnt) + 1

                cur.execute("SELECT * FROM today_words WHERE id = ?;", (word_id,))
                tw = cur.fetchone()
                today_verse = None
                if tw:
                    cur.execute("SELECT v.*, b.name as book_name FROM verses v JOIN books b ON v.book_id = b.id WHERE v.unit_code = ? AND v.jeol = ?;", (tw["unit_code"], tw["jeol_start"]))
                    v_row = cur.fetchone()
                    if v_row: today_verse = dict(v_row)

                cur.execute("SELECT text FROM one_line_thanks WHERE id = ?;", (thank_id,))
                th_row = cur.fetchone()

                self.send_json({
                    "dayOfYear": day_of_year,
                    "today_word": today_verse,
                    "one_line_thanks": th_row["text"] if th_row else "항상 기뻐하라 쉬지 말고 기도하라 범사에 감사하라"
                })

            # 7. 통독 플랜 및 통계
            elif path == "/api/reading-plan":
                day = int(query.get("day", [1])[0])
                cur.execute("SELECT * FROM reading_plans WHERE day = ?;", (day,))
                plan = cur.fetchone()
                cur.execute("SELECT count(*) as cnt FROM user_reading_log;")
                read_cnt = cur.fetchone()["cnt"]
                self.send_json({
                    "day": day,
                    "plan": dict(plan) if plan else None,
                    "progress": {
                        "total": 1189,
                        "read": read_cnt,
                        "percentage": round((read_cnt / 1189) * 100, 1)
                    }
                })

            elif path == "/api/reading-stats":
                cur.execute("SELECT unit_code FROM user_reading_log;")
                read_list = [r["unit_code"] for r in cur.fetchall()]
                ot_read = sum(1 for u in read_list if u // 1000 <= 39)
                nt_read = sum(1 for u in read_list if u // 1000 > 39)
                self.send_json({
                    "total": 1189,
                    "read_total": len(read_list),
                    "percentage": round((len(read_list) / 1189) * 100, 1),
                    "ot": {"total": 929, "read": ot_read, "percentage": round((ot_read / 929) * 100, 1)},
                    "nt": {"total": 260, "read": nt_read, "percentage": round((nt_read / 260) * 100, 1)}
                })

            elif path == "/api/user/bookmarks":
                cur.execute("""
                    SELECT b.id, b.unit_code, b.jeol, b.label, b.created_at,
                           bk.name as book_name, v.chapter, v.phrase_rv as text
                    FROM user_bookmarks b
                    JOIN verses v ON b.unit_code = v.unit_code AND b.jeol = v.jeol
                    JOIN books bk ON v.book_id = bk.id
                    ORDER BY b.created_at DESC;
                """)
                self.send_json([dict(r) for r in cur.fetchall()])

            elif path == "/api/user/notes":
                cur.execute("""
                    SELECT n.id, n.unit_code, n.jeol, n.content, n.updated_at,
                           bk.name as book_name, v.chapter, v.phrase_rv as text
                    FROM user_notes n
                    JOIN verses v ON n.unit_code = v.unit_code AND n.jeol = v.jeol
                    JOIN books bk ON v.book_id = bk.id
                    ORDER BY n.updated_at DESC;
                """)
                self.send_json([dict(r) for r in cur.fetchall()])

            else:
                self.send_json(None, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
        finally:
            conn.close()

    def handle_api_post(self, path, data):
        conn = get_db()
        cur = conn.cursor()

        try:
            if path == "/api/user/highlight":
                unit = int(data.get("unit_code"))
                jeol = int(data.get("jeol"))
                color = data.get("color", "none")
                hid = f"{unit}_{jeol}"

                if color == "none" or not color:
                    cur.execute("DELETE FROM user_highlights WHERE unit_code = ? AND jeol = ?;", (unit, jeol))
                else:
                    cur.execute("""
                        INSERT INTO user_highlights (id, unit_code, jeol, color, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(id) DO UPDATE SET color = excluded.color, updated_at = CURRENT_TIMESTAMP;
                    """, (hid, unit, jeol, color))
                conn.commit()
                self.send_json({"saved": True, "color": color})

            elif path == "/api/user/bookmark":
                unit = int(data.get("unit_code"))
                jeol = int(data.get("jeol"))
                label = data.get("label", "")
                bid = f"{unit}_{jeol}"

                cur.execute("SELECT id FROM user_bookmarks WHERE id = ?;", (bid,))
                if cur.fetchone():
                    cur.execute("DELETE FROM user_bookmarks WHERE id = ?;", (bid,))
                    conn.commit()
                    self.send_json({"bookmarked": False})
                else:
                    cur.execute("INSERT INTO user_bookmarks (id, unit_code, jeol, label) VALUES (?, ?, ?, ?);", (bid, unit, jeol, label))
                    conn.commit()
                    self.send_json({"bookmarked": True})

            elif path == "/api/user/note":
                unit = int(data.get("unit_code"))
                jeol = int(data.get("jeol"))
                content = (data.get("content") or "").strip()
                nid = f"{unit}_{jeol}"

                if not content:
                    cur.execute("DELETE FROM user_notes WHERE id = ?;", (nid,))
                else:
                    cur.execute("""
                        INSERT INTO user_notes (id, unit_code, jeol, content, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(id) DO UPDATE SET content = excluded.content, updated_at = CURRENT_TIMESTAMP;
                    """, (nid, unit, jeol, content))
                conn.commit()
                self.send_json({"saved": True})

            elif path == "/api/user/reading-toggle":
                unit = int(data.get("unit_code"))
                cur.execute("SELECT unit_code FROM user_reading_log WHERE unit_code = ?;", (unit,))
                if cur.fetchone():
                    cur.execute("DELETE FROM user_reading_log WHERE unit_code = ?;", (unit,))
                    conn.commit()
                    self.send_json({"is_read": False})
                else:
                    cur.execute("INSERT INTO user_reading_log (unit_code, read_count) VALUES (?, 1);", (unit,))
                    conn.commit()
                    self.send_json({"is_read": True})
            else:
                self.send_json(None, 404)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
        finally:
            conn.close()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    with ThreadedTCPServer(("", PORT), BibleRequestHandler) as httpd:
        print("====================================================")
        print(f" WordBible Full-Stack Server Running on: http://localhost:{PORT}")
        print("====================================================")
        httpd.serve_forever()
