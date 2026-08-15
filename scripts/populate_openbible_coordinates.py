import sqlite3
import urllib.request
import json
import gzip
import shutil
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

print("1. Fetching OpenBible.info complete biblical geocoding dataset...")
openbible_url = 'https://raw.githubusercontent.com/openbibleinfo/Bible-Geocoding-Data/main/data/ancient.jsonl'

openbible_places = [] # list of { id, name, lat, lon, verses, desc }

try:
    req = urllib.request.Request(openbible_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as response:
        for line in response:
            item = json.loads(line.decode('utf-8'))
            f_id = item.get('friendly_id')
            lonlat = None
            ident_desc = ""
            for ident in item.get('identifications', []):
                ident_desc = ident.get('description', '')
                for res in ident.get('resolutions', []):
                    if res.get('lonlat'):
                        lonlat = res.get('lonlat')
                        break
                if lonlat:
                    break
            
            if f_id and lonlat:
                lon_s, lat_s = lonlat.split(',')
                # clean description
                clean_desc = re.sub(r'<[^>]+>', '', ident_desc).strip()
                openbible_places.append({
                    "name": f_id,
                    "lat": float(lat_s),
                    "lon": float(lon_s),
                    "desc": clean_desc,
                    "verses": [v.get('readable', '') for v in item.get('verses', [])]
                })
    print(f"Loaded {len(openbible_places)} historical places with exact GPS coordinates from OpenBible.info.")
except Exception as e:
    print(f"Error fetching OpenBible: {e}")

# Exact historical coordinate mapping for biblical sites
primary_biblical_sites = {
    "예루살렘": (31.7767, 35.2345, "예루살렘 성전산 및 다윗성 고대 유적 (Old City of Jerusalem)"),
    "시온": (31.7719, 35.2286, "시온산 및 다윗성 요새 (Mount Zion)"),
    "다윗성": (31.7733, 35.2361, "다윗 왕국의 고대 성읍 발굴지 (City of David)"),
    "베들레헴": (31.7043, 35.2075, "예수 탄생 기념 성당 및 다윗의 고향 (Bethlehem)"),
    "갈릴리": (32.8222, 35.5861, "갈릴리 호수 / 디베랴 바다 (Sea of Galilee)"),
    "나사렛": (32.7022, 35.2978, "예수님의 고향 나사렛 (Nazareth)"),
    "가버나움": (32.8805, 35.5750, "예수님의 사역 중심지 고대 회당 유적 (Capernaum - Kfar Nahum)"),
    "요단강": (31.8383, 35.5478, "예수님 세례 터 - 카스르 엘 야후드 (Qasr al-Yahud / Jordan River)"),
    "요단": (31.8383, 35.5478, "요단강 성지 (Jordan River)"),
    "여리고": (31.8708, 35.4439, "고대 여리고 텔 에스술탄 성벽 유적 (Tell es-Sultan / Ancient Jericho)"),
    "시내산": (28.5397, 33.9750, "모세가 십계명을 받은 성산 (Mount Sinai / Jebel Musa)"),
    "호렙산": (28.5397, 33.9750, "호렙산 / 시내산 성지 (Mount Horeb)"),
    "헤브론": (31.5247, 35.1108, "아브라함·사라·이삭·야곱의 막벨라 굴 성지 (Cave of Machpelah / Hebron)"),
    "벧엘": (31.9286, 35.2403, "야곱의 사닥다리 꿈과 하나님의 집 유적 (Beitin / Ancient Bethel)"),
    "세겜": (32.2139, 35.2819, "야곱의 우물 및 아브라함 최초 제단 터 (Tell Balata / Ancient Shechem)"),
    "사마리아": (32.2778, 35.1906, "북이스라엘 왕국의 수도 사마리아 세바스티야 유적 (Sebastia / Samaria)"),
    "소돔": (31.0667, 35.3833, "사해 남부 소돔 산 및 고대 도시 터 (Mount Sodom / Bab edh-Dhra)"),
    "고모라": (31.2000, 35.4000, "사해 동남부 고모라 추정 발굴지 (Numeira)"),
    "브엘세바": (31.2447, 34.8408, "아브라함의 맹세의 우물 텔 브엘세바 유적 (Tel Be'er Sheva)"),
    "모리아산": (31.7780, 35.2353, "이삭을 바친 모리아 산 / 성전산 바위 (Mount Moriah / Temple Mount)"),
    "모리아": (31.7780, 35.2353, "모리아 산 (Mount Moriah)"),
    "겟세마네": (31.7794, 35.2397, "예수님의 눈물의 기도 동산 (Garden of Gethsemane)"),
    "골고다": (31.7785, 35.2297, "예수 그리스도 십자가 처형 터 - 성묘 (Golgotha / Holy Sepulchre)"),
    "갈보리": (31.7785, 35.2297, "골고다 언덕 / 갈보리 (Calvary)"),
    "감람산": (31.7781, 35.2447, "예수님 승천 터 및 감람산 전망대 (Mount of Olives)"),
    "베다니": (31.7708, 35.2608, "나사로와 마르다의 집 및 나사로 무덤 (Bethany - Al-Eizariya)"),
    "벳바게": (31.7739, 35.2503, "나귀를 타신 벳바게 기념 성당 (Bethphage)"),
    "엠마오": (31.8389, 34.9892, "부활하신 예수님이 제자들에게 나타나신 엠마오 (Emmaus Nicopolis)"),
    "가나": (32.7483, 35.3375, "물로 포도주를 만드신 가나 혼인잔치 기념 교회 (Kafr Kanna)"),
    "벳새다": (32.9100, 35.6300, "베드로·안드레·빌립의 고향 벳새다 유적 (Et-Tell / Bethsaida)"),
    "디베랴": (32.7944, 35.5311, "갈릴리 서안 디베랴 (Tiberias)"),
    "거라사": (32.2797, 35.8925, "귀신 들린 자를 고치신 거라사 고대 도시 (Jerash / Gerasa)"),
    "막달라": (32.8228, 35.5186, "막달라 마리아의 고향 고대 1세기 회당 발굴지 (Magdala - Migdal)"),
    "가이사랴": (32.5008, 34.8925, "헤롯 대왕의 해변 항구도시 가이사랴 마리티마 유적 (Caesarea Maritima)"),
    "욥바": (32.0536, 34.7553, "요나의 출항지 및 베드로 환상 터 시몬의 집 (Old Jaffa - Joppa)"),
    "길갈": (31.8667, 35.4833, "요단강 도하 후 첫 진영 12개 돌 기념비 터 (Gilgal)"),
    "실로": (32.0556, 35.2897, "광야 성막과 언약궤가 300년간 머문 고대 실로 유적 (Tel Shiloh)"),
    "아이": (31.9167, 35.2667, "여호수아가 정복한 고대 아이 성 터 (Et-Tell / Ai)"),
    "기브온": (31.8483, 35.1883, "태양이 멈춘 기브온 고대 웅덩이 유적 (El-Jib / Gibeon)"),
    "벧세메스": (31.7456, 34.9878, "언약궤가 돌아온 벧세메스 유적 (Tel Beth Shemesh)"),
    "기럇여아림": (31.8039, 35.1097, "언약궤가 아비나답의 집에 20년간 머문 기럇여아림 (Kiryat Ye'arim)"),
    "갈멜산": (32.7350, 35.0450, "엘리야가 바알 선지자 450명과 대결한 엘 무흐라카 (Mount Carmel - Muhraqa)"),
    "길보아산": (32.5000, 35.4167, "사울 왕과 요나단이 전사한 길보아 산 (Mount Gilboa)"),
    "다메섹": (33.5138, 36.2765, "바울이 회심한 다메섹 직가 거리 성지 (Straight Street, Damascus)"),
    "두로": (33.2708, 35.2039, "지중해 페니키아 고대 무역항 두로 유적 (Tyre - Sour)"),
    "시돈": (33.5631, 35.3689, "고대 해안 도시 시돈 성지 (Sidon - Saida)"),
    "가나안": (31.7683, 35.2137, "약속의 땅 가나안 (Land of Canaan)"),
    "안디옥": (36.2021, 36.1606, "이방 선교의 출발지이자 성 베드로 동굴 교회 (Antioch / Antakya)"),
    "다소": (36.9167, 34.8958, "사도 바울의 고향 다소 (Tarsus)"),
    "구브로": (35.1264, 33.4299, "바나바의 고향 구브로 섬 (Cyprus)"),
    "버가": (36.9608, 30.8528, "바울의 1차 전도여행지 버가 고대 유적 (Perga)"),
    "이고니온": (37.8714, 32.4847, "바울이 복음을 전한 이고니온 (Konya / Iconium)"),
    "루스드라": (37.5833, 32.2167, "디모데의 고향 루스드라 텔 유적 (Lystra)"),
    "더베": (37.3500, 33.3667, "바울이 전도하여 많은 제자를 삼은 더베 (Derbe)"),
    "드로아": (39.7564, 26.1558, "마게도냐인의 환상을 본 알렉산드리아 드로아 유적 (Alexandria Troas)"),
    "빌립보": (41.0131, 24.2847, "유럽 최초의 교회이자 바울과 실라의 감옥 터 (Ancient Philippi)"),
    "데살로니가": (40.6401, 22.9444, "바울이 세운 데살로니가 교회 터 (Thessaloniki)"),
    "베뢰아": (40.5239, 22.2039, "말씀을 간절히 상고한 베뢰아 바울의 연단 터 (Veria / Berea)"),
    "아덴": (37.9715, 23.7257, "바울이 아레오바고에서 설교한 아테네 아크로폴리스 (Areopagus / Athens)"),
    "고린도": (37.9067, 22.8800, "바울이 1년 6개월간 머문 고대 고린도 유적 및 갈리오 법정 터 (Ancient Corinth - Bema)"),
    "겐그레아": (37.8833, 22.9833, "바울이 서원하여 머리를 깎은 겐그레아 항구 (Kenchreai)"),
    "에베소": (37.9400, 27.3414, "두란노 서원과 셀수스 도서관이 있는 에베소 고대 유적 (Ancient Ephesus)"),
    "밀레도": (37.5306, 27.2767, "에베소 장로들과 눈물로 고별한 밀레도 고대 극장 유적 (Miletus)"),
    "골로새": (37.7869, 29.2567, "골로새 교회 터 텔 유적 (Colossae - Honaz)"),
    "라오디게아": (37.8358, 29.1081, "차지도 덥지도 않은 교회 라오디게아 고대 도시 유적 (Laodicea)"),
    "서머나": (38.4192, 27.1287, "폴리카프 순교지 서머나 아고라 유적 (Smyrna - Izmir)"),
    "버가모": (39.1325, 27.1842, "사탄의 위가 있는 버가모 아크로폴리스 유적 (Pergamon)"),
    "두아디라": (38.9228, 27.8406, "루디아의 고향 두아디라 고대 유적 (Thyatira - Akhisar)"),
    "사데": (38.4875, 28.0403, "금과 부의 도시 사데 아르테미스 신전 및 회당 유적 (Sardis)"),
    "빌라델비아": (38.3517, 28.5175, "칭찬받은 빌라델비아 성 요한 바실리카 유적 (Philadelphia - Alasehir)"),
    "로마": (41.8902, 12.4922, "바울과 베드로의 순교지 로마 콜로세움 및 맘메르틴 감옥 (Ancient Rome)"),
    "밧모섬": (37.3167, 26.5500, "사도 요한이 요한계시록을 기록한 요한 계시 동굴 (Cave of the Apocalypse, Patmos)"),
    "우르": (30.9628, 46.1031, "아브라함의 고향 갈대아 우르 지구라트 유적 (Ziggurat of Ur / Tell el-Muqayyar)"),
    "하란": (36.8644, 39.0253, "데라가 머물고 야곱이 라반의 집에 거한 고대 하란 유적 (Ancient Harran)"),
    "아라랏산": (39.7022, 44.2989, "노아의 방주가 머문 아라랏 산 정상 (Mount Ararat)"),
    "바벨론": (32.5422, 44.4211, "고대 바벨론 이슈타르 문 및 공중정원 터 (Ancient Babylon)"),
    "수산궁": (32.1894, 48.2436, "에스더와 다니엘의 배경 페르시아 수산궁 아파다나 유적 (Apadana of Susa)"),
    "니느웨": (36.3589, 43.1528, "요나가 회개를 외친 앗수르 수도 고대 니느웨 유적 (Nineveh - Mosul)"),
    "애굽": (29.9792, 31.1342, "요셉과 모세의 배경 고대 이집트 멤피스/기자 유적 (Ancient Egypt)"),
    "고센": (30.7878, 31.8344, "야곱 일가가 정착한 나일강 삼각주 고센 땅 (Land of Goshen - Tell el-Dab'a)"),
    "홍해": (27.5000, 34.0000, "이스라엘 백성이 건넌 홍해 (Red Sea - Gulf of Suez)"),
    "마라": (29.5833, 32.7833, "쓴 물이 단 물로 변한 마라의 샘 (Ain Hawara / Marah)"),
    "엘림": (29.3000, 33.0000, "물샘 12과 종려나무 70그루가 있던 엘림 (Wadi Gharandel / Elim)"),
    "르비딤": (28.6000, 33.7000, "모세가 반석을 쳐서 물을 낸 므리바 르비딤 (Wadi Feiran / Rephidim)"),
    "가데스바네아": (30.6500, 34.4167, "12정탐꾼을 보낸 가데스 바네아 오아시스 (Ain el-Qudeirat / Kadesh Barnea)"),
    "에돔": (30.3285, 35.4444, "에서의 후손들의 붉은 바위 요새 페트라 성지 (Petra / Edom)"),
    "모압": (31.4000, 35.8000, "룻의 고향 아르논 골짜기 모압 평지 (Moab Plateau)"),
    "암몬": (31.9500, 35.9333, "랍바 암몬 요새 고대 성채 (Amman Citadel / Rabbah Ammon)"),
    "바산": (32.8000, 36.0000, "옥의 땅 비옥한 골란고원 바산 평야 (Bashan Plain)")
}

print("2. Updating database with exact historical archaeological GPS coordinates...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Update primary sites
updated_count = 0
for name, (lat, lng, desc) in primary_biblical_sites.items():
    cur.execute("""
        UPDATE bible_dictionary
        SET latitude = ?, longitude = ?
        WHERE name_ko = ? AND category = '지명';
    """, (lat, lng, name))
    if cur.rowcount > 0:
        updated_count += cur.rowcount

print(f"Updated {updated_count} primary biblical sites with exact historical coordinates.")

# Match other place entries from OpenBible by English name
cur.execute("SELECT id, name_ko, name_en, key_verses FROM bible_dictionary WHERE category = '지명' AND (latitude IS NULL OR latitude = 0);")
unmatched_places = cur.fetchall()

openbible_map = {p["name"].lower(): (p["lat"], p["lon"]) for p in openbible_places}

ob_updated = 0
for r in unmatched_places:
    name_en = (r["name_en"] or "").lower().strip()
    if name_en and name_en in openbible_map:
        lat, lon = openbible_map[name_en]
        cur.execute("UPDATE bible_dictionary SET latitude = ?, longitude = ? WHERE id = ?;", (lat, lon, r["id"]))
        ob_updated += 1

conn.commit()
print(f"Matched {ob_updated} additional places from OpenBible.info database.")

# Count total places with coordinates
cur.execute("SELECT count(*) FROM bible_dictionary WHERE category = '지명' AND latitude IS NOT NULL AND latitude != 0;")
total_geo = cur.fetchone()[0]
print(f"Total biblical places with precise GPS coordinates: {total_geo}")

# 3. Compress database to bible.db.gz
print("\n3. Compressing database to server/data/bible.db.gz...")
with open(DB_PATH, 'rb') as f_in:
    with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)

gz_size = os.path.getsize(DB_GZ_PATH) / (1024 * 1024)
print(f"Compressed bible.db.gz: {gz_size:.2f} MB")
