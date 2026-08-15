import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

print("--- Check phrase_rv with <q> ---")
cur.execute("SELECT book_id, chapter, jeol, phrase_rv FROM verses WHERE phrase_rv LIKE '%<q>%' LIMIT 5;")
for r in cur.fetchall():
    print(f"Book {r[0]} {r[1]}:{r[2]} -> {r[3]}")

print("\n--- Check phrase_nv (NIV) with <q> ---")
cur.execute("SELECT book_id, chapter, jeol, phrase_nv FROM verses WHERE phrase_nv LIKE '%<q>%' LIMIT 5;")
for r in cur.fetchall():
    print(f"Book {r[0]} {r[1]}:{r[2]} -> {r[3]}")

print("\n--- Check phrase_rv with <i> ---")
cur.execute("SELECT book_id, chapter, jeol, phrase_rv FROM verses WHERE phrase_rv LIKE '%<i>%' LIMIT 5;")
for r in cur.fetchall():
    print(f"Book {r[0]} {r[1]}:{r[2]} -> {r[3]}")
