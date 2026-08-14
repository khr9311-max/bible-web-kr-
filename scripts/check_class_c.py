import sqlite3
import zipfile

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()
cur.execute("SELECT unit_code, jeol, phrase_rv FROM verses WHERE phrase_rv LIKE '%class=c%' LIMIT 10;")
for r in cur.fetchall():
    print(r[0], r[1], r[2])
conn.close()

print("\n--- Check CSS definitions in APK ---")
with zipfile.ZipFile('갓피플성경_26.06_APKPure.apk', 'r') as z:
    css = z.read('assets/css/bible_min.css').decode('utf-8', errors='ignore')
    for line in css.split('\n'):
        if any(k in line for k in ['u.c', 'u.l', 'u.n', 'u {', 'u,', '.c', 'class=c']):
            print(line)
