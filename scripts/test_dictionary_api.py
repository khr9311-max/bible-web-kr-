import sqlite3
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Test 1: Search '아브라함'
cur.execute("SELECT * FROM bible_dictionary WHERE name_ko LIKE '%아브라함%' OR aliases LIKE '%아브라함%';")
rows = [dict(r) for r in cur.fetchall()]
print(f"[Test 1] Search '아브라함' found {len(rows)} entries:")
for r in rows:
    print(f"  - [{r['category']}] {r['name_ko']} ({r['name_en']}) / {r['name_original']}: {r['meaning']}")

# Test 2: Genesis 12:1 verse entity detection (창 12:1 unit_code = 1012, jeol = 1)
unit_code = 1012
jeol = 1
cur.execute("SELECT phrase_rv, phrase_ko, phrase_nv FROM verses WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
v = cur.fetchone()
print(f"\n[Test 2] Genesis 12:1 Text: {v['phrase_rv']}")

comb = f"{v['phrase_rv'] or ''} {v['phrase_ko'] or ''}"
cur.execute("SELECT * FROM bible_dictionary;")
all_entries = [dict(r) for r in cur.fetchall()]

detected = []
for entry in all_entries:
    name_ko = entry["name_ko"]
    aliases = [a.strip() for a in (entry["aliases"] or "").split(",") if a.strip()]
    if name_ko in comb:
        detected.append(entry)
    else:
        for a in aliases:
            if len(a) >= 2 and a in comb:
                detected.append(entry)
                break

print(f"Detected in Gen 12:1: {[d['name_ko'] for d in detected]}")

# Test 3: Matthew 2:1 verse entity detection (마 2:1 unit_code = 40002, jeol = 1)
unit_code = 40002
jeol = 1
cur.execute("SELECT phrase_rv, phrase_ko, phrase_nv FROM verses WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
v = cur.fetchone()
print(f"\n[Test 3] Matthew 2:1 Text: {v['phrase_rv']}")
comb = f"{v['phrase_rv'] or ''} {v['phrase_ko'] or ''}"
detected_mat2 = []
for entry in all_entries:
    name_ko = entry["name_ko"]
    aliases = [a.strip() for a in (entry["aliases"] or "").split(",") if a.strip()]
    if name_ko in comb:
        detected_mat2.append(entry)
    else:
        for a in aliases:
            if len(a) >= 2 and a in comb:
                detected_mat2.append(entry)
                break
print(f"Detected in Mat 2:1: {[d['name_ko'] for d in detected_mat2]}")
