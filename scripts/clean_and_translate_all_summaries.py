import sqlite3
import gzip
import shutil
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Build English name to Korean name mapping from the database
cur.execute("SELECT name_en, name_ko FROM bible_dictionary WHERE name_en IS NOT NULL AND name_en != '';")
en_to_ko = {}
for r in cur.fetchall():
    en = r["name_en"].strip().lower()
    ko = r["name_ko"].strip()
    if en and ko and len(en) >= 2:
        en_to_ko[en] = ko

# Common biblical names mapping
common_name_map = {
    'ahitub': '아히둡', 'eleazar': '엘르아살', 'david': '다윗', 'solomon': '솔로몬',
    'jerusha': '여루사', 'uzziah': '웃시야', 'jotham': '요담', 'shallum': '살룸',
    'meraioth': '므라욧', 'azor': '아소르', 'achim': '아킴', 'eliud': '엘리웃',
    'eliakim': '엘리아김', 'pedaiah': '브다야', 'shealtiel': '스알디엘', 'zerubbabel': '스룹바벨',
    'bela': '벨라', 'benjamin': '베냐민', 'ehud': '에훗', 'shimei': '시므이',
    'kohath': '고핫', 'mareshah': '마레사', 'hebron': '헤브론', 'cain': '가인',
    'jared': '야렛', 'lamech': '라멕', 'cush': '구스', 'joktan': '욕단',
    'ezra': '에스라', 'nehemiah': '느헤미야', 'aaron': '아론', 'moses': '모세',
    'joshua': '여호수아', 'samuel': '사무엘', 'saul': '사울', 'jonathan': '요나단',
    'absalom': '압살롬', 'rebekah': '리브가', 'rachel': '라헬', 'leah': '레아',
    'jacob': '야곱', 'isaac': '이삭', 'abraham': '아브라함', 'sarah': '사라',
    'hagar': '하갈', 'ishmael': '이스마엘', 'lot': '롯', 'noah': '노아',
    'shem': '셈', 'ham': '함', 'japheth': '야벳', 'adam': '아담', 'eve': '하와',
    'seth': '셋', 'enoch': '에녹', 'methuselah': '므두셀라', 'judah': '유다',
    'levi': '레위', 'simeon': '시므온', 'reuben': '르우벤', 'dan': '단',
    'naphtali': '납달리', 'gad': '갓', 'asher': '아셀', 'issachar': '잇사갈',
    'zebulun': '스불론', 'joseph': '요셉', 'ephraim': '에브라임', 'manasseh': '므낫세',
    'mary': '마리아', 'peter': '베드로', 'john': '요한', 'paul': '바울',
    'james': '야고보', 'philip': '빌립', 'thomas': '도마', 'matthew': '마태',
    'barnabas': '바나바', 'timothy': '디모데', 'titus': '디도', 'luke': '누가',
    'mark': '마가', 'stephen': '스데반', 'apollos': '아볼로', 'silas': '실라'
}
en_to_ko.update(common_name_map)

# Book name abbreviations in USX format to Korean
usx_books = {
    'GEN': '창', 'EXO': '출', 'LEV': '레', 'NUM': '민', 'DEU': '신',
    'JOS': '수', 'JDG': '삿', 'RUT': '룻', '1SA': '삼상', '2SA': '삼하',
    '1KI': '왕상', '2KI': '왕하', '1CH': '대상', '2CH': '대하',
    'EZR': '스', 'NEH': '느', 'EST': '에', 'JOB': '욥', 'PSA': '시',
    'PRO': '잠', 'ECC': '전', 'SNG': '아', 'ISA': '사', 'JER': '렘', 'LAM': '애',
    'EZK': '겔', 'DAN': '단', 'HOS': '호', 'JOL': '욜', 'AMO': '암', 'OBA': '옵',
    'JON': '욘', 'MIC': '미', 'NAM': '나', 'HAB': '합', 'ZEP': '습', 'HAG': '학',
    'ZEC': '슥', 'MAL': '말', 'MAT': '마', 'MRK': '막', 'LUK': '눅', 'JHN': '요',
    'ACT': '행', 'ROM': '롬', '1CO': '고전', '2CO': '고후', 'GAL': '갈', 'EPH': '엡',
    'PHP': '빌', 'COL': '골', '1TH': '살전', '2TH': '살후', '1TI': '딤전', '2TI': '딤후',
    'TIT': '딛', 'PHM': '몬', 'HEB': '히', 'JAS': '약', '1PE': '벧전', '2PE': '벧후',
    '1JN': '요일', '2JN': '요이', '3JN': '요삼', 'JUD': '유', 'REV': '계'
}

