import http.server
import json
import sqlite3
import os
import re
import urllib.parse
from datetime import datetime

import gzip
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(ROOT_DIR, "server", "data", "bible.db")
DB_GZ_PATH = os.path.join(ROOT_DIR, "server", "data", "bible.db.gz")
TMP_DB_PATH = "/tmp/bible.db"

def ensure_db_extracted():
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 1000000:
        return DB_PATH
    if os.path.exists(TMP_DB_PATH) and os.path.getsize(TMP_DB_PATH) > 1000000:
        return TMP_DB_PATH
    if os.path.exists(DB_GZ_PATH):
        target = TMP_DB_PATH if os.path.exists("/tmp") else DB_PATH
        try:
            with gzip.open(DB_GZ_PATH, 'rb') as f_in:
                with open(target, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return target
        except Exception as e:
            print("DB Decompression error:", e)
    return DB_PATH

def get_db():
    active_path = ensure_db_extracted()
    conn = sqlite3.connect(active_path)
    conn.row_factory = sqlite3.Row
    return conn

class handler(http.server.BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        res_bytes = json.dumps({"success": True, "data": data}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(res_bytes)))
        self.send_header("Cache-Control", "public, max-age=600, s-maxage=3600")
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

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        conn = get_db()
        cur = conn.cursor()

        try:
            # 1. 책 목록
            if path == "/api/books" or path.endswith("/books"):
                cur.execute("SELECT id, name, abbr, eng_name, eng_abbr, testament, category, chapters FROM books ORDER BY id ASC;")
                rows = [dict(r) for r in cur.fetchall()]
                self.send_json(rows)

            # 2. 장별 성경 본문
            elif "/chapter/" in path:
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

                cur.execute("SELECT jeol, color FROM user_highlights WHERE unit_code = ?;", (unit_code,))
                hl_map = {r["jeol"]: r["color"] for r in cur.fetchall()}

                cur.execute("SELECT read_count, last_read_at FROM user_reading_log WHERE unit_code = ?;", (unit_code,))
                read_row = cur.fetchone()

                for v in verses:
                    j = v["jeol"]
                    v["highlight"] = hl_map.get(j)

                self.send_json({
                    "unit_code": unit_code,
                    "is_read": bool(read_row),
                    "read_info": dict(read_row) if read_row else None,
                    "verses": verses
                })

            # 3. 절 상세 (원어 스트롱 분해 + 관주)
            elif "/verse/" in path:
                parts = path.strip("/").split("/")
                unit_code = int(parts[-2])
                jeol = int(parts[-1])

                cur.execute("""
                    SELECT unit_code, book_id, chapter, jeol,
                           phrase_rv, phrase_ko, phrase_nw, phrase_ez, phrase_wr,
                           phrase_nv, phrase_nt, phrase_es, phrase_nb, phrase_kj
                    FROM verses WHERE unit_code = ? AND jeol = ?;
                """, (unit_code, jeol))
                row = cur.fetchone()
                if not row:
                    self.send_json({"error": "Verse not found"}, status=404)
                    return

                verse_data = dict(row)

                cur.execute("""
                    SELECT version, unit_code, jeol, kind, mark, explains, link_ids
                    FROM cross_references
                    WHERE unit_code = ? AND jeol = ?
                    ORDER BY id ASC;
                """, (unit_code, jeol))
                verse_data["cross_references"] = [dict(r) for r in cur.fetchall()]

                self.send_json(verse_data)

            # 4. 스트롱 코드 단독 사전 조회
            elif "/strong/" in path:
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
            elif "lookup-ref" in path:
                ref_param = query.get("ref", [""])[0].strip()
                version = query.get("version", ["rv"])[0]

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

                parts = re.split(r'[;,]', ref_param)
                verses_result = []
                last_book_id = None
                last_chapter = None

                for p in parts:
                    p = p.strip()
                    if not p:
                        continue
                    
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

            # 4.2 성경 인물/지명 사전 구절 연계 자동 감지 API
            elif "dictionary/verse" in path:
                unit_code = int(query.get("unit_code", [0])[0])
                jeol = int(query.get("jeol", [1])[0])

                cur.execute("SELECT phrase_rv, phrase_ko, phrase_nv FROM verses WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
                verse_row = cur.fetchone()
                
                matched = []
                if verse_row:
                    raw_rv = verse_row["phrase_rv"] or ""
                    raw_ko = verse_row["phrase_ko"] or ""
                    raw_nv = (verse_row["phrase_nv"] or "").lower()

                    # 1. 성경 원문 본문에 태깅된 고유명사 (<b>...</b>) 추출
                    b_names = set(re.findall(r'<b>([^<]+)</b>', raw_rv) + re.findall(r'<b>([^<]+)</b>', raw_ko))
                    
                    matched_map = {}
                    if b_names:
                        placeholders = ",".join("?" for _ in b_names)
                        cur.execute(f"SELECT * FROM bible_dictionary WHERE name_ko IN ({placeholders}) ORDER BY id ASC;", tuple(b_names))
                        for r in cur.fetchall():
                            matched_map[r["id"]] = dict(r)

                    # 2. 본문 텍스트 내 별칭/영문명 매칭 (예: 아브람 -> 아브라함, 게바 -> 베드로, 사울 -> 바울)
                    def clean_verse_text(text):
                        txt = re.sub(r'<cite>\d+</cite>', '', text)
                        txt = re.sub(r'<u[^>]*>[^<]*</u>', '', txt)
                        txt = re.sub(r'<[^>]+>', '', txt)
                        return txt.strip()

                    clean_txt = f"{clean_verse_text(raw_rv)} {clean_verse_text(raw_ko)}"
                    particles = r'(?:에서|으로|로써|으로써|부터|께서|에게|한테|이라|라고|이며|[이가은는을를과와의도만에로라며께])?'

                    def match_word(word, text):
                        if not word or len(word) < 1: return False
                        pattern = rf'(?:^|[\s"\'(\[\-])' + re.escape(word) + rf'{particles}(?=[\s.,?!;:\)\]\-]|$)'
                        return bool(re.search(pattern, text))

                    # 자주 매칭되는 별칭/주요 인물/도량형 및 성경 단어 보정
                    cur.execute("SELECT * FROM bible_dictionary WHERE category = '단어' OR aliases != '' ORDER BY id ASC;")
                    core_entries = [dict(r) for r in cur.fetchall()]

                    for entry in core_entries:
                        if entry["id"] in matched_map:
                            continue
                        name_ko = entry["name_ko"]
                        aliases = [a.strip() for a in (entry["aliases"] or "").split(",") if a.strip()]

                        base_names = [name_ko] + aliases
                        is_match = False
                        for n in base_names:
                            if len(n) >= 2 and match_word(n, clean_txt):
                                is_match = True
                                break
                            elif len(n) == 1 and n in ["금", "은", "놋", "철"]:
                                if match_word(n, clean_txt):
                                    is_match = True
                                    break

                        if is_match:
                            matched_map[entry["id"]] = entry

                    matched = list(matched_map.values())

                self.send_json({"unit_code": unit_code, "jeol": jeol, "count": len(matched), "entries": matched})

            # 4.3 성경 인명/지명/단어 사전 검색 및 목록 조회 API
            elif "dictionary/search" in path or "dictionary/all" in path:
                q = query.get("q", [""])[0].strip()
                cat = query.get("category", [""])[0].strip()
                limit = int(query.get("limit", [60])[0])

                sql = "SELECT * FROM bible_dictionary WHERE 1=1"
                params = []

                if cat and cat in ["인명", "인물", "지명", "단어"]:
                    cat_val = "인명" if cat == "인물" else cat
                    sql += " AND category = ?"
                    params.append(cat_val)

                if q:
                    sql += " AND (name_ko LIKE ? OR name_en LIKE ? OR aliases LIKE ? OR meaning LIKE ? OR summary LIKE ?)"
                    p = f"%{q}%"
                    params.extend([p, p, p, p, p])

                sql += " ORDER BY id ASC LIMIT ?;"
                params.append(limit)
                cur.execute(sql, tuple(params))
                items = [dict(r) for r in cur.fetchall()]
                self.send_json({"query": q, "category": cat, "count": len(items), "entries": items})

            # 4.4 성경 인물/지명 사전 단건 상세 조회 API
            elif "dictionary/entry" in path:
                entry_id = int(path.strip("/").split("/")[-1])
                cur.execute("SELECT * FROM bible_dictionary WHERE id = ?;", (entry_id,))
                row = cur.fetchone()
                if row:
                    self.send_json(dict(row))
                else:
                    self.send_json({"error": "Entry not found"}, status=404)

            # 5. 본문 검색
            elif "search" in path:
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
            elif "today" in path:
                day_of_year = datetime.now().timetuple().tm_yday
                cur.execute("SELECT count(*) as cnt FROM today_words;")
                tw_cnt = cur.fetchone()["cnt"] or 1
                cur.execute("SELECT count(*) as cnt FROM one_line_thanks;")
                th_cnt = cur.fetchone()["cnt"] or 1

                word_id = (day_of_year % tw_cnt) + 1
                cur.execute("SELECT * FROM today_words WHERE id = ?;", (word_id,))
                word_row = cur.fetchone()

                thanks_id = (day_of_year % th_cnt) + 1
                cur.execute("SELECT * FROM one_line_thanks WHERE id = ?;", (thanks_id,))
                thanks_row = cur.fetchone()

                self.send_json({
                    "today_word": dict(word_row) if word_row else None,
                    "one_line_thanks": dict(thanks_row)["content"] if thanks_row else "오늘도 주님의 은혜에 감사합니다."
                })

            # 7. 맥체인 통독 플랜
            elif "reading-plan" in path:
                day = int(query.get("day", [1])[0])
                cur.execute("SELECT * FROM mcheyne_plan WHERE day = ? ORDER BY id ASC;", (day,))
                plans = [dict(r) for r in cur.fetchall()]
                self.send_json({"day": day, "items": plans})

            # 8. 통독 통계
            elif "reading-stats" in path:
                cur.execute("SELECT count(DISTINCT unit_code) as read_chapters FROM user_reading_log;")
                read_chapters = cur.fetchone()["read_chapters"]
                cur.execute("SELECT count(*) as total_chapters FROM books;")
                total_chapters = 1189

                self.send_json({
                    "total_chapters": total_chapters,
                    "read_chapters": read_chapters,
                    "progress_percentage": round((read_chapters / total_chapters) * 100, 2)
                })

            else:
                self.send_json({"error": f"Endpoint not found: {path}"}, status=404)

        except Exception as e:
            self.send_json({"error": str(e)}, status=500)
        finally:
            conn.close()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        conn = get_db()
        cur = conn.cursor()

        try:
            if "highlight" in path:
                unit_code = int(data.get("unit_code", 0))
                jeol = int(data.get("jeol", 0))
                color = data.get("color", "")

                if not color or color == "none":
                    cur.execute("DELETE FROM user_highlights WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
                else:
                    cur.execute("""
                        INSERT INTO user_highlights (unit_code, jeol, color, created_at)
                        VALUES (?, ?, ?, datetime('now'))
                        ON CONFLICT(unit_code, jeol) DO UPDATE SET color = excluded.color;
                    """, (unit_code, jeol, color))
                conn.commit()
                self.send_json({"status": "ok", "unit_code": unit_code, "jeol": jeol, "color": color})

            elif "bookmark" in path:
                unit_code = int(data.get("unit_code", 0))
                jeol = int(data.get("jeol", 0))
                label = data.get("label", "")

                cur.execute("SELECT id FROM user_bookmarks WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
                existing = cur.fetchone()
                if existing:
                    cur.execute("DELETE FROM user_bookmarks WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
                    is_bookmarked = False
                else:
                    cur.execute("""
                        INSERT INTO user_bookmarks (unit_code, jeol, label, created_at)
                        VALUES (?, ?, ?, datetime('now'));
                    """, (unit_code, jeol, label))
                    is_bookmarked = True
                conn.commit()
                self.send_json({"status": "ok", "is_bookmarked": is_bookmarked})

            elif "note" in path:
                unit_code = int(data.get("unit_code", 0))
                jeol = int(data.get("jeol", 0))
                content = data.get("content", "").strip()

                if not content:
                    cur.execute("DELETE FROM user_notes WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
                else:
                    cur.execute("""
                        INSERT INTO user_notes (unit_code, jeol, content, updated_at)
                        VALUES (?, ?, ?, datetime('now'))
                        ON CONFLICT(unit_code, jeol) DO UPDATE SET content = excluded.content, updated_at = datetime('now');
                    """, (unit_code, jeol, content))
                conn.commit()
                self.send_json({"status": "ok", "unit_code": unit_code, "jeol": jeol})

            elif "reading-toggle" in path:
                unit_code = int(data.get("unit_code", 0))
                cur.execute("SELECT id FROM user_reading_log WHERE unit_code = ?;", (unit_code,))
                row = cur.fetchone()
                if row:
                    cur.execute("DELETE FROM user_reading_log WHERE unit_code = ?;", (unit_code,))
                    is_read = False
                else:
                    cur.execute("""
                        INSERT INTO user_reading_log (unit_code, read_count, last_read_at)
                        VALUES (?, 1, datetime('now'));
                    """, (unit_code,))
                    is_read = True
                conn.commit()
                self.send_json({"status": "ok", "unit_code": unit_code, "is_read": is_read})

            else:
                self.send_json({"error": f"POST endpoint not found: {path}"}, status=404)

        except Exception as e:
            self.send_json({"error": str(e)}, status=500)
        finally:
            conn.close()
