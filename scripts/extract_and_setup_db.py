import zipfile
import sqlite3
import os
import json
import re

APK_PATH = "갓피플성경_26.06_APKPure.apk"
OUTPUT_DB = "server/data/bible.db"
EXTRACT_DIR = "extracted_tmp"

# 성경 66권 정밀 메타데이터 (순서, 한글명, 한글약어, 영문명, 영문약어, 구약/신약, 카테고리)
BIBLE_BOOKS = [
    # 구약 (Old Testament - 39권)
    {"id": 1, "name": "창세기", "abbr": "창", "eng_name": "Genesis", "eng_abbr": "Gen", "testament": "OT", "category": "율법서", "chapters": 50},
    {"id": 2, "name": "출애굽기", "abbr": "출", "eng_name": "Exodus", "eng_abbr": "Exo", "testament": "OT", "category": "율법서", "chapters": 40},
    {"id": 3, "name": "레위기", "abbr": "레", "eng_name": "Leviticus", "eng_abbr": "Lev", "testament": "OT", "category": "율법서", "chapters": 27},
    {"id": 4, "name": "민수기", "abbr": "민", "eng_name": "Numbers", "eng_abbr": "Num", "testament": "OT", "category": "율법서", "chapters": 36},
    {"id": 5, "name": "신명기", "abbr": "신", "eng_name": "Deuteronomy", "eng_abbr": "Deu", "testament": "OT", "category": "율법서", "chapters": 34},
    {"id": 6, "name": "여호수아", "abbr": "수", "eng_name": "Joshua", "eng_abbr": "Jos", "testament": "OT", "category": "역사서", "chapters": 24},
    {"id": 7, "name": "사사기", "abbr": "삿", "eng_name": "Judges", "eng_abbr": "Jdg", "testament": "OT", "category": "역사서", "chapters": 21},
    {"id": 8, "name": "룻기", "abbr": "룻", "eng_name": "Ruth", "eng_abbr": "Rut", "testament": "OT", "category": "역사서", "chapters": 4},
    {"id": 9, "name": "사무엘상", "abbr": "삼상", "eng_name": "1 Samuel", "eng_abbr": "1Sa", "testament": "OT", "category": "역사서", "chapters": 31},
    {"id": 10, "name": "사무엘하", "abbr": "삼하", "eng_name": "2 Samuel", "eng_abbr": "2Sa", "testament": "OT", "category": "역사서", "chapters": 24},
    {"id": 11, "name": "열왕기상", "abbr": "왕상", "eng_name": "1 Kings", "eng_abbr": "1Ki", "testament": "OT", "category": "역사서", "chapters": 22},
    {"id": 12, "name": "열왕기하", "abbr": "왕하", "eng_name": "2 Kings", "eng_abbr": "2Ki", "testament": "OT", "category": "역사서", "chapters": 25},
    {"id": 13, "name": "역대상", "abbr": "대상", "eng_name": "1 Chronicles", "eng_abbr": "1Ch", "testament": "OT", "category": "역사서", "chapters": 29},
    {"id": 14, "name": "역대하", "abbr": "대하", "eng_name": "2 Chronicles", "eng_abbr": "2Ch", "testament": "OT", "category": "역사서", "chapters": 36},
    {"id": 15, "name": "에스라", "abbr": "스", "eng_name": "Ezra", "eng_abbr": "Ezr", "testament": "OT", "category": "역사서", "chapters": 10},
    {"id": 16, "name": "느헤미야", "abbr": "느", "eng_name": "Nehemiah", "eng_abbr": "Neh", "testament": "OT", "category": "역사서", "chapters": 13},
    {"id": 17, "name": "에스더", "abbr": "에", "eng_name": "Esther", "eng_abbr": "Est", "testament": "OT", "category": "역사서", "chapters": 10},
    {"id": 18, "name": "욥기", "abbr": "욥", "eng_name": "Job", "eng_abbr": "Job", "testament": "OT", "category": "시가서", "chapters": 42},
    {"id": 19, "name": "시편", "abbr": "시", "eng_name": "Psalms", "eng_abbr": "Psa", "testament": "OT", "category": "시가서", "chapters": 150},
    {"id": 20, "name": "잠언", "abbr": "잠", "eng_name": "Proverbs", "eng_abbr": "Pro", "testament": "OT", "category": "시가서", "chapters": 31},
    {"id": 21, "name": "전도서", "abbr": "전", "eng_name": "Ecclesiastes", "eng_abbr": "Ecc", "testament": "OT", "category": "시가서", "chapters": 12},
    {"id": 22, "name": "아가", "abbr": "아", "eng_name": "Song of Songs", "eng_abbr": "Sng", "testament": "OT", "category": "시가서", "chapters": 8},
    {"id": 23, "name": "이사야", "abbr": "사", "eng_name": "Isaiah", "eng_abbr": "Isa", "testament": "OT", "category": "대선지서", "chapters": 66},
    {"id": 24, "name": "예레미야", "abbr": "렘", "eng_name": "Jeremiah", "eng_abbr": "Jer", "testament": "OT", "category": "대선지서", "chapters": 52},
    {"id": 25, "name": "예레미야애가", "abbr": "애", "eng_name": "Lamentations", "eng_abbr": "Lam", "testament": "OT", "category": "대선지서", "chapters": 5},
    {"id": 26, "name": "에스겔", "abbr": "겔", "eng_name": "Ezekiel", "eng_abbr": "Ezk", "testament": "OT", "category": "대선지서", "chapters": 48},
    {"id": 27, "name": "다니엘", "abbr": "단", "eng_name": "Daniel", "eng_abbr": "Dan", "testament": "OT", "category": "대선지서", "chapters": 12},
    {"id": 28, "name": "호세아", "abbr": "호", "eng_name": "Hosea", "eng_abbr": "Hos", "testament": "OT", "category": "소선지서", "chapters": 14},
    {"id": 29, "name": "요엘", "abbr": "욜", "eng_name": "Joel", "eng_abbr": "Jol", "testament": "OT", "category": "소선지서", "chapters": 3},
    {"id": 30, "name": "아모스", "abbr": "암", "eng_name": "Amos", "eng_abbr": "Amo", "testament": "OT", "category": "소선지서", "chapters": 9},
    {"id": 31, "name": "오바댜", "abbr": "옵", "eng_name": "Obadiah", "eng_abbr": "Oba", "testament": "OT", "category": "소선지서", "chapters": 1},
    {"id": 32, "name": "요나", "abbr": "욘", "eng_name": "Jonah", "eng_abbr": "Jon", "testament": "OT", "category": "소선지서", "chapters": 4},
    {"id": 33, "name": "미가", "abbr": "미", "eng_name": "Micah", "eng_abbr": "Mic", "testament": "OT", "category": "소선지서", "chapters": 7},
    {"id": 34, "name": "나훔", "abbr": "나", "eng_name": "Nahum", "eng_abbr": "Nah", "testament": "OT", "category": "소선지서", "chapters": 3},
    {"id": 35, "name": "하박국", "abbr": "합", "eng_name": "Habakkuk", "eng_abbr": "Hab", "testament": "OT", "category": "소선지서", "chapters": 3},
    {"id": 36, "name": "스바냐", "abbr": "습", "eng_name": "Zephaniah", "eng_abbr": "Zep", "testament": "OT", "category": "소선지서", "chapters": 3},
    {"id": 37, "name": "학개", "abbr": "학", "eng_name": "Haggai", "eng_abbr": "Hag", "testament": "OT", "category": "소선지서", "chapters": 2},
    {"id": 38, "name": "스가랴", "abbr": "슥", "eng_name": "Zechariah", "eng_abbr": "Zec", "testament": "OT", "category": "소선지서", "chapters": 14},
    {"id": 39, "name": "말라기", "abbr": "말", "eng_name": "Malachi", "eng_abbr": "Mal", "testament": "OT", "category": "소선지서", "chapters": 4},

    # 신약 (New Testament - 27권)
    {"id": 40, "name": "마태복음", "abbr": "마", "eng_name": "Matthew", "eng_abbr": "Mat", "testament": "NT", "category": "복음서", "chapters": 28},
    {"id": 41, "name": "마가복음", "abbr": "막", "eng_name": "Mark", "eng_abbr": "Mrk", "testament": "NT", "category": "복음서", "chapters": 16},
    {"id": 42, "name": "누가복음", "abbr": "눅", "eng_name": "Luke", "eng_abbr": "Luk", "testament": "NT", "category": "복음서", "chapters": 24},
    {"id": 43, "name": "요한복음", "abbr": "요", "eng_name": "John", "eng_abbr": "Jhn", "testament": "NT", "category": "복음서", "chapters": 21},
    {"id": 44, "name": "사도행전", "abbr": "행", "eng_name": "Acts", "eng_abbr": "Act", "testament": "NT", "category": "역사서", "chapters": 28},
    {"id": 45, "name": "로마서", "abbr": "롬", "eng_name": "Romans", "eng_abbr": "Rom", "testament": "NT", "category": "바울서신", "chapters": 16},
    {"id": 46, "name": "고린도전서", "abbr": "고전", "eng_name": "1 Corinthians", "eng_abbr": "1Co", "testament": "NT", "category": "바울서신", "chapters": 16},
    {"id": 47, "name": "고린도후서", "abbr": "고후", "eng_name": "2 Corinthians", "eng_abbr": "2Co", "testament": "NT", "category": "바울서신", "chapters": 13},
    {"id": 48, "name": "갈라디아서", "abbr": "갈", "eng_name": "Galatians", "eng_abbr": "Gal", "testament": "NT", "category": "바울서신", "chapters": 6},
    {"id": 49, "name": "에베소서", "abbr": "엡", "eng_name": "Ephesians", "eng_abbr": "Eph", "testament": "NT", "category": "바울서신", "chapters": 6},
    {"id": 50, "name": "빌립보서", "abbr": "빌", "eng_name": "Philippians", "eng_abbr": "Php", "testament": "NT", "category": "바울서신", "chapters": 4},
    {"id": 51, "name": "골로새서", "abbr": "골", "eng_name": "Colossians", "eng_abbr": "Col", "testament": "NT", "category": "바울서신", "chapters": 4},
    {"id": 52, "name": "데살로니가전서", "abbr": "살전", "eng_name": "1 Thessalonians", "eng_abbr": "1Th", "testament": "NT", "category": "바울서신", "chapters": 5},
    {"id": 53, "name": "데살로니가후서", "abbr": "살후", "eng_name": "2 Thessalonians", "eng_abbr": "2Th", "testament": "NT", "category": "바울서신", "chapters": 3},
    {"id": 54, "name": "디모데전서", "abbr": "딤전", "eng_name": "1 Timothy", "eng_abbr": "1Ti", "testament": "NT", "category": "바울서신", "chapters": 6},
    {"id": 55, "name": "디모데후서", "abbr": "딤후", "eng_name": "2 Timothy", "eng_abbr": "2Ti", "testament": "NT", "category": "바울서신", "chapters": 4},
    {"id": 56, "name": "디도서", "abbr": "딛", "eng_name": "Titus", "eng_abbr": "Tit", "testament": "NT", "category": "바울서신", "chapters": 3},
    {"id": 57, "name": "빌레몬서", "abbr": "몬", "eng_name": "Philemon", "eng_abbr": "Phm", "testament": "NT", "category": "바울서신", "chapters": 1},
    {"id": 58, "name": "히브리서", "abbr": "히", "eng_name": "Hebrews", "eng_abbr": "Heb", "testament": "NT", "category": "일반서신", "chapters": 13},
    {"id": 59, "name": "야고보서", "abbr": "약", "eng_name": "James", "eng_abbr": "Jas", "testament": "NT", "category": "일반서신", "chapters": 5},
    {"id": 60, "name": "베드로전서", "abbr": "벧전", "eng_name": "1 Peter", "eng_abbr": "1Pe", "testament": "NT", "category": "일반서신", "chapters": 5},
    {"id": 61, "name": "베드로후서", "abbr": "벧후", "eng_name": "2 Peter", "eng_abbr": "2Pe", "testament": "NT", "category": "일반서신", "chapters": 3},
    {"id": 62, "name": "요한일서", "abbr": "요일", "eng_name": "1 John", "eng_abbr": "1Jn", "testament": "NT", "category": "일반서신", "chapters": 5},
    {"id": 63, "name": "요한이서", "abbr": "요이", "eng_name": "2 John", "eng_abbr": "2Jn", "testament": "NT", "category": "일반서신", "chapters": 1},
    {"id": 64, "name": "요한삼서", "abbr": "요삼", "eng_name": "3 John", "eng_abbr": "3Jn", "testament": "NT", "category": "일반서신", "chapters": 1},
    {"id": 65, "name": "유다서", "abbr": "유", "eng_name": "Jude", "eng_abbr": "Jud", "testament": "NT", "category": "일반서신", "chapters": 1},
    {"id": 66, "name": "요한계시록", "abbr": "계", "eng_name": "Revelation", "eng_abbr": "Rev", "testament": "NT", "category": "예언서", "chapters": 22}
]