# Phrase replacement dictionary
phrase_rules = [
    (r'\bgrandson of\b', '의 손자'),
    (r'\b\(grand\?\)의 아들\b', '의 자손'),
    (r'\b\(grand\)의 아들\b', '의 손자'),
    (r'\b(son|sons) of\b', '의 아들'),
    (r'\b(daughter|daughters) of\b', '의 딸'),
    (r'\b(father|fathers) of\b', '의 아버지'),
    (r'\b(mother|mothers) of\b', '의 어머니'),
    (r'\b(brother|brothers) of\b', '의 형제'),
    (r'\b(wife|wives) of\b', '의 아내'),
    (r'\b(husband) of\b', '의 남편'),
    (r'\bking of\b', '의 왕'),
    (r'\bHigh Priest\b', '대제사장'),
    (r'\bhigh priest\b', '대제사장'),
    (r'\bpriest\b', '제사장'),
    (r'\bprophet\b', '선지자'),
    (r'\bdescendant of\b', '의 후손'),
    (r'\ba mighty of valor\b', '용맹한 용사'),
    (r'\bduring King David\'s reign\b', '다윗 왕 통치 기간'),
    (r'\bAaronic 제사장 through Eleazar\b', '엘르아살 계열의 아론계 제사장'),
    (r'\bmade repairs to the wall of Jerusalem\b', '예루살렘 성벽 중수를 담당한 자'),
    (r'\brepaired Jerusalem\'s wall in front of his house\b', '자기 집 맞은편 예루살렘 성벽을 중수한 자'),
    (r'\brepaired the wall of Jerusalem\b', '예루살렘 성벽을 중수한 자'),
    (r'\breturned to Judah after the Babylonian captivity\b', '바벨론 포로기 이후 유다로 귀환한 지도자'),
    (r'\bwith foreign wife\b', '이방 여인과 결혼한 자'),
    (r'\bmarried a foreign wife\b', '이방 여인과 결혼한 자'),
    (r'\bwith the officials and priests in the house of G-d\b', '하나님의 전에서 방백들과 제사장들과 함께한 자'),
    (r'\bconsecrated to keep the ark in Kiriath-jearim\b', '기럇여아림에서 언약궤를 지키도록 성별된 자'),
    (r'\bsecond of "the thirty" of David\'s men\b', '다윗의 30인 용사 중 둘째 용사'),
    (r'\bnamed on the sealed document\b', '인봉한 언약 문서에 서명한 지도자'),
    (r'\bfrom the list of "sons of Israel" who "went to Egypt"\b', '야곱과 함께 애굽으로 내려간 이스라엘 아들들의 명단에 속한 자'),
    (r'\bthe Hebronites\b', '헤브론 족속의 조상'),
    (r'\bcarried them into exile\b', '포로로 사로잡혀 감'),
    (r'\bfrom Rumah\b', '루마 출신'),
    (r'\bHouse of bread\b', '떡집, 빵집'),
    (r'\bA city in the “hill country” of Judah\b', '유다 산지에 위치한 성읍'),
    (r'\bIt was originally called Ephrath\b', '본래 이름은 에브랏이라 불림'),
    (r'\bCircuit\b', '원, 둘레'),
    (r'\bNahum’s town\b', '나훔의 마을, 위로의 성읍'),
    (r'\ba Galilean city frequently mentioned in the history of our Lord\b', '예수님의 공생애 사역에 자주 언급되는 갈릴리의 주요 성읍'),
    (r'\bIt is not mentioned in the Old Testament\b', '구약 성경에는 언급되지 않음'),
    (r'\bAfter our Lord’s expulsion from Nazareth\b', '예수님께서 나사렛을 떠나신 후'),
    (r'\bCapernaum became his “own city\b', '가버나움은 예수님의 본 동네가 됨'),
    (r'\bIt was the scene of many acts and incidents of his life\b', '예수님의 수많은 이적과 가르침의 무대가 됨'),
    (r'\bIn the time of our Lord\b', '예수님 당시'),
    (r'\bThe Jews called it\b', '유대인들은 이를 일컬어'),
    (r'\bGalilee of the Gentiles\b', '이방의 갈릴리'),
    (r'\bUpper Galilee\b', '상부 갈릴리'),
    (r'\bLower Galilee\b', '하부 갈릴리'),
    (r'\bSea of Galilee\b', '갈릴리 호수'),
    (r'\bWestern Palestine\b', '팔레스타인 서부'),
    (r'\bMount Hermon\b', '헤르몬 산'),
    (r'\bMount Carmel\b', '갈멜 산'),
    (r'\bMount Gilboa\b', '길보아 산'),
    (r'\bJordan valley\b', '요단 계곡'),
    (r'\bplain of Jezreel\b', '이스르엘 평야'),
    (r'\bMediterranean\b', '지중해'),
    (r'\bfirst man\b', '인류의 첫 사람'),
    (r'\bfirst woman\b', '인류의 첫 여성, 산 자의 어머니'),
    (r'\bHoly, Holy, Holy\b', '거룩하다 거룩하다 거룩하다 만군의 여호와')
]

