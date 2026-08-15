import sqlite3
import urllib.request
import csv
import io
import gzip
import shutil
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

print("1. Fetching Hitchcock's Bible Names Dictionary from GitHub...")
hitchcock_url = 'https://raw.githubusercontent.com/BradyStephenson/bible-data/master/HitchcocksBibleNamesDictionary.csv'
hitchcock_dict = {} # lowercase english name -> meaning

try:
    req = urllib.request.Request(hitchcock_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        content = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            if len(row) >= 2:
                name = row[0].strip().lstrip('\ufeff')
                meaning = row[1].strip()
                if name and meaning:
                    hitchcock_dict[name.lower()] = (name, meaning)
    print(f"Loaded {len(hitchcock_dict)} names from Hitchcock's Dictionary.")
except Exception as e:
    print(f"Warning: Failed to fetch Hitchcock's: {e}")

# English to Korean common meaning translations
meaning_translations = {
    "just": "의로움",
    "justified": "의롭다 함을 얻음",
    "preparing": "준비함",
    "confirming": "확증함",
    "God is my praise": "하나님은 나의 찬송",
    "a helper": "돕는 자",
    "a court": "뜰, 법정",
    "father of praise": "찬송의 아버지",
    "father of a multitude": "열국의 아버지",
    "laughter": "웃음",
    "supplanter": "발꿈치를 잡은 자",
    "savior": "구원자",
    "the Lord is salvation": "여호와는 구원이시다",
    "beloved": "사랑을 받는 자",
    "peaceable": "평화로운 자",
    "my God is the Lord": "나의 하나님은 여호와이시다",
    "whom the Lord has appointed": "여호와께서 세우신 자",
    "God is my judge": "하나님은 나의 재판관이시다",
    "grace of the Lord": "여호와의 은혜",
    "exalted": "높여진 자",
    "small": "작은 자",
    "asked of God": "하나님께 구하여 얻음",
    "son of comfort": "위로의 아들",
    "honoring God": "하나님을 공경하는 자",
    "delight": "기쁨, 즐거움",
    "house of God": "하나님의 집",
    "association": "연합, 교제",
    "house of bread": "떡집, 빵집",
    "foundation of peace": "평화의 터전",
    "circle": "원, 둘레",
    "branch": "가지, 싹",
    "village of comfort": "나훔의 마을",
    "descender": "내려오는 자",
    "fragrant": "향기의 성읍",
    "oil press": "기름 짜는 틀",
    "skull": "해골",
    "strength": "힘, 능력",
    "friendship": "우정",
    "in him is strength": "그에게 능력이 있다",
    "heard of God": "하나님이 들으셨다",
    "strength of the Lord": "여호와의 힘",
    "the Lord heals": "여호와께서 치료하심",
    "star": "별",
    "crown": "면류관",
    "whom God helps": "하나님이 도우시는 자",
    "pure": "순결한 자",
    "red": "붉음",
    "fruitful": "풍성함, 기름진 밭"
}

def translate_meaning(en_meaning):
    if not en_meaning: return ""
    ko_parts = []
    parts = re.split(r'[;,]\s*', en_meaning)
    for p in parts:
        p_clean = p.strip()
        if p_clean in meaning_translations:
            ko_parts.append(meaning_translations[p_clean])
        else:
            # Simple keyword matching
            matched = False
            for k, v in meaning_translations.items():
                if k.lower() in p_clean.lower():
                    ko_parts.append(v)
                    matched = True
                    break
            if not matched:
                ko_parts.append(p_clean)
    return ", ".join(ko_parts)

print("2. Connecting to SQLite database and collecting entity data...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get book metadata
cur.execute("SELECT id, name, abbr FROM books;")
book_rows = cur.fetchall()
book_map = {r["id"]: (r["name"], r["abbr"]) for r in book_rows}

# Keep existing hand-crafted rich profiles
cur.execute("SELECT name_ko, name_en, name_original, category, meaning, summary, events, key_verses, aliases FROM bible_dictionary;")
existing_rich_entries = {r["name_ko"]: dict(r) for r in cur.fetchall()}
print(f"Preserving {len(existing_rich_entries)} rich hand-crafted profiles.")

# Scan all verses with <b> tags
cur.execute("SELECT unit_code, book_id, chapter, jeol, phrase_rv, phrase_nv FROM verses WHERE phrase_rv LIKE '%<b>%';")
verse_rows = cur.fetchall()
print(f"Scanned {len(verse_rows)} verses with <b> entity tags.")

entity_data = {} # name_ko -> { 'occurrences': [(unit_code, jeol, book_name, abbr, chapter)], 'nv_samples': [] }

# Unit words or non-name terms to exclude
stop_words = {
    "규빗", "달란트", "므나", "세겔", "에바", "호멜", "스아", "힌", "오멜", "게라", "베가", 
    "일", "월", "년", "하룻길", "사흗길", "안식일", "유월절", "초막절", "오순절", "칠칠절", 
    "나팔절", "속죄일", "수전절", "부림절", "월삭", "안식년", "희년", "하나님", "여호와", "주"
}

for r in verse_rows:
    unit_code = r["unit_code"]
    b_id = r["book_id"]
    ch = r["chapter"]
    j = r["jeol"]
    b_info = book_map.get(b_id, ("성경", "성"))
    b_name, b_abbr = b_info
    
    matches = re.findall(r'<b>([^<]+)</b>', r["phrase_rv"])
    clean_nv = re.sub(r'<[^>]+>', ' ', r["phrase_nv"] or '')

    for m in matches:
        name = m.strip()
        if not name or len(name) > 12 or name in stop_words:
            continue
        # Exclude numeric strings or pure punctuation
        if re.match(r'^\d+$', name):
            continue
            
        if name not in entity_data:
            entity_data[name] = {
                "count": 0,
                "refs": [],
                "nv_text_samples": []
            }
        
        entity_data[name]["count"] += 1
        ref_str = f"{b_abbr} {ch}:{j}"
        if len(entity_data[name]["refs"]) < 8 and ref_str not in entity_data[name]["refs"]:
            entity_data[name]["refs"].append(ref_str)
        if len(entity_data[name]["nv_text_samples"]) < 5:
            entity_data[name]["nv_text_samples"].append(clean_nv)

print(f"Extracted {len(entity_data)} unique entity names across the Bible.")

# Known place keywords in Korean
place_suffixes = ('산', '강', '바다', '들', '못', '골짜기', '시내', '성', '읍', '궁', '땅', '광야', '섬', '나루')
known_places = {
    '에덴', '아라랏', '바벨', '우르', '하란', '가나안', '세겜', '벧엘', '헤브론', '소돔', '고모라',
    '브엘세바', '모리아', '애굽', '고센', '홍해', '마라', '엘림', '르비딤', '시내산', '호렙산',
    '가데스바네아', '에돔', '모압', '암몬', '바산', '길앗', '요단', '여리고', '아이', '길갈',
    '기브온', '실로', '벧세메스', '기럇여아림', '베들레헴', '예루살렘', '시온', '갈멜산', '길보아',
    '다메섹', '사마리아', '디르사', '앗수르', '니느웨', '바벨론', '갈대아', '수산', '갈릴리',
    '나사렛', '가버나움', '벳새다', '가나', '디베랴', '거라사', '막달라', '두로', '시돈',
    '가이사랴', '변화산', '베다니', '벳바게', '감람산', '겟세마네', '골고다', '갈보리', '엠마오',
    '욥바', '안디옥', '다소', '구브로', '버가', '이고니온', '루스드라', '더베', '드로아',
    '빌립보', '데살로니가', '베뢰아', '아덴', '고린도', '겐그레아', '에베소', '밀레도', '로마',
    '밧모', '밧모섬', '서머나', '버가모', '두아디라', '사데', '빌라델비아', '라오디게아', '골로새'
}

# Clear table
cur.execute("DELETE FROM bible_dictionary;")

inserted_count = 0

# Insert existing hand-crafted rich profiles first
for name_ko, profile in existing_rich_entries.items():
    cur.execute("""
        INSERT INTO bible_dictionary (name_ko, name_en, name_original, category, meaning, summary, events, key_verses, aliases)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        profile["name_ko"], profile["name_en"], profile["name_original"], profile["category"],
        profile["meaning"], profile["summary"], profile["events"], profile["key_verses"], profile["aliases"]
    ))
    inserted_count += 1

# Generate and insert comprehensive entries for all remaining biblical names
for name, data in entity_data.items():
    if name in existing_rich_entries:
        continue
    
    # Determine category (인물 vs 지명)
    is_place = False
    if name in known_places or any(name.endswith(sfx) for sfx in place_suffixes if len(name) > len(sfx)):
        is_place = True
    category = "지명" if is_place else "인물"
    
    # Try finding English name from Hitchcock or NV samples
    en_name = ""
    en_meaning = ""
    
    # 1. Search in Hitchcock by closest matching English word in NV samples
    for sample in data["nv_text_samples"]:
        words = re.findall(r'[A-Z][a-z]+', sample)
        for w in words:
            w_lower = w.lower()
            if w_lower in hitchcock_dict:
                h_name, h_meaning = hitchcock_dict[w_lower]
                en_name = h_name
                en_meaning = h_meaning
                break
        if en_name:
            break
            
    meaning_ko = translate_meaning(en_meaning) if en_meaning else ""
    
    # Key verse references
    key_verses_str = "; ".join(data["refs"])
    first_ref = data["refs"][0] if data["refs"] else "성경 본문"
    
    # Generate theological summary based on category and occurrences
    if category == "인물":
        summary = f"성경에 등장하는 {category}로, {first_ref} 등 총 {data['count']}회 언급됩니다. "
        if meaning_ko:
            summary += f"이름의 뜻은 '{meaning_ko}'이며, "
        summary += "하나님의 구속 역사 속에서 언약의 백성과 관련된 인물로 기록되어 있습니다."
    else:
        summary = f"성경에 등장하는 주요 {category}로, {first_ref} 등 총 {data['count']}회 언급됩니다. "
        if meaning_ko:
            summary += f"이름의 뜻은 '{meaning_ko}'이며, "
        summary += "성경의 역사적 사건과 구속사적 활동이 일어난 주요 지역입니다."

    events = f"{first_ref} 등 성경 본문에 기록된 주요 사건 및 계보에 등장합니다."

    cur.execute("""
        INSERT INTO bible_dictionary (name_ko, name_en, name_original, category, meaning, summary, events, key_verses, aliases)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, en_name, "", category, meaning_ko, summary, events, key_verses_str, ""
    ))
    inserted_count += 1

conn.commit()

cur.execute("SELECT count(*) FROM bible_dictionary;")
total = cur.fetchone()[0]
print(f"\n=======================================================")
print(f" Successfully built EXHAUSTIVE Bible Dictionary!")
print(f" Total Entries: {total}")
print(f"=======================================================")

# Verify specific minor entries like 사독 and 아킴
for test_name in ['사독', '아킴', '엘리웃', '아소르', '아비훗']:
    cur.execute("SELECT * FROM bible_dictionary WHERE name_ko = ?;", (test_name,))
    row = cur.fetchone()
    if row:
        print(f"Verified [{row['category']}] {row['name_ko']} ({row['name_en']}): meaning='{row['meaning']}', refs='{row['key_verses']}'")

# Re-compress bible.db to bible.db.gz
print("\nCompressing database to server/data/bible.db.gz...")
with open(DB_PATH, 'rb') as f_in:
    with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)

gz_size = os.path.getsize(DB_GZ_PATH) / (1024 * 1024)
print(f"Compressed bible.db.gz: {gz_size:.2f} MB")
