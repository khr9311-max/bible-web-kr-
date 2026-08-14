import sqlite3

conn = sqlite3.connect('extracted_tmp/res/30.sqlite')
cur = conn.cursor()

print("--- Check tables in 30.sqlite ---")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]
print(tables)

print("\n--- Check columns in bible7_phrase ---")
cur.execute("PRAGMA table_info(bible7_phrase);")
for r in cur.fetchall():
    print(r[1])

print("\n--- Check stitle columns or tables in 30.sqlite ---")
for t in tables:
    if 'stitle' in t or 'title' in t or 'sub' in t:
        print("Found table:", t)
        cur.execute(f"PRAGMA table_info({t});")
        print([r[1] for r in cur.fetchall()])

conn.close()
