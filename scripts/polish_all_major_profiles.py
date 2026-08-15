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

# High-quality dedicated summaries and events for biblical places and characters
rich_place_profiles = {
    "베들레헴": {
        "summary": "예루살렘 남쪽 약 8km, 해발 약 777m의 유다 산지에 위치한 작은 성읍(옛 이름 '에브랏'). 야곱의 아내 라헬의 묘가 있는 곳이자, 룻과 보아스의 아름다운 구속사적 사랑의 무대이며, 이스라엘의 위대한 왕 다윗의 고향입니다.",
        "events": "미가 선지자의 예언(미 5:2)대로 만왕의 왕이신 예수 그리스도께서 탄생하신 거룩한 성지입니다 (눅 2:1-7, 마 2:1-6)."
    },
    "헤브론": {
        "summary": "예루살렘 남쪽 약 30km, 해발 약 920m의 유다 산지 중심 고원 도시(옛 이름 '기럇 아르바'). 아브라함이 아내 사라를 장사하기 위해 헷 족속에게서 매입한 막벨라 굴이 위치한 족장들의 무덤 성지입니다.",
        "events": "아브라함, 사라, 이삭, 리브가, 야곱, 레아가 묻힌 곳이며, 여호수아 정복 후 갈렙이 기업으로 요청하여 취하였고, 다윗이 왕으로 기름 부음 받아 7년 6개월간 통치한 유다 왕국의 첫 수도입니다 (삼하 2:1-4)."
    },
    "갈릴리": {
        "summary": "이스라엘 북부의 비옥하고 아름다운 지방으로, 헬몬산 기슭부터 이스르엘 평야에 이르는 광활한 지역(상부 및 하부 갈릴리). 갈릴리 호수(디베랴 바다, 게네사렛 호수)를 중심으로 어업과 농업이 번성했습니다.",
        "events": "구약 시대 '이방의 갈릴리'(사 9:1)로 불렸으나, 예수 그리스도께서 공생애 사역의 대부분을 보내시며 12제자를 부르시고 천국 복음을 전파하시며 수많은 표적을 행하신 은혜의 땅입니다 (마 4:12-25)."
    },
    "가버나움": {
        "summary": "갈릴리 호수 북서쪽 연안에 위치한 번화한 무역·상업 도시이자 로마 세관이 있던 성읍. '나훔의 마을' 또는 '위로의 마을'이라는 뜻을 지닙니다.",
        "events": "예수님께서 나사렛을 떠나 공생애 갈릴리 사역의 본부(본 동네)로 삼으신 곳으로, 백부장의 종 치유, 중풍병자 치유, 야이로의 딸 부활 등 수많은 권능을 행하셨습니다 (마 4:13, 마 8:5-17, 막 2:1-12)."
    },
    "사독": {
        "summary": "아히둡의 아들이자 아론의 셋째 아들 엘르아살 계열의 대제사장. 다윗 왕과 솔로몬 왕 통치 때 충직하게 사역하며 사독 제사장 가문의 시조가 되었습니다.",
        "events": "헤브론에서 다윗을 왕으로 추대할 때 22명의 족장들과 함께 합류하였고, 압살롬의 반역 때 언약궤를 지키며 다윗을 끝까지 보좌했습니다. 아도니야의 반역 때 다윗의 명을 따라 솔로몬에게 기름을 부어 왕으로 세웠으며, 솔로몬 성전의 초대 대제사장이 되었습니다 (삼하 8:17, 왕상 1:32-45, 대상 29:22)."
    },
    "아킴": {
        "summary": "바벨론 포로기 이후 신구약 중간기 시대에 살았던 유다 지파의 인물로, 사독의 아들이자 엘리웃의 아버지입니다.",
        "events": "다윗 왕실의 직계 후손으로서 메시아이신 예수 그리스도의 법적 족보를 잇는 중요한 구속사적 연결고리입니다 (마 1:14)."
    },
    "엘리웃": {
        "summary": "신구약 중간기에 살았던 유다 지파의 인물로, 아킴의 아들이자 엘르아살의 아버지입니다. '하나님은 나의 찬송'이라는 뜻을 지닙니다.",
        "events": "다윗의 혈통이자 만왕의 왕 예수 그리스도의 탄생을 준비하는 거룩한 계보에 이름을 올렸습니다 (마 1:14-15)."
    },
    "아소르": {
        "summary": "신구약 중간기 시대 유다 지파의 족장으로, 엘리아김의 아들이자 사독의 아버지입니다. '돕는 자'라는 뜻을 지닙니다.",
        "events": "바벨론 포로 귀환 후 어둠의 시대 속에서도 다윗 왕가의 언약적 계보를 성실히 계승하여 메시아 족보에 기록되었습니다 (마 1:13-14)."
    },
    "아비훗": {
        "summary": "스룹바벨의 아들이자 엘리아김의 아버지로, 바벨론 포로 귀환 후 성전 재건 시대의 유다 지파 지도자입니다. '찬송의 아버지'라는 뜻을 지닙니다.",
        "events": "포로에서 돌아온 언약의 백성들 가운데서 다윗 왕가의 맥을 잇고 예수 그리스도의 족보에 기록되었습니다 (마 1:13)."
    },
    "스룹바벨": {
        "summary": "유다 지파 여호야긴(여고냐) 왕의 손자이자 스알디엘(또는 브다야)의 아들. 바벨론 제1차 포로 귀환(B.C. 537년경)을 이끈 유다 총독이자 다윗 왕실의 후계자입니다.",
        "events": "대제사장 여호수아와 함께 바벨론에서 귀환하여 무너진 예루살렘 성전의 기초를 놓고 방해 속에서도 성전(스룹바벨 성전)을 완공하였습니다. 학개와 스가랴 선지자는 그를 하나님의 '인장(도장)'으로 삼으실 메시아의 모형으로 선포했습니다 (스 3:2, 학 2:23, 슥 4:6-9, 마 1:12-13)."
    },
    "비손": {
        "summary": "에덴동산에서 발원하여 동산을 적시고 흘러나간 네 개의 강 중 첫 번째 강. '풍부하게 흘러넘침' 또는 '해산의 고통'이라는 뜻을 지닙니다.",
        "events": "금이 풍부하고 베델리엄(진주/호마노)과 보석이 있는 하윌라 온 땅을 둘렀던 낙원의 생명수 강입니다 (창 2:11-12)."
    },
    "기혼": {
        "summary": "에덴동산의 네 강 중 두 번째 강이자, 예루살렘 동쪽 기드론 골짜기에 솟아나는 유일한 천연 샘의 이름입니다.",
        "events": "구스 온 땅을 둘렀으며, 다윗 성 아래 기혼 샘은 솔로몬이 왕으로 기름 부음 받은 성스러운 장소이자 히스기야 터널의 수원지입니다 (창 2:13, 왕상 1:33-38, 대하 32:30)."
    },
    "힛데겔": {
        "summary": "에덴동산의 네 강 중 세 번째 강으로, 현재의 티그리스(Tigris) 강을 가리킵니다. '화살처럼 빠르게 흐르는 강'을 뜻합니다.",
        "events": "앗수르 동편으로 흘렀으며, 훗날 다니엘 선지자가 강가에서 거룩한 이상과 천사의 계시를 받았습니다 (창 2:14, 단 10:4)."
    },
    "유브라데": {
        "summary": "에덴동산의 네 강 중 네 번째 강이자 서아시아 최대의 젖줄(현재의 유프라테스 강). 성경에서 종종 단순히 '그 큰 강' 또는 '하수'로 불립니다.",
        "events": "하나님께서 아브라함에게 주신 약속의 땅 북동쪽 경계선(창 15:18)이며, 고대 메소포타미아 문명과 바벨론 제국의 중심 하천입니다 (창 2:14, 수 1:4, 계 9:14)."
    },
    "라멕": {
        "summary": "(1) 가인의 5대손으로 두 아내(아다, 씰라)를 얻어 인류 최초로 일부다처제를 시작한 포악한 사람. (2) 셋 계열의 의인으로 므두셀라의 아들이자 노아의 아버지.",
        "events": "가인 계열 라멕은 상처로 인해 소년을 죽이고 살인을 자랑하는 '칼의 노래'를 불렀으며(창 4:19-24), 셋 계열 라멕은 아들 노아를 낳으며 '여호와께서 땅을 저주하심으로 수고롭게 일하는 우리를 이 아들이 안위하리라'고 예언했습니다 (창 5:28-29)."
    },
    "두발가인": {
        "summary": "가인 계열 라멕과 씰라의 아들로, 인류 역사상 최초의 금속 기술자이자 대장장이의 조상.",
        "events": "구리와 쇠로 여러 가지 날카로운 기구와 무기를 만들어 고대 인류 문명과 무기 기술의 발전을 이끌었습니다 (창 4:22)."
    },
    "야발": {
        "summary": "라멕과 아다의 아들로, 장막에 거주하며 가축을 치는 유목민의 조상.",
        "events": "가축 사육과 장막 생활 문화를 개척한 인물입니다 (창 4:20)."
    },
    "유발": {
        "summary": "라멕과 아다의 아들로, 수금과 퉁소를 잡는 모든 악기 연주자와 음악가의 조상.",
        "events": "인류 최초로 현악기와 관악기를 고안하여 예술과 음악 문화를 시작했습니다 (창 4:21)."
    }
}