def extract_assets():
    print("[1/5] Extracting APK assets and SQLite DB...")
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    os.makedirs("public/icons", exist_ok=True)
    
    with zipfile.ZipFile(APK_PATH, 'r') as z:
        for name in z.namelist():
            if name == 'res/30.sqlite' or name.endswith('.sqlite'):
                z.extract(name, EXTRACT_DIR)
            elif name.startswith('assets/web_icons/') or name.startswith('assets/img/'):
                dest_filename = os.path.basename(name)
                if dest_filename:
                    with open(os.path.join("public/icons", dest_filename), "wb") as f:
                        f.write(z.read(name))

def clean_html(raw_html):
    if not raw_html:
        return ""
    # <p><cite>1</cite>... </p> 제거 또는 깔끔한 텍스트로 보존
    text = re.sub(r'<cite>\d+</cite>', '', raw_html)
    text = text.replace('<p>', '').replace('</p>', '')
    return text.strip()

def setup_database():
    print("[2/5] Creating optimized web database schema...")
    os.makedirs("server/data", exist_ok=True)
    
    if os.path.exists(OUTPUT_DB):
        os.remove(OUTPUT_DB)
        
    out_conn = sqlite3.connect(OUTPUT_DB)
    out_cur = out_conn.cursor()
    
    # 1. 책 목록 테이블
    out_cur.execute("""
    CREATE TABLE books (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        abbr TEXT NOT NULL,
        eng_name TEXT NOT NULL,
        eng_abbr TEXT NOT NULL,
        testament TEXT NOT NULL,
        category TEXT NOT NULL,
        chapters INTEGER NOT NULL
    );
    """)
    
    for b in BIBLE_BOOKS:
        out_cur.execute("""
        INSERT INTO books (id, name, abbr, eng_name, eng_abbr, testament, category, chapters)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (b["id"], b["name"], b["abbr"], b["eng_name"], b["eng_abbr"], b["testament"], b["category"], b["chapters"]))
        
    # 2. 장/절별 성경 본문 테이블
    out_cur.execute("""
    CREATE TABLE verses (
        unit_code INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        chapter INTEGER NOT NULL,
        jeol INTEGER NOT NULL,
        stitle_rv TEXT,
        phrase_rv TEXT,
        phrase_ko TEXT,
        phrase_nw TEXT,
        phrase_ez TEXT,
        phrase_wr TEXT,
        phrase_nv TEXT,
        phrase_nt TEXT,
        phrase_es TEXT,
        phrase_nb TEXT,
        phrase_kj TEXT,
        search_text TEXT,
        PRIMARY KEY (unit_code, jeol)
    );
    """)
    
    # 3. 스트롱 코드 원어 분해 테이블
    out_cur.execute("""
    CREATE TABLE strong_phrases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_code INTEGER NOT NULL,
        jeol INTEGER NOT NULL,
        phrase_order INTEGER NOT NULL,
        strong_code TEXT,
        phrase TEXT NOT NULL,
        bracket INTEGER DEFAULT 0,
        space INTEGER DEFAULT 1
    );
    """)
    
    # 4. 관주 및 각주 테이블
    out_cur.execute("""
    CREATE TABLE cross_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version TEXT NOT NULL,
        unit_code INTEGER NOT NULL,
        jeol INTEGER NOT NULL,
        kind TEXT,
        mark TEXT,
        explains TEXT,
        link_ids TEXT
    );
    """)
    
    # 5. 오늘의 말씀 및 한 줄 감사 테이블
    out_cur.execute("""
    CREATE TABLE today_words (
        id INTEGER PRIMARY KEY,
        unit_code INTEGER NOT NULL,
        jeol_start INTEGER NOT NULL,
        jeol_end INTEGER NOT NULL
    );
    """)
    out_cur.execute("""
    CREATE TABLE one_line_thanks (
        id INTEGER PRIMARY KEY,
        text TEXT NOT NULL
    );
    """)

    # 6. 사용자 데이터 테이블 (북마크, 형광펜, 메모, 통독 로그)
    out_cur.execute("""
    CREATE TABLE user_highlights (
        id TEXT PRIMARY KEY,
        unit_code INTEGER NOT NULL,
        jeol INTEGER NOT NULL,
        color TEXT NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    out_cur.execute("""
    CREATE TABLE user_bookmarks (
        id TEXT PRIMARY KEY,
        unit_code INTEGER NOT NULL,
        jeol INTEGER NOT NULL,
        label TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    out_cur.execute("""
    CREATE TABLE user_notes (
        id TEXT PRIMARY KEY,
        unit_code INTEGER NOT NULL,
        jeol INTEGER NOT NULL,
        content TEXT NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    out_cur.execute("""
    CREATE TABLE user_reading_log (
        unit_code INTEGER PRIMARY KEY,
        read_count INTEGER DEFAULT 1,
        last_read_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    out_cur.execute("""
    CREATE TABLE reading_plans (
        day INTEGER PRIMARY KEY,
        ot_1 TEXT NOT NULL,
        ot_2 TEXT,
        nt_1 TEXT NOT NULL,
        psalm TEXT
    );
    """)
    
    out_conn.commit()

    print("[3/5] Migrating and indexing Bible phrases...")
    src_db = os.path.join(EXTRACT_DIR, "res/30.sqlite")
    src_conn = sqlite3.connect(src_db)
    src_cur = src_conn.cursor()
    
    # 성경 구절 복사
    src_cur.execute("""
    SELECT unit_code, unit_jeol, stitle_rv, phrase_rv, phrase_ko, phrase_nw, phrase_ez, phrase_wr, 
           phrase_nv, phrase_nt, phrase_es, phrase_nb, phrase_kj, plain_txt
    FROM bible7_phrase ORDER BY unit_code, unit_jeol;
    """)
    
    rows = src_cur.fetchall()
    insert_verses = []
    for r in rows:
        unit_code = r[0]
        jeol = r[1]
        book_id = unit_code // 1000
        chapter = unit_code % 1000
        stitle_rv = clean_html(r[2]) if r[2] else ""
        phrase_rv = r[3] or ""
        phrase_ko = r[4] or ""
        phrase_nw = r[5] or ""
        phrase_ez = r[6] or ""
        phrase_wr = r[7] or ""
        phrase_nv = r[8] or ""
        phrase_nt = r[9] or ""
        phrase_es = r[10] or ""
        phrase_nb = r[11] or ""
        phrase_kj = r[12] or ""
        plain_txt = r[13] or ""
        
        insert_verses.append((
            unit_code, book_id, chapter, jeol, stitle_rv,
            phrase_rv, phrase_ko, phrase_nw, phrase_ez, phrase_wr,
            phrase_nv, phrase_nt, phrase_es, phrase_nb, phrase_kj,
            plain_txt
        ))
        
    out_cur.executemany("""
    INSERT INTO verses (unit_code, book_id, chapter, jeol, stitle_rv,
                        phrase_rv, phrase_ko, phrase_nw, phrase_ez, phrase_wr,
                        phrase_nv, phrase_nt, phrase_es, phrase_nb, phrase_kj,
                        search_text)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, insert_verses)
    out_conn.commit()
    print(f"  -> Migrated {len(insert_verses)} verses.")

    print("[4/5] Migrating Strong codes, cross-references & daily words...")
    # 스트롱 코드 복사
    src_cur.execute("""
    SELECT unit_code, unit_jeol, phrase_order, strong_code, phrase, bracket, space 
    FROM bible_code_phrase ORDER BY unit_code, unit_jeol, phrase_order;
    """)
    strong_rows = src_cur.fetchall()
    out_cur.executemany("""
    INSERT INTO strong_phrases (unit_code, jeol, phrase_order, strong_code, phrase, bracket, space)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, strong_rows)
    out_conn.commit()
    print(f"  -> Migrated {len(strong_rows)} strong code phrases.")

    # 관주 복사 (개역개정 rv, NIV nv, 쉬운성경 ez 등)
    for ver in ['rv', 'nv', 'ez', 'nw', 'wr']:
        tbl = f"bible_link_{ver}"
        try:
            src_cur.execute(f"SELECT '{ver}', unit_code, unit_jeol, kind, mark, explains, link_ids FROM {tbl};")
            links = src_cur.fetchall()
            out_cur.executemany("""
            INSERT INTO cross_references (version, unit_code, jeol, kind, mark, explains, link_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, links)
        except Exception as e:
            print(f"  Warning on table {tbl}: {e}")
    out_conn.commit()

    # 오늘의 말씀 & 감사
    src_cur.execute("SELECT tw_no, tw_code, tw_jeol_s, tw_jeol_e FROM today_words;")
    out_cur.executemany("INSERT INTO today_words (id, unit_code, jeol_start, jeol_end) VALUES (?, ?, ?, ?);", src_cur.fetchall())
    
    src_cur.execute("SELECT ot_no, ot_txt FROM one_line_thanks;")
    out_cur.executemany("INSERT INTO one_line_thanks (id, text) VALUES (?, ?);", src_cur.fetchall())
    out_conn.commit()

    # 맥체인 성경 읽기표 365일 기본 생성
    print("[5/5] Generating M'Cheyne 365-day reading plan and creating performance indexes...")
    # 맥체인 기본 데이터 채우기 (샘플 및 순환 매핑)
    # 구약1(창1~), 구약2(스1~), 신약1(마1~), 시편(시1~)
    mcheyne_days = []
    for day in range(1, 366):
        # 365일 플랜
        ot1_book = 1 if day <= 50 else (2 if day <= 90 else (day % 39 + 1))
        ot1_ch = (day % 50) + 1
        nt1_book = 40 + (day % 27)
        nt1_ch = (day % 28) + 1
        ps_ch = (day % 150) + 1
        mcheyne_days.append((day, f"{ot1_book*1000 + ot1_ch}", f"{(ot1_book+1)*1000 + 1}", f"{nt1_book*1000 + nt1_ch}", f"19{ps_ch:03d}"))
        
    out_cur.executemany("INSERT INTO reading_plans (day, ot_1, ot_2, nt_1, psalm) VALUES (?, ?, ?, ?, ?);", mcheyne_days)

    # 인덱스 생성
    out_cur.execute("CREATE INDEX idx_verses_unit_code ON verses (unit_code);")
    out_cur.execute("CREATE INDEX idx_verses_book_ch ON verses (book_id, chapter);")
    out_cur.execute("CREATE INDEX idx_verses_search ON verses (search_text);")
    out_cur.execute("CREATE INDEX idx_strong_unit ON strong_phrases (unit_code, jeol);")
    out_cur.execute("CREATE INDEX idx_strong_code ON strong_phrases (strong_code);")
    out_cur.execute("CREATE INDEX idx_crossref_unit ON cross_references (unit_code, jeol);")
    out_cur.execute("CREATE INDEX idx_highlights_unit ON user_highlights (unit_code);")
    out_cur.execute("CREATE INDEX idx_bookmarks_unit ON user_bookmarks (unit_code);")
    out_cur.execute("CREATE INDEX idx_notes_unit ON user_notes (unit_code);")
    
    out_conn.commit()
    src_conn.close()
    out_conn.close()
    print("Database extraction, migration, and optimization COMPLETED successfully!")

if __name__ == "__main__":
    extract_assets()
    setup_database()
