import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()
cur.execute("SELECT id, name_ko, name_en, meaning FROM bible_dictionary WHERE meaning != '' AND meaning IS NOT NULL;")
rows = cur.fetchall()
print(f"Total entries with meaning: {len(rows)}")

has_english = []
for r in rows:
    if re.search(r'[a-zA-Z]', r[3]):
        has_english.append(r)

print(f"Entries with English words in meaning: {len(has_english)}")
print("Sample 30 entries with English in meaning:")
for r in has_english[:30]:
    print(f"  - ID {r[0]}: {r[1]} ({r[2]}) -> {r[3]}")
