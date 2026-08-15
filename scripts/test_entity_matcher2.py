import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def clean_html(text):
    if not text: return ""
    # Strip <cite>, <u ...>, and standard html tags
    txt = re.sub(r'<cite>\d+</cite>', '', text)
    txt = re.sub(r'<u[^>]*>[^<]*</u>', '', txt)
    txt = re.sub(r'<[^>]+>', '', txt)
    return txt.strip()

# Postpositions in Korean biblical texts: 이, 가, 은, 는, 을, 를, 과, 와, 의, 에게, 에, 에서, 으로, 로, 로써, 으로써, 부터, 께서, 께, 이라, 라, 라며, 고, 도, 만, 며
PARTICLES = r'(?:[이가은는을를과와의도만에(서)?로(써)?부터(이)?라(고)?(며)?께(서)?]|에게|한테)?'

def match_entity_in_text(name_or_alias, clean_txt):
    if not name_or_alias or len(name_or_alias) < 1:
        return False
    
    # Prefix boundary: start of string, whitespace, quotes, punctuation, or single Korean mark
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
    
    # Also check short base name if name_ko contains space (e.g. '예수 그리스도' -> '예수', '그리스도')
    base_names = [name_ko] + aliases
    if ' ' in name_ko:
        base_names.extend([p for p in name_ko.split() if len(p) >= 2])

    is_match = any(match_entity_in_text(n, clean_mat2) for n in base_names)
    if is_match:
        detected.append(entry)

print("Properly detected in Mat 2:1:", [f"{d['name_ko']} ({d['category']})" for d in detected])
