import sqlite3
import os

db_path = 'server/data/bible.db'
apk_db = 'extracted_tmp/res/30.sqlite'

print("=== Migrating all translation stitles into bible.db ===")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. verses 테이블에 각 역본별 stitle 컬럼 추가 (없으면)
stitle_cols = [
    'stitle_ko', 'stitle_nw', 'stitle_ez', 'stitle_wr',
    'stitle_nv', 'stitle_nt', 'stitle_es', 'stitle_nb', 'stitle_kj'
]

cur.execute("PRAGMA table_info(verses);")
existing_cols = [r[1] for r in cur.fetchall()]

for col in stitle_cols:
    if col not in existing_cols:
        print(f"Adding column {col} to verses table...")
        cur.execute(f"ALTER TABLE verses ADD COLUMN {col} TEXT;")

conn.commit()

# 2. 30.sqlite에서 stitle 데이터 채우기
src_conn = sqlite3.connect(apk_db)
src_cur = src_conn.cursor()

src_cur.execute("""
    SELECT unit_code, unit_jeol, 
           stitle_rv, stitle_ko, stitle_nw, stitle_ez, stitle_wr,
           stitle_nv, stitle_nt, stitle_es, stitle_nb, stitle_kj
    FROM bible7_phrase;
""")

rows = src_cur.fetchall()
print(f"Fetched {len(rows)} rows from APK DB. Updating bible.db...")

cur.executemany("""
    UPDATE verses SET
        stitle_rv = ?,
        stitle_ko = ?,
        stitle_nw = ?,
        stitle_ez = ?,
        stitle_wr = ?,
        stitle_nv = ?,
        stitle_nt = ?,
        stitle_es = ?,
        stitle_nb = ?,
        stitle_kj = ?
    WHERE unit_code = ? AND jeol = ?;
""", [(r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[0], r[1]) for r in rows])

conn.commit()
src_conn.close()

# 검증: 창세기 1장 1절 소제목들 확인
cur.execute("""
    SELECT jeol, stitle_rv, stitle_ez, stitle_wr, stitle_nv, stitle_es 
    FROM verses WHERE unit_code=1001 AND jeol=1;
""")
print("Genesis 1:1 stitles:", cur.fetchone())

conn.close()
print("=== All translation stitles migration completed successfully! ===")
