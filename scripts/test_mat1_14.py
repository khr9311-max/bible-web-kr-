import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Test Mat 1:14 (unit_code 40001, jeol 14)
unit_code = 40001
jeol = 14

cur.execute("SELECT phrase_rv, phrase_ko, phrase_nv FROM verses WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
row = cur.fetchone()

raw_rv = row["phrase_rv"] or ""
raw_ko = row["phrase_ko"] or ""

# 1. Extract bold names directly tagged in Korean Bible text
b_names = set(re.findall(r'<b>([^<]+)</b>', raw_rv) + re.findall(r'<b>([^<]+)</b>', raw_ko))
print("Bold names in Mat 1:14:", b_names)

# 2. Query dictionary for these exact names
placeholders = ",".join("?" for _ in b_names)
cur.execute(f"SELECT * FROM bible_dictionary WHERE name_ko IN ({placeholders}) ORDER BY id ASC;", tuple(b_names))
matched = [dict(r) for r in cur.fetchall()]

print(f"Instantly found {len(matched)} matching entries for Mat 1:14:")
for m in matched:
    print(f"  - [{m['category']}] {m['name_ko']} ({m['name_en']}): {m['meaning']} / {m['summary']}")
