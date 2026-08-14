import sqlite3

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

cur.execute("SELECT unit_code, jeol, stitle_rv, stitle_ez, stitle_nv FROM verses WHERE stitle_rv LIKE '%lnk.spc%' LIMIT 5;")
for r in cur.fetchall():
    print("Unit:", r[0], "Jeol:", r[1])
    print("  RV:", r[2])
    print("  EZ:", r[3])
    print("  NV:", r[4])
    print()

conn.close()
