import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

phrase_cols = ['phrase_rv', 'phrase_ko', 'phrase_nw', 'phrase_ez', 'phrase_wr', 'phrase_nv', 'phrase_nt', 'phrase_es', 'phrase_nb', 'phrase_kj']

tags_per_col = {}
for col in phrase_cols:
    tags_ot = set()
    tags_nt = set()
    cur.execute(f"SELECT {col} FROM verses WHERE book_id <= 39;")
    for row in cur.fetchall():
        if row[0]:
            for tag in re.findall(r'<([^>]+)>', row[0]):
                tag_name = tag.split()[0].replace('/', '').lower()
                tags_ot.add(tag_name)
                
    cur.execute(f"SELECT {col} FROM verses WHERE book_id >= 40;")
    for row in cur.fetchall():
        if row[0]:
            for tag in re.findall(r'<([^>]+)>', row[0]):
                tag_name = tag.split()[0].replace('/', '').lower()
                tags_nt.add(tag_name)
                
    print(f"{col}:")
    print(f"  OT tags: {sorted(list(tags_ot))}")
    print(f"  NT tags: {sorted(list(tags_nt))}")