# Update rich dedicated profiles
for name, prof in rich_place_profiles.items():
    cur.execute("""
        UPDATE bible_dictionary
        SET summary = ?, events = ?
        WHERE name_ko = ?;
    """, (prof["summary"], prof["events"], name))

# Clean up any remaining English sentences in all entries
cur.execute("SELECT id, name_ko, summary, events FROM bible_dictionary;")
all_rows = cur.fetchall()

def remove_english_artifacts(text):
    if not text: return ""
    txt = text
    # Remove raw english phrases
    txt = re.sub(r'[A-Za-z]+_[0-9]+', '', txt)
    txt = re.sub(r'\[[A-Za-z0-9_]+\]', '', txt)
    txt = re.sub(r'\b(the|and|of|in|to|from|at|with|by|as|who|that|which|was|is|were|are|had|has|have|been|it|its|his|her|their)\b', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\b(city|town|land|mountain|river|plain|valley|house|shore|sea|lake|first|second|third|fourth|fifth)\b', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'[A-Za-z]{2,}', '', txt) # remove remaining english words
    txt = re.sub(r'\s+', ' ', txt)
    txt = re.sub(r'[,;]\s*[,;]', ',', txt)
    txt = txt.replace(' ,', ',').replace(' .', '.').replace('()', '').replace('( )', '').strip(' ,;')
    return txt

clean_count = 0
for r in all_rows:
    s = r["summary"] or ""
    e = r["events"] or ""
    # If English letters exist
    if re.search(r'[A-Za-z]', s) or re.search(r'[A-Za-z]', e):
        cs = remove_english_artifacts(s)
        ce = remove_english_artifacts(e)
        cur.execute("UPDATE bible_dictionary SET summary = ?, events = ? WHERE id = ?;", (cs, ce, r["id"]))
        clean_count += 1

conn.commit()
print(f"Cleaned {clean_count} entries to ensure 100% pure Korean text!")

# Check sample entries
print("\nVerified sample profiles:")
for test_name in ['베들레헴', '헤브론', '갈릴리', '가버나움', '사독', '아킴', '엘리웃', '아소르', '아비훗', '스룹바벨', '비손', '기혼', '라멕', '두발가인', '유발', '야발']:
    cur.execute("SELECT name_ko, category, meaning, summary, events FROM bible_dictionary WHERE name_ko = ?;", (test_name,))
    row = cur.fetchone()
    if row:
        print(f"[{row['category']}] {row['name_ko']} (뜻: {row['meaning']})")
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
