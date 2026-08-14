import sqlite3
import json

conn = sqlite3.connect('extracted_tmp/res/30.sqlite')
cur = conn.cursor()

print("--- Check is_exist_thelord in bible7_phrase ---")
cur.execute('SELECT unit_code, unit_jeol, is_exist_thelord, phrase_rv, phrase_nv FROM bible7_phrase WHERE is_exist_thelord = 1 LIMIT 5;')
for r in cur.fetchall():
    print(r[0], r[1], r[2], r[3][:60])

print("\n--- Check HTML tags in verses with thelord ---")
cur.execute('SELECT phrase_rv FROM bible7_phrase WHERE is_exist_thelord = 1 AND unit_code >= 40001 LIMIT 5;')
for r in cur.fetchall():
    print(r[0])

conn.close()
