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

# Explicit known Places & Nations in the Korean Bible
explicit_places = {
    # 주요 고대 국가 및 민족 영토
    "블레셋": {
        "name_en": "Philistia",
        "meaning": "이주자들의 땅, 방랑",
        "summary": "가나안 남서부 지중해 연안 평야 지대에 위치했던 호전적이고 강력한 해양 민족의 땅. 가사, 아스돗, 아스글론, 에그론, 가드의 5대 주요 도시 연맹체(블레셋 5대 방백)로 구성되었습니다.",
        "events": "철기 문화를 바탕으로 사사 시대부터 사울 왕과 다윗 왕 시대에 이르기까지 이스라엘을 끊임없이 침략하고 위협했던 가장 강력한 숙적이었습니다. 삼손, 골리앗과의 전투, 법궤(언약궤)를 빼앗아 다곤 신전에 둔 사건의 무대입니다 (삿 13-16장, 삼상 4-6장, 삼상 17장)."
    },
    "애굽": {
        "name_en": "Egypt",
        "meaning": "검은 땅, 프타 신의 신전",
        "summary": "나일강 유역에 형성된 아프리카 동북부의 세계적인 고대 문명 대제국 (성경의 미스라임). 성경 전체를 관통하는 구속사의 거대한 무대입니다.",
        "events": "아브라함과 야곱 가문의 기근 피난처, 요셉의 국무총리 치리, 430년간의 이스라엘 민족 형성 및 노예 생활, 모세를 통한 출애굽 10대 재앙 구원, 솔로몬의 무역, 아기 예수님의 헤롯 박해 피난처(마 2:13-15)의 배경입니다."
    },
    "가나안": {
        "name_en": "Canaan",
        "meaning": "낮은 땅, 자줏빛 땅",
        "summary": "지중해와 요단강 사이에 위치한 약속의 땅(현재의 팔레스타인/이스라엘 지역). 하나님께서 아브라함과 그의 후손에게 영원한 기업으로 주시겠다고 맹세하신 '젖과 꿀이 흐르는 땅'입니다.",
        "events": "아브라함의 부르심과 족장들의 거주지, 여호수아의 정복 전쟁과 열두 지파의 기업 분배, 사사 시대와 통일 왕국 이스라엘의 역사적 중심 무대입니다 (창 12:1-7, 수 1-24장)."
    },
    "모압": {
        "name_en": "Moab",
        "meaning": "아버지로부터, 아버지의 소생",
        "summary": "사해 동쪽 고원 지대(아르논강 남쪽)에 위치했던 롯의 큰딸의 후손들이 세운 왕국. 수도는 길하레셋(디본)이었습니다.",
        "events": "출애굽 이스라엘의 통과를 거절하고 발람을 고용해 저주하려 함(민 22장), 룻의 고향이자 다윗 왕실의 외가 혈통(룻 4:18-22), 남유다와 북이스라엘과의 잦은 전쟁 무대입니다."
    },
    "암몬": {
        "name_en": "Ammon",
        "meaning": "내 백성의 아들",
        "summary": "요단강 동편 얍복강과 아르논강 사이 고원 지대에 위치했던 롯의 작은딸의 후손들이 세운 왕국. 수도는 랍바(현재 요르단의 수도 암만).",
        "events": "몰렉(밀곰) 우상을 숭배하며 이스라엘을 자주 대적함(삿 11장), 다윗이 랍바 성을 정복하고 밧세바의 남편 우리아를 전사시킨 전쟁터(삼하 11-12장)."
    },
    "에돔": {
        "name_en": "Edom / Idumea",
        "meaning": "붉음 (Red), 세일산",
        "summary": "사해 남쪽 세일산 산악 지대에 위치했던 에서(야곱의 쌍둥이 형)의 후손들이 세운 험준한 바위 왕국. 신약 시대에는 '이두매'로 불렸습니다.",
        "events": "출애굽 이스라엘의 '왕의 대로' 통과를 완강히 거절함(민 20장), 예루살렘 멸망 때 바벨론 편에 서서 조롱하고 약탈하여 오바댜 선지자의 준엄한 심판 예언을 받음(옵 1장), 헤롯 대왕 가문의 출신지."
    },
    "앗수르": {
        "name_en": "Assyria",
        "meaning": "아수르 신의 땅, 평원",
        "summary": "메소포타미아 북부 티그리스강 상류에 위치했던 고대 근동 최강의 잔혹한 군사 제국. 수도는 니느웨, 갈라, 아술 등이었습니다.",
        "events": "요나 선지자의 회개 선포(욘 3장), B.C. 722년 사르곤 2세에 의해 북이스라엘 사마리아를 멸망시킴(왕하 17장), 히스기야 왕 때 산헤립이 예루살렘을 포위했으나 여호와의 사자가 18만 5천 군사를 전멸시킴(왕하 19장)."
    },
    "바벨론": {
        "name_en": "Babylon / Babylonia",
        "meaning": "신의 문, 혼잡 (Babel)",
        "summary": "메소포타미아 남부 유브라데강 하류의 비옥한 평원에 위치했던 세계적인 대제국 (성경의 시날 땅). 인류 교만의 상징인 바벨탑의 땅입니다.",
        "events": "느부갓네살 왕 때 B.C. 586년 예루살렘 성전과 도성을 파괴하고 유다 백성을 포로로 끌고 감(바벨론 70년 포로기), 다니엘과 세 친구의 믿음의 승리(단 1-6장), 요한계시록에서 하나님을 대적하는 세속 음녀 도시의 영적 상징(계 17-18장)."
    },
    "아람": {
        "name_en": "Aram / Syria",
        "meaning": "높은 땅, 고원",
        "summary": "이스라엘 북동쪽 시리아 평원과 레바논 산맥에 위치했던 셈족 계열의 고대 왕국. 중심 도시는 다메섹(다마스쿠스)이었습니다.",
        "events": "다윗 왕에게 정복되어 조공을 바쳤으나, 분열 왕국 시대 벤하닷과 하사엘 왕 때 북이스라엘을 맹렬히 침략함, 나아만 장군의 문둥병 치유(왕하 5장), 엘리사를 잡으려던 도단 성 포위 사건의 배경."
    },
    "두로": {
        "name_en": "Tyre",
        "meaning": "바위, 해상 무역의 수도",
        "summary": "지중해 연안 북부 페니키아(베니게)의 세계적인 해상 무역 항구 도시. 섬과 육지의 천연 요새로 막대한 부를 누렸습니다.",
        "events": "히람 왕이 다윗과 솔로몬에게 성전 건축용 백향목과 석수를 공급함(왕상 5장), 에스겔 선지자의 교만에 대한 준엄한 애가와 심판 예언(겔 27-28장), 예수님께서 두로와 시돈 지방을 방문하시어 가나안 여인의 딸을 고치심(마 15:21-28)."
    },
    "시돈": {
        "name_en": "Sidon",
        "meaning": "어업, 어항",
        "summary": "두로 북쪽 약 40km에 위치한 페니키아에서 가장 유서 깊은 고대 해상 무역 항구 성읍.",
        "events": "아합 왕의 악명 높은 아내 이세벨의 친정(시돈 왕 엣바알의 딸, 왕상 16:31), 엘리야 선지자를 공궤한 사렙다(사르밧) 과부의 고향 인근(왕상 17:9)."
    },
    "다메섹": {
        "name_en": "Damascus",
        "meaning": "활동적인 땅, 수리아의 수도",
        "summary": "세계에서 가장 오래된 연속 주거 도시 중 하나로, 수리아(아람)의 번영한 수도이자 교통과 무역의 요충지.",
        "events": "사울(바울)이 기독교인을 체포하러 가다가 다메섹 도상에서 부활하신 예수님의 강력한 빛과 음성을 만나 극적으로 회심한 거룩한 성지(행 9:1-19), 직가(Straight Street) 거리의 아나니아 만남."
    },
    "사마리아": {
        "name_en": "Samaria",
        "meaning": "파수대, 지키는 산",
        "summary": "북이스라엘 오므리 왕이 세멜에게서 은 두 달란트로 사서 건설한 북왕국의 영구한 수도이자, 신약 시대 유대와 갈릴리 사이에 위치한 중앙 지방.",
        "events": "B.C. 722년 앗수르에 함락된 후 이방 민족과의 혼혈로 유대인들에게 멸시받았으나, 예수님께서 수가성 우물가 여인에게 생명수를 주시고(요 4장), 빌립 집사가 최초로 복음을 전파하여 큰 기쁨이 넘친 땅(행 8장)."
    },
    "안디옥": {
        "name_en": "Antioch",
        "meaning": "안티오쿠스의 도시, 이방 선교의 본부",
        "summary": "수리아 오론테스강 유역에 위치한 로마 제국 제3의 대도시이자, 초대 교회의 세계 이방인 선교의 모교회(본부)가 세워진 곳.",
        "events": "스데반의 일로 흩어진 성도들이 세운 교회로, 바나바와 사울(바울)이 동역하며 제자들이 비로소 '그리스도인(Christian)'이라 불리게 된 영광스러운 성지이자, 바울의 1·2·3차 전도여행의 파송 본부입니다 (행 11:19-26, 행 13:1-3)."
    },
    "에베소": {
        "name_en": "Ephesus",
        "meaning": "열망, 바람직함",
        "summary": "소아시아 서부 지중해 연안의 최고 무역·정치·문화 중심 항구 도시. 세계 7대 불가사의인 아데미 신전이 있던 번화한 대도시.",
        "events": "바울이 3차 전도여행 중 두란노 서원에서 2년 이상 날마다 성경을 강론하며 소아시아 전체에 복음을 전파한 곳(행 19장), 에베소서의 수신지이자 요한계시록 아시아 일곱 교회의 첫 번째 첫사랑의 교회(계 2:1-7)."
    },
    "빌립보": {
        "name_en": "Philippi",
        "meaning": "말을 사랑하는 자의 도시, 마게도냐의 첫 성",
        "summary": "마게도냐 지방의 로마 직할 식민지 도시이자 유럽 대륙 복음화의 첫 관문 성읍.",
        "events": "바울이 환상을 보고 건너가 자주장사 루디아의 집에서 유럽 최초의 교회를 세움, 바울과 실라가 감옥에서 찬송할 때 옥터가 흔들리고 간수와 온 가족이 구원받은 기적의 현장 (행 16:11-40, 빌립보서)."
    },
    "고린도": {
        "name_en": "Corinth",
        "meaning": "장식, 번영의 항구 도시",
        "summary": "펠로폰네소스반도와 그리스 본토를 잇는 좁은 지협에 위치한 무역과 상업의 대도시이자 아가야 지방의 수도. 아프로디테 신전 등 음란과 우상숭배가 만연했던 성읍.",
        "events": "바울이 2차 전도여행 때 1년 6개월간 머물며 브리스길라와 아굴라와 함께 장막을 만들며 개척한 교회 (행 18:1-18, 고린도전·후서)."
    },
    "로마": {
        "name_en": "Rome",
        "meaning": "힘, 강함, 로마 제국의 수도",
        "summary": "지중해 온 세계를 정복하고 지배했던 로마 제국의 거대한 수도.",
        "events": "바울이 죄수의 몸으로 호송되어 셋집에서 담대히 하나님 나라를 전파함(행 28장), 로마서의 수신지이자 바울과 베드로가 순교한 초대 교회의 중심지."
    },
    "소돔": {
        "name_en": "Sodom",
        "meaning": "불타는 곳, 멸망의 성읍",
        "summary": "사해 남부 싯딤 골짜기의 비옥하고 풍요로웠으나 성적 타락과 죄악이 극에 달했던 가나안 성읍.",
        "events": "롯이 눈을 들어 택한 땅이었으나, 하늘에서 유황과 불이 비같이 내려 철저히 멸망하여 영원한 심판의 경고 표본이 되었습니다 (창 13:10-13, 창 19:24-28, 벧후 2:6)."
    },
    "고모라": {
        "name_en": "Gomorrah",
        "meaning": "물에 잠김, 침몰",
        "summary": "소돔과 함께 사해 남단에 위치했던 타락한 쌍둥이 성읍으로, 소돔과 함께 유황불 심판으로 멸망했습니다 (창 19장).",
        "events": "소돔과 함께 하나님의 준엄한 심판으로 영원히 소멸된 교훈의 성읍 (창 19:24-28, 유 1:7)."
    },
    "시내산": {
        "name_en": "Mount Sinai / Horeb",
        "meaning": "가시나무 숲, 하나님의 산",
        "summary": "시나이반도 남부 화강암 바위산 (해발 2,285m, 현재의 제벨 무사). 호렙산으로도 불립니다.",
        "events": "모세가 불타는 떨기나무에서 소명을 받은 산이자(출 3장), 출애굽 이스라엘 백성이 십계명과 성막 율법을 받고 하나님과 피의 언약을 맺은 구속사의 성산(출 19-24장), 엘리야가 세미한 음성을 들은 산(왕상 19장)."
    },
    "갈멜산": {
        "name_en": "Mount Carmel",
        "meaning": "하나님의 포도원, 기름진 과원",
        "summary": "지중해에서 남동쪽으로 뻗은 약 24km 길이의 비옥하고 아름다운 산맥.",
        "events": "엘리야 선지자가 바알과 아세라 선지자 850명과 대결하여 하늘에서 여호와의 불이 내려와 번제물을 사르고 참 하나님을 증명한 위대한 영적 승리의 성산 (왕상 18:19-40)."
    },
    "감람산": {
        "name_en": "Mount of Olives",
        "meaning": "올리브 기름의 산",
        "summary": "예루살렘 성전 동쪽 기드론 골짜기 건너편에 위치한 해발 약 818m의 올리브나무 산.",
        "events": "다윗이 압살롬을 피해 눈물로 넘은 산(삼하 15:30), 예수님께서 예루살렘을 보시며 눈물 흘리시고 종말의 징조를 예언하신 산(마 24장), 겟세마네 동산에서 땀이 핏방울 되도록 기도하신 산(눅 22:39-44), 부활 후 하늘로 승천하시고 다시 오실 산(행 1:9-12, 슥 14:4)."
    },
    "요단강": {
        "name_en": "Jordan River",
        "meaning": "내려오는 자, 단에서 흘러내림",
        "summary": "헬몬산(헤르몬산) 만년설에서 발원하여 갈릴리 호수를 거쳐 사해로 흘러 들어가는 이스라엘의 최대 젖줄 강 (길이 약 250km).",
        "events": "여호수아와 이스라엘 백성이 언약궤를 앞세우고 마른 땅처럼 건넌 강(수 3장), 엘리야와 엘리사가 겉옷으로 물을 가르고 건넌 강(왕하 2장), 나아만 장군이 일곱 번 몸을 씻어 문둥병을 고침받은 강(왕하 5장), 예수 그리스도께서 세례 요한에게 세례를 받으신 거룩한 강(마 3:13-17)."
    },
    "유브라데": {
        "name_en": "Euphrates",
        "meaning": "좋고 단 물, 큰 강",
        "summary": "터키 동부 아르메니아 고원에서 발원하여 페르시아만으로 흐르는 서아시아 최대의 젖줄 강 (길이 약 2,780km). 성경에서 종종 단순히 '그 큰 강' 또는 '하수'로 불립니다.",
        "events": "에덴동산의 네 번째 강(창 2:14), 하나님께서 아브라함에게 약속하신 기업의 북동쪽 경계선(창 15:18, 수 1:4), 바벨론 제국의 중심 하천."
    },
    "홍해": {
        "name_en": "Red Sea",
        "meaning": "갈대 바다 (Yam Suph)",
        "summary": "아프리카와 아라비아반도 사이에 위치한 바다로, 북쪽으로 수에즈만과 아카바만으로 갈라집니다.",
        "events": "모세가 지팡이를 내밀자 하나님께서 밤새 동풍으로 바다를 가르사 이스라엘 백성은 마른 땅으로 건너고, 뒤쫓던 바로의 애굽 정예 병거 군대는 수장된 출애굽 최대의 구원 기적의 바다 (출 14장, 고전 10:1-2 세례의 모형)."
    },
    "사해": {
        "name_en": "Dead Sea / Salt Sea",
        "meaning": "염해, 아라바 바다",
        "summary": "지구상에서 가장 낮은 곳(해수면 아래 약 430m)에 위치한 염분 농도 약 30%가 넘는 내해 (길이 약 80km, 너비 약 16km). 생물이 살 수 없어 '죽은 바다(사해)'라 불립니다.",
        "events": "소돔과 고모라가 유황불로 멸망한 싯딤 골짜기 자리(창 14:3), 에스겔 성전 환상에서 성전 문지방에서 흘러나온 생수가 사해를 적셔 모든 물고기가 살아나고 어부들이 서는 회복의 예언 (겔 47:8-10)."
    }
}

