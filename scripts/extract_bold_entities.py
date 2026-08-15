import sqlite3
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

cur.execute("SELECT phrase_rv FROM verses WHERE phrase_rv LIKE '%<b>%';")
rows = cur.fetchall()
print(f"Total verses with <b> tags: {len(rows)}")

all_b_names = []
for r in rows:
    matches = re.findall(r'<b>([^<]+)</b>', r[0])
    for m in matches:
        clean = m.strip()
        if clean and len(clean) <= 15:
            all_b_names.append(clean)

counts = Counter(all_b_names)
print(f"Total unique <b> terms: {len(counts)}")
print("Sample top 30 bold names/terms in Bible text:")
for name, cnt in counts.most_common(30):
    print(f"  {name}: {cnt} times")
