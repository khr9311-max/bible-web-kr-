import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

# Check count of ○ in RV, KO, NW, etc.
cur.execute("SELECT count(*) FROM verses WHERE phrase_rv LIKE '%○%';")
print('RV with ○ count:', cur.fetchone()[0])

cur.execute("SELECT count(*) FROM verses WHERE phrase_rv LIKE '%<h2>%';")
print('RV with <h2> count:', cur.fetchone()[0])

cur.execute("SELECT count(*) FROM verses WHERE phrase_ko LIKE '%○%';")
print('KO with ○ count:', cur.fetchone()[0])

# Check Genesis 1 verses in RV
print("\n--- Genesis 1 (unit 1001) RV ---")
cur.execute("SELECT jeol, phrase_rv FROM verses WHERE unit_code=1001 ORDER BY jeol;")
for jeol, phrase in cur.fetchall():
    has_circle = '○' in phrase or '●' in phrase
    has_h2 = '<h2>' in phrase
    if has_circle or has_h2 or jeol in [1, 3, 6, 9, 14, 20, 24]:
        print(f"v{jeol}: circle={has_circle}, h2={has_h2} | {phrase[:50]}")

# Check Matthew 5 verses in RV
print("\n--- Matthew 5 (unit 40005) RV ---")
cur.execute("SELECT jeol, phrase_rv FROM verses WHERE unit_code=40005 ORDER BY jeol;")
for jeol, phrase in cur.fetchall():
    has_circle = '○' in phrase or '●' in phrase
    has_h2 = '<h2>' in phrase
    if has_circle or has_h2:
        print(f"v{jeol}: circle={has_circle}, h2={has_h2} | {phrase[:50]}")

