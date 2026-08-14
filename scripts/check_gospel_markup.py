import sqlite3

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

print("--- Matthew 5:1-12 phrase_rv in DB ---")
cur.execute('SELECT jeol, phrase_rv FROM verses WHERE unit_code=40005 AND jeol BETWEEN 1 AND 12;')
for r in cur.fetchall():
    print(f"[{r[0]}절]: {r[1]}")

print("\n--- John 3:16 phrase_rv in DB ---")
cur.execute('SELECT jeol, phrase_rv FROM verses WHERE unit_code=43003 AND jeol BETWEEN 14 AND 18;')
for r in cur.fetchall():
    print(f"[{r[0]}절]: {r[1]}")

conn.close()
