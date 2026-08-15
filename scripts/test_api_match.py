import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def test_api_dictionary_verse(unit_code, jeol):
    cur.execute("SELECT phrase_rv, phrase_ko, phrase_nv FROM verses WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
    verse_row = cur.fetchone()
    if not verse_row: return

    raw_rv = verse_row["phrase_rv"] or ""
    raw_ko = verse_row["phrase_ko"] or ""

    b_names = set(re.findall(r'<b>([^<]+)</b>', raw_rv) + re.findall(r'<b>([^<]+)</b>', raw_ko))
    
    matched_map = {}
    if b_names:
        placeholders = ",".join("?" for _ in b_names)
        cur.execute(f"SELECT * FROM bible_dictionary WHERE name_ko IN ({placeholders}) ORDER BY id ASC;", tuple(b_names))
        for r in cur.fetchall():
            matched_map[r["id"]] = dict(r)

    def clean_verse_text(text):
        txt = re.sub(r'<cite>\d+</cite>', '', text)
        txt = re.sub(r'<u[^>]*>[^<]*</u>', '', txt)
        txt = re.sub(r'<[^>]+>', '', txt)
        return txt.strip()

    clean_txt = f"{clean_verse_text(raw_rv)} {clean_verse_text(raw_ko)}"
    particles = r'(?:에서|으로|로써|으로써|부터|께서|에게|한테|이라|라고|이며|[이가은는을를과와의도만에로라며께])?'

    def match_word(word, text):
        if not word or len(word) < 1: return False
        pattern = rf'(?:^|[\s"\'(\[\-])' + re.escape(word) + rf'{particles}(?=[\s.,?!;:\)\]\-]|$)'
        return bool(re.search(pattern, text))

    cur.execute("SELECT * FROM bible_dictionary WHERE category = '단어' OR aliases != '' ORDER BY id ASC;")
    core_entries = [dict(r) for r in cur.fetchall()]

    for entry in core_entries:
        if entry["id"] in matched_map:
            continue
        name_ko = entry["name_ko"]
        aliases = [a.strip() for a in (entry["aliases"] or "").split(",") if a.strip()]

        base_names = [name_ko] + aliases
        is_match = False
        for n in base_names:
            if len(n) >= 2 and match_word(n, clean_txt):
                is_match = True
                break
            elif len(n) == 1 and n in ["금", "은", "놋", "철"]:
                if match_word(n, clean_txt):
                    is_match = True
                    break

        if is_match:
            matched_map[entry["id"]] = entry

    results = list(matched_map.values())
    print(f"\n[API Output for Unit {unit_code} Jeol {jeol}]: ({len(results)} items)")
    for item in results:
        print(f"  📌 [{item['category']}] {item['name_ko']} ({item['name_en']}) - {item['summary'][:60]}...")

test_api_dictionary_verse(40001, 1)  # 마태복음 1:1
test_api_dictionary_verse(40001, 16) # 마태복음 1:16
test_api_dictionary_verse(40003, 1)  # 마태복음 3:1
test_api_dictionary_verse(43001, 19) # 요한복음 1:19
