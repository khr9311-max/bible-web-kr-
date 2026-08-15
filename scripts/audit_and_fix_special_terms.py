import sqlite3
import gzip
import shutil
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Special Biblical terms, offices, covenants, and sacred groups that must have authentic theological depth
special_theological_terms = [
    {
        "name_ko": "나실",
        "aliases": "나실, 나실인, 나실인의 서원, 나실인 서원",
        "name_en": "Nazirite / Nazarite",
        "name_original": "נָזִיר (H5139) / 어근: נָזַר (구별하다, 성별하다)",
        "category": "단어",
        "meaning": "구별된 자, 성별된 자, 하나님께 온전히 봉헌된 사람",
        "summary": "하나님께 특별한 서원을 하여 일정 기간 혹은 평생 동안 자기 몸과 삶을 거룩하게 구별하여 바친 사람(민수기 6장의 '나실인의 법'). 남녀 누구나 자원하여 서원할 수 있었으며, 평생 나실인으로 하나님께 바쳐진 삼손, 사무엘, 세례 요한이 대표적입니다.",
        "events": "나실인의 3대 성별 규례: (1) 포도나무 소산(포도주, 독주, 생포도, 건포도, 씨, 껍질) 일체 금지(세속 쾌락 단절 및 오직 여호와로 기뻐함), (2) 머리에 삭도를 대지 않음(하나님의 거룩한 주권 아래 있음을 나타내는 표식), (3) 시체 접촉 금지(대제사장과 동등한 최상의 거룩함 유지). 신약에서는 사도 바울도 나실인 결례를 행했습니다 (민 6:1-21, 삿 13:5, 삼상 1:11, 눅 1:15, 행 18:18, 행 21:23-26).",
        "key_verses": "민 6:2; 민 6:5; 민 6:8; 삿 13:5; 삿 16:17; 삼상 1:11; 암 2:11-12; 눅 1:15; 행 18:18; 행 21:24"
    },
    {
        "name_ko": "느디님",
        "aliases": "느디님, 느디님 사람, 느디님 사람들",
        "name_en": "Nethinim",
        "name_original": "נְתִינִים (H5411) / 바쳐진 자들 (Given ones)",
        "category": "단어",
        "meaning": "주어진 자들, 하나님과 성전에 온전히 바쳐진 봉사자",
        "summary": "성전에서 제사장과 레위인들을 도와 나무를 패고 물을 긷는 등 성전의 궂은일과 헌신적인 수종을 담당하도록 성별된 성전 봉사자 계층.",
        "events": "원래 기브온 주민(수 9:27)과 다윗 왕 및 방백들이 성전 봉사를 위해 성별하여 준 자들로(스 8:20), 바벨론 포로 후 예루살렘으로 귀환하여 무너진 성벽(오벨 맞은편)을 중수하고 거룩한 성전 봉사를 신실하게 이어갔습니다 (대상 9:2, 스 2:43, 스 8:20, 느 3:26, 느 10:28).",
        "key_verses": "대상 9:2; 스 2:43; 스 8:20; 느 3:26; 느 7:46; 느 10:28"
    },
    {
        "name_ko": "레갑",
        "aliases": "레갑, 레갑 족속, 레갑 사람들",
        "name_en": "Rechabites",
        "name_original": "רֵכָב (H7394) / 기수, 전차병",
        "category": "단어",
        "meaning": "말 타는 자, 기수, 절개와 순종의 가문",
        "summary": "모세의 장인 이드로 계열인 겐 족속의 후손(대상 2:55). 선조 요나답(여호나답)의 훈계를 따라 수백 년 동안 포도주를 마시지 않고, 집을 짓지 않으며, 파종하지 않고 장막에 거주하며 거룩한 순결을 지킨 가문.",
        "events": "예레미야 선지자 시대에 하나님께서 타락한 유다 백성의 불순종을 책망하시기 위해 레갑 족속의 철저한 조상 훈계 순종을 모범으로 제시하셨으며, 하나님은 '레갑의 아들 요나답에게서 내 앞에 설 사람이 영원히 끊어지지 아니하리라'(렘 35:19)는 축복의 언약을 주셨습니다.",
        "key_verses": "왕하 10:15; 대상 2:55; 렘 35:2; 렘 35:6; 렘 35:19"
    },
    {
        "name_ko": "네피림",
        "aliases": "네피림, 거인",
        "name_en": "Nephilim",
        "name_original": "נְפִילִים (H5303) / 떨어진 자들, 거인",
        "category": "단어",
        "meaning": "하늘에서 떨어진 자, 압제자, 고대의 거인들",
        "summary": "노아 홍수 이전 하나님의 아들들과 사람의 딸들 사이에서 태어난 고대의 거인 용사들이자 당대의 유명한 폭력자들 (창 6:4).",
        "events": "가나안 탐지 때 10명의 불신앙적 정탐꾼들이 헤브론의 아낙 자손을 보며 '우리는 스스로 보기에도 메뚜기 같으니 그들의 보기에도 그와 같았을 것이라'고 두려워하며 네피림 후손에 비유했습니다 (창 6:4, 민 13:33).",
        "key_verses": "창 6:4; 민 13:33"
    },
    {
        "name_ko": "아낙",
        "aliases": "아낙, 아낙 자손, 아낙 족속",
        "name_en": "Anakim / Anak",
        "name_original": "עֲנָק (H6061) / 목이 긴 자, 거인",
        "category": "단어",
        "meaning": "목이 긴 자, 거대한 체구의 족속",
        "summary": "가나안 헤브론 산지와 남부 산악 지대에 거주했던 키가 매우 크고 용맹한 고대 거인 족속. 아낙의 세 아들(세새, 아히만, 달매)이 헤브론을 지배했습니다.",
        "events": "이스라엘 정탐꾼들을 두려움에 떨게 했으나(민 13:22), 85세의 갈렙이 믿음으로 '이 산지를 지금 내게 주소서'라고 선포하고 헤브론에서 아낙 자손을 완전히 몰아내고 기업을 차지했습니다 (수 14:12-15, 수 15:14, 삿 1:20).",
        "key_verses": "민 13:22; 민 13:28; 민 13:33; 신 9:2; 수 14:12; 수 15:14; 삿 1:20"
    },
    {
        "name_ko": "고핫",
        "aliases": "고핫, 고핫 자손",
        "name_en": "Kohath / Kohathites",
        "name_original": "קְהָת (H6955) / 집회, 모임",
        "category": "단어",
        "meaning": "모임, 회중, 성막 지성물 운반 직무",
        "summary": "레위의 둘째 아들이자 모세와 아론의 조부. 고핫 자손은 레위 지파 중에서도 가장 거룩한 성막의 지성물(언약궤, 떡상, 등잔대, 분향단, 번제단 등)을 관리하고 어깨에 메어 운반하는 최고 거룩한 직무를 맡았습니다.",
        "events": "지성물은 수레에 싣지 않고 반드시 제사장들이 보자기로 싼 후 거룩한 채를 꿰어 어깨에 직접 메어야 했습니다 (출 6:16, 민 3:27-32, 민 4:4-15, 민 7:9, 대상 6:1-3).",
        "key_verses": "출 6:16; 출 6:18; 민 3:27; 민 4:4; 민 4:15; 민 7:9; 대상 6:1"
    },
    {
        "name_ko": "게르손",
        "aliases": "게르손, 게르손 자손",
        "name_en": "Gershon / Gershonites",
        "name_original": "גֵּרְשׁוֹן (H1648) / 추방, 이방인",
        "category": "단어",
        "meaning": "나그네 됨, 성막 휘장과 덮개 운반 직무",
        "summary": "레위의 맏아들. 게르손 자손은 광야 이동 시 성막의 거룩한 앙장(휘장), 해달의 가죽 덮개, 회막 문장, 뜰의 휘장과 줄들을 관리하고 두 대의 수레와 네 마리 소로 운반하는 사역을 담당했습니다.",
        "events": "성막의 외관과 덮개 성물들을 보호하고 이동시키는 헌신을 감당했습니다 (출 6:16, 민 3:21-26, 민 4:21-28, 민 7:7).",
        "key_verses": "출 6:16; 민 3:21; 민 4:24; 민 7:7; 대상 6:1"
    },
    {
        "name_ko": "므라리",
        "aliases": "므라리, 므라리 자손",
        "name_en": "Merari / Merarites",
        "name_original": "מְרָרִי (H4847) / 쓰라림, 쓴 것",
        "category": "단어",
        "meaning": "비터(쓴맛), 성막 널판과 기둥 운반 직무",
        "summary": "레위의 셋째 아들. 므라리 자손은 성막의 널판, 띠, 기둥, 받침, 말뚝 등 무겁고 견고한 성막의 뼈대와 골격 구조물들을 관리하고 네 대의 수레와 여덟 마리 소로 운반하는 중책을 맡았습니다.",
        "events": "성막이 든든히 서도록 무거운 하중을 지탱하는 기초 구조물들을 책임졌습니다 (출 6:16, 민 3:33-37, 민 4:29-33, 민 7:8).",
        "key_verses": "출 6:16; 민 3:33; 민 4:31; 민 7:8; 대상 6:1"
    },
    {
        "name_ko": "그렛 사람",
        "aliases": "그렛 사람, 그렛 사람과 블렛 사람",
        "name_en": "Cherethites",
        "name_original": "כְּרֵתִי (H3774) / 처형자, 궁수",
        "category": "단어",
        "meaning": "베어내는 자, 다윗 왕의 정예 친위대",
        "summary": "다윗 왕의 신실하고 용맹한 왕실 근위대(경호대)를 구성했던 정예 부대. 여호야다의 아들 브나야의 지휘를 받았습니다.",
        "events": "압살롬의 반역과 세바의 반란 때에도 변함없이 다윗 왕을 끝까지 호위하며 충성하였고, 솔로몬 왕의 즉위식 때 다윗의 노새에 솔로몬을 태우고 기혼 샘으로 호위하여 솔로몬을 왕으로 옹립했습니다 (삼하 8:18, 삼하 15:18, 삼하 20:7, 왕상 1:38-44).",
        "key_verses": "삼하 8:18; 삼하 15:18; 삼하 20:7; 왕상 1:38; 대상 18:17"
    },
    {
        "name_ko": "블렛 사람",
        "aliases": "블렛 사람, 블렛 사람과 그렛 사람",
        "name_en": "Pelethites",
        "name_original": "פְּלֵתִי (H6432) / 신속한 자, 전령",
        "category": "단어",
        "meaning": "신속한 주자, 다윗의 왕실 친위대",
        "summary": "그렛 사람과 함께 다윗 왕의 곁을 지키며 호위한 왕실 정예 친위대. 빠른 기동력과 충성심으로 무장된 용사들.",
        "events": "다윗과 솔로몬의 왕권을 보호하고 하나님의 기름 부음 받은 왕실의 안위를 목숨 걸고 수호했습니다 (삼하 8:18, 왕상 1:38).",
        "key_verses": "삼하 8:18; 삼하 15:18; 왕상 1:38"
    }
]