# Step 1: Update explicit place definitions
print("1. Updating explicit Biblical places and nations...")
for name_ko, pdata in explicit_places.items():
    cur.execute("""
        UPDATE bible_dictionary
        SET category = '지명',
            name_en = COALESCE(NULLIF(name_en, ''), ?),
            meaning = ?,
            summary = ?,
            events = ?
        WHERE name_ko = ?;
    """, (pdata["name_en"], pdata["meaning"], pdata["summary"], pdata.get("events", ""), name_ko))

# Step 2: Auto-detect places miscategorized as '인명'
print("2. Scanning all entries for place/geographical attributes...")
cur.execute("SELECT id, name_ko, name_en, category, meaning, summary, events FROM bible_dictionary;")
all_entries = cur.fetchall()

reclassified_to_place = 0
reclassified_to_term = 0

term_words = {
    '달란트', '세겔', '므나', '베가', '게라', '데나리온', '드라크마', '앗사리온', '렙돈', '고드란트', '다릭',
    '규빗', '뼘', '손바닥 넓이', '손너비', '갈대', '스다디온', '스타디온', '하룻길', '사흗길', '안식일 길',
    '에바', '호멜', '고르', '스아', '오멜', '갑', '밧', '힌', '로그',
    '유월절', '무교절', '초실절', '오순절', '칠칠절', '맥추절', '나팔절', '대속죄일', '초막절', '장막절', '수장절', '수전절', '부림절', '안식일', '안식년', '희년',
    '언약궤', '법궤', '증거궤', '속죄소', '시은좌', '우림과 둠밈', '에봇', '흉패', '번제단', '분향단', '금촛대', '등대', '메노라', '떡상', '물두멍',
    '지성소', '성소', '휘장', '번제', '소제', '화목제', '속죄제', '속건제', '요제', '거제', '전제', '십일조'
}

