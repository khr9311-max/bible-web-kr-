import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def clean_html(text):
    if not text: return ""
    return re.sub(r'<[^>]+>', '', text)

def match_entity_in_text(name_or_alias, clean_txt):
    if not name_or_alias or len(name_or_alias) < 1:
        return False
    # If 1-2 char word, ensure word boundary (not attached to prior letters)
    pattern = rf'(?:^|[\s"\'(\[\-])' + re.escape(name_or_alias) + rf'(?:[이가은는을를과와의에게도만]|(?=[\s.,?!;:\)\]\-]|$))'
    return bool(re.search(pattern, clean_txt))

cur.execute("SELECT * FROM bible_dictionary;")
all_entries = [dict(r) for r in cur.fetchall()]

# Test with Matthew 2:1
cur.execute("SELECT phrase_rv FROM verses WHERE unit_code = 40002 AND jeol = 1;")
raw_mat2 = cur.fetchone()["phrase_rv"]
clean_mat2 = clean_html(raw_mat2)
print("Clean Matthew 2:1:", clean_mat2)

detected = []
for entry in all_entries:
    name_ko = entry["name_ko"]
    aliases = [a.strip() for a in (entry["aliases"] or "").split(",") if a.strip()]
    
    is_match = False
    if match_entity_in_text(name_ko, clean_mat2):
        is_match = True
    else:
        for a in aliases:
            if match_entity_in_text(a, clean_mat2):
                is_match = True
                break
    if is_match:
        detected.append(entry)

print("Properly detected in Mat 2:1:", [d["name_ko"] for d in detected])

# Test with Genesis 12:1
cur.execute("SELECT phrase_rv FROM verses WHERE unit_code = 1012 AND jeol = 1;")
raw_gen12 = clean_html(cur.fetchone()["phrase_rv"])
print("\nClean Genesis 12:1:", raw_gen12)
detected_gen12 = []
for entry in all_entries:
    name_ko = entry["name_ko"]
    aliases = [a.strip() for a in (entry["aliases"] or "").split(",") if a.strip()]
    is_match = False
    if match_entity_in_text(name_ko, raw_gen12):
        is_match = True
    else:
        for a in aliases:
            if match_entity_in_text(a, raw_gen12):
                is_match = True
                break
    if is_match:
        detected_gen12.append(entry)
print("Properly detected in Gen 12:1:", [d["name_ko"] for d in detected_gen12])
