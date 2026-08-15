import sqlite3
import gzip
import shutil

conn = sqlite3.connect('server/data/bible.db')
c = conn.cursor()
c.execute("UPDATE bible_dictionary SET aliases = '위로의 아들, 요셉(바나바)' WHERE id = 113;")
c.execute("UPDATE bible_dictionary SET aliases = '갈릴리 나사렛' WHERE id = 125;")
conn.commit()
conn.close()

with open('server/data/bible.db', 'rb') as f_in:
    with gzip.open('server/data/bible.db.gz', 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)
print("Updated aliases and compressed DB!")