for r in all_entries:
    entry_id = r["id"]
    name_ko = r["name_ko"].strip()
    name_en = (r["name_en"] or "").strip().lower()
    cat = r["category"]
    summary = r["summary"] or ""
    events = r["events"] or ""
    meaning = r["meaning"] or ""

    # Check if this is a term
    if name_ko in term_words or any(tw in name_ko for tw in ['달란트', '세겔', '규빗', '에바', '절기', '제사', '성막']):
        if cat != '단어':
            cur.execute("UPDATE bible_dictionary SET category = '단어' WHERE id = ?;", (entry_id,))
            reclassified_to_term += 1
        continue

    # Check if this entry is a place
    is_place = False
    if name_ko in explicit_places:
        is_place = True
    elif any(name_ko.endswith(suf) for suf in ['산', '강', '바다', '호수', '골짜기', '시내', '광야', '성', '섬']):
        # If not a known person name ending in those letters
        if name_ko not in ['요나단', '나단', '에단', '호산', '엘르아살']:
            is_place = True

    # Check if the summary or meaning describes a place
    if not is_place and cat == '인명':
        # If summary mentions clear place keywords and does not mention person attributes
        has_place_cue = any(cue in summary for cue in ['성읍', '위치한 성읍', '위치한 도시', '산지에 위치한', '항구 도시', '유다의 성읍', '갈릴리의 주요 성읍', '산에 위치한', '해변의 성읍', '고대 유적'])
        has_person_cue = any(pcue in summary for pcue in ['의 아들', '의 아버지', '의 아내', '의 딸', '제사장', '대제사장', '왕으로', '선지자', '사도', '동일한 이름으로 등장하는 인물'])
        
        if has_place_cue and not has_person_cue:
            is_place = True

    if is_place and cat != '지명':
        cur.execute("UPDATE bible_dictionary SET category = '지명' WHERE id = ?;", (entry_id,))
        reclassified_to_place += 1

