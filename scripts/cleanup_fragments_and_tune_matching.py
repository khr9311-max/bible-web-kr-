import sqlite3
import gzip
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

# 1. Clean up fragmented phrases in dictionary
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

delete_names = [
    '나사렛 예수 유대',
    '나사렛 예수 그리스도',
    '그리스도 예수',
    '호산나 다윗'
]

for name in delete_names:
    cur.execute("DELETE FROM bible_dictionary WHERE name_ko = ?", (name,))
    print(f"🗑️ 파편화 표제어 정리: {name}")

conn.commit()
conn.close()

# 2. Re-compress bible.db.gz
print("📦 bible.db.gz 압축 중...")
with open(DB_PATH, 'rb') as f_in:
    with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)
        
print("🎉 완료!")