print("Updating special theological terms...")
for term in special_theological_terms:
    cur.execute("""
        UPDATE bible_dictionary
        SET category = ?,
            name_en = ?,
            name_original = ?,
            meaning = ?,
            summary = ?,
            events = ?,
            key_verses = COALESCE(NULLIF(key_verses, ''), ?),
            aliases = ?
        WHERE name_ko = ?;
    """, (
        term["category"], term["name_en"], term["name_original"],
        term["meaning"], term["summary"], term["events"],
        term["key_verses"], term["aliases"], term["name_ko"]
    ))

conn.commit()
print("Successfully enriched special theological terms!")

# Verification of '나실'
cur.execute("SELECT * FROM bible_dictionary WHERE name_ko = '나실';")
row = cur.fetchone()
if row:
    print(f"\n[Verified] {row['name_ko']} ({row['name_en']})")
    print(f"  카테고리: {row['category']}")
    print(f"  원어: {row['name_original']}")
    print(f"  의미: {row['meaning']}")
    print(f"  요약: {row['summary']}")
    print(f"  행적/규례: {row['events']}")
    print(f"  대표구절: {row['key_verses']}")

# Compress to bible.db.gz
print("\nCompressing database to server/data/bible.db.gz...")
with open(DB_PATH, 'rb') as f_in:
    with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)

gz_size = os.path.getsize(DB_GZ_PATH) / (1024 * 1024)
print(f"Compressed bible.db.gz: {gz_size:.2f} MB")
