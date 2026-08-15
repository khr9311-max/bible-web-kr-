import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('server/data/bible.db')
cursor = conn.cursor()

cursor.execute("SELECT book_id, chapter, jeol, phrase_rv FROM verses WHERE phrase_rv LIKE '%<q>%' AND book_id <= 39 LIMIT 10;")
for r in cursor.fetchall():
    print(f"Book {r[0]} {r[1]}:{r[2]} -> {r[3]}")