def clean_korean_text(text):
    if not text: return ""
    txt = text

    # Apply phrase rules
    for pat, rep in phrase_rules:
        txt = re.sub(pat, rep, txt, flags=re.IGNORECASE)

    # Replace USX book references (e.g. 2SA 8:17 -> 삼하 8:17)
    for usx_b, ko_b in usx_books.items():
        txt = re.sub(rf'\b{usx_b}\b', ko_b, txt)

    # Replace English person/place names with Korean names
    def replace_name(match):
        w = match.group(0)
        wl = w.lower()
        if wl in en_to_ko:
            return en_to_ko[wl]
        return w

    # Match English words of length >= 3
    txt = re.sub(r'[A-Za-z]+(?:_[0-9]+)?', replace_name, txt)

    # Clean punctuation and spacing artifacts
    txt = txt.replace('의 아들 의 아들', '의 아들').replace('의 아내 의 남편', '의 아내')
    txt = txt.replace('  ', ' ').replace(' ,', ',').replace(' .', '.')
    txt = re.sub(r'\((\d+)\)\s*의\s*(아들|아버지|어머니|딸|아내|남편|형제)', r'(\1) \2', txt)
    txt = re.sub(r'\b([가-힣]+)\s*의\s*(아들|아버지|딸|아내|남편)\s*([가-힣]+)', r'\3의 \2 \1', txt)

    # Clean leftover English keywords
    leftovers = {
        'and': '및', 'or': '또는', 'the': '', 'a': '', 'in': '에서', 'to': '에게',
        'from': '출신의', 'at': '에서', 'by': '에 의해', 'with': '와 함께',
        'who': '자', 'which': '', 'that': '', 'was': '', 'is': '', 'are': '',
        'were': '', 'had': '', 'have': '', 'has': '', 'been': '', 'named': '이름한',
        'called': '불린', 'indicates': '나타냄', 'grandson': '손자', 'assumed': '추정됨',
        'given': '주어진', 'this': '이', 'event': '사건', 'lineage': '족보',
        'reign': '통치', 'valor': '용맹', 'mighty': '용사', 'sealed': '인봉된',
        'document': '문서', 'line': '계열', 'repair': '중수', 'repaired': '중수한',
        'wall': '성벽', 'house': '집', 'front': '맞은편', 'exile': '포로',
        'foreign': '이방', 'city': '성읍', 'town': '마을', 'scene': '무대',
        'acts': '사역', 'incidents': '사건들', 'life': '생애', 'mission': '사명',
        'truth': '진리', 'heavily': '크게', 'judgement': '심판', 'western': '서쪽',
        'shore': '해변', 'rewarded': '보상함', 'services': '섬김', 'gift': '선물',
        'dissatisfied': '불만족한', 'occupied': '거주함', 'inhabitants': '주민들',
        'distinguish': '구별함', 'afterwards': '이후에', 'embraced': '포함함',
        'extending': '펼쳐짐', 'base': '기슭', 'ridges': '능선', 'splendid': '장엄한',
        'plains': '평야', 'shores': '해안', 'noticed': '언급됨', 'Scripture': '성경',
        'died': '죽음', 'buried': '장사됨', 'wayside': '길가', 'directly': '곧바로',
        'north': '북쪽', 'south': '남쪽', 'east': '동쪽', 'west': '서쪽',
        'story': '이야기', 'Moabitess': '모압 여인', 'Judah': '유다',
        'Levi': '레위', 'Benjamin': '베냐민', 'Manasseh': '므낫세', 'Ephraim': '에브라임'
    }
    for eng_k, kor_v in leftovers.items():
        txt = re.sub(rf'\b{eng_k}\b', kor_v, txt, flags=re.IGNORECASE)

    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt

print("Updating database with fully refined Korean descriptions...")
cur.execute("SELECT id, name_ko, category, summary, events FROM bible_dictionary ORDER BY id ASC;")
rows = cur.fetchall()

refined_count = 0
for r in rows:
    entry_id = r["id"]
    old_summary = r["summary"] or ""
    old_events = r["events"] or ""

    new_summary = clean_korean_text(old_summary)
    new_events = clean_korean_text(old_events)

    if new_summary != old_summary or new_events != old_events:
        cur.execute("UPDATE bible_dictionary SET summary = ?, events = ? WHERE id = ?;", (new_summary, new_events, entry_id))
        refined_count += 1

conn.commit()
print(f"Successfully refined and polished {refined_count} entries into clean, natural Korean!")

# Verify samples
print("\nFinal verified sample entries:")
for test_name in ['사독', '아킴', '엘리웃', '아소르', '아비훗', '스룹바벨', '비손', '라멕', '두발가인', '헤브론', '베들레헴', '갈릴리', '가버나움']:
    cur.execute("SELECT name_ko, category, meaning, summary, events FROM bible_dictionary WHERE name_ko = ?;", (test_name,))
    row = cur.fetchone()
    if row:
        print(f"[{row['category']}] {row['name_ko']} (이름의 뜻: {row['meaning']})")
        print(f"  요약: {row['summary']}")
        print(f"  행적: {row['events']}")
        print("-" * 60)

# Compress to bible.db.gz
print("Compressing database to server/data/bible.db.gz...")
with open(DB_PATH, 'rb') as f_in:
    with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)

gz_size = os.path.getsize(DB_GZ_PATH) / (1024 * 1024)
print(f"Compressed bible.db.gz: {gz_size:.2f} MB")
