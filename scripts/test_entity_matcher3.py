import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def clean_html(text):
    if not text: return ""
    txt = re.sub(r'<cite>\d+</cite>', '', text)
    txt = re.sub(r'<u[^>]*>[^<]*</u>', '', txt)
    txt = re.sub(r'<[^>]+>', '', txt)
    return txt.strip()

PARTICLES = r'(?:에서|으로|로써|으로써|부터|께서|에게|한테|이라|라고|이며|[이가은는을를과와의도만에로라며께])?'

def match_entity_in_text(name_or_alias, clean_txt):
    if not name_or_alias or len(name_or_alias) < 1:
        return False
    
    # Prefix boundary: start of string, whitespace, quotes, punctuation, or marks
    # Postfix boundary: allowed particle or punctuation/end
    pattern = rf'(?:^|[\s"\'(\[\-])' + re.escape(name_or_alias) + rf'{PARTICLES}(?=[\s.,?!;:\)\]\-]|$)'
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
    
    base_names = [name_ko] + aliases
    if ' ' in name_ko:
        base_names.extend([p for p in name_ko.split() if len(p) >= 2])

    is_match = any(match_entity_in_text(n, clean_mat2) for n in base_names)
    if is_match:
        detected.append(entry)

print("Properly detected in Mat 2:1:", [f"{d['name_ko']} ({d['category']})" for d in detected])
