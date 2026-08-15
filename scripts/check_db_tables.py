import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print('Tables in bible.db:', tables)

cur.execute("SELECT count(*) FROM strong_phrases;")
print('strong_phrases count:', cur.fetchone()[0])

cur.execute("SELECT * FROM strong_phrases LIMIT 3;")
print('strong_phrases samples:', cur.fetchall())
