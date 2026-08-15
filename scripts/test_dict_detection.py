import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def test_verse(unit_code, jeol):
    cur.execute("SELECT phrase_rv, phrase_ko, phrase_nv FROM verses WHERE unit_code = ? AND jeol = ?;", (unit_code, jeol))
    r = cur.fetchone()
    if not r: return
    raw_rv = r["phrase_rv"]
    raw_ko = r["phrase_ko"]
    print(f"\n--- [Unit {unit_code} Jeol {jeol}] ---")
    print("RV Text:", raw_rv)
    b_names = list(set(re.findall(r'<b>([^<]+)</b>', raw_rv) + re.findall(r'<b>([^<]+)</b>', raw_ko)))
    print("Detected bold names:", b_names)
    if b_names:
        placeholders = ",".join("?" for _ in b_names)
        cur.execute(f"SELECT id, name_ko, name_en, category, meaning, summary FROM bible_dictionary WHERE name_ko IN ({placeholders})", tuple(b_names))
        for row in cur.fetchall():
            print(f"  👉 [{row['category']}] {row['name_ko']} (영문: {row['name_en']}) | 뜻: {row['meaning']}\n     요약: {row['summary']}")

test_verse(40001, 1)  # 마태복음 1:1 (아브라함, 다윗, 예수 그리스도)
test_verse(40001, 16) # 마태복음 1:16 (야곱, 요셉, 마리아, 그리스도, 예수)
test_verse(40003, 1)  # 마태복음 3:1 (세례 요한)
test_verse(43001, 19) # 요한복음 1:19 (요한의 증언)