conn.commit()
print(f"Successfully reclassified:")
print(f"  - {reclassified_to_place} entries -> [지명]")
print(f"  - {reclassified_to_term} entries -> [단어]")

# Final check of categories
cur.execute("SELECT category, count(*) FROM bible_dictionary GROUP BY category;")
print("\nFinal Category Distribution:")
for cat, cnt in cur.fetchall():
    print(f"  - [{cat}]: {cnt} entries")

# Check key places
print("\nVerified Places:")
for test_p in ['블레셋', '애굽', '가나안', '모압', '암몬', '에돔', '앗수르', '바벨론', '두로', '시돈', '사마리아', '안디옥', '에베소', '빌립보', '고린도', '로마', '소돔', '시내산', '갈멜산', '감람산', '요단강', '유브라데', '홍해', '사해']:
    cur.execute("SELECT name_ko, category, meaning, summary FROM bible_dictionary WHERE name_ko = ?;", (test_p,))
    row = cur.fetchone()
    if row:
        print(f"[{row['category']}] {row['name_ko']} (뜻: {row['meaning']})")
        print(f"  요약: {row['summary'][:90]}...")
        print("-" * 50)

# Compress to bible.db.gz
print("\nCompressing database to server/data/bible.db.gz...")
with open(DB_PATH, 'rb') as f_in:
    with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)

gz_size = os.path.getsize(DB_GZ_PATH) / (1024 * 1024)
print(f"Compressed bible.db.gz: {gz_size:.2f} MB")
