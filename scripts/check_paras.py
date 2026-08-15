import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

# Check Matthew 5 verses in all Korean versions and English versions
cur.execute("SELECT jeol, phrase_rv, phrase_wr, phrase_ez, phrase_nw, phrase_nv, phrase_es FROM verses WHERE unit_code=40005 AND jeol IN (1, 13, 17, 21, 27, 33, 38, 43);")
for row in cur.fetchall():
    jeol = row[0]
    rv = row[1][:30]
    wr = row[2][:30] if row[2] else ''
    ez = row[3][:30] if row[3] else ''
    nw = row[4][:30] if row[4] else ''
    nv = row[5][:30] if row[5] else ''
    print(f"v{jeol:2d} | RV: {rv:30s} | WR: {wr:30s} | NV: {nv:30s}")

# Check subtitle table if any
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("\nTables:", cur.fetchall())

# Check stitles table or column
cur.execute("PRAGMA table_info(stitles);")
print("stitles columns:", cur.fetchall())

cur.execute("SELECT * FROM stitles WHERE unit_code=40005;")
print("Mat 5 stitles:", cur.fetchall())

cur.execute("SELECT * FROM stitles WHERE unit_code=1001;")
print("Gen 1 stitles:", cur.fetchall())
