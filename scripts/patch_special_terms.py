import sqlite3
import gzip
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

patches = [
    {
        "name_ko": "에봇",
        "name_en": "Ephod",
        "category": "단어",
        "meaning": "성별된 겉옷, 제사장의 성의",
        "summary": "구약 시대 대제사장이 예복 겉옷 위에 걸치던 소매 없는 조끼 모양의 거룩한 옷. 금실, 청색, 자색, 홍색 실과 가늘게 꼰 베실로 정교하게 짰으며 가슴에 열두 보석이 박힌 판결 흉패(우림과 둠밈 수납)를 달았습니다.",
        "events": "대제사장의 거룩한 직무와 하나님의 뜻을 묻는 판결에 사용됨 (출애굽기 28장)"
    },
    {
        "name_ko": "나실인",
        "name_en": "Nazirite",
        "category": "단어",
        "meaning": "구별된 자, 성별된 사람",
        "summary": "하나님께 특별한 서원을 하여 일정 기간 혹은 평생 동안 자기 몸과 삶을 거룩하게 구별하여 바친 사람 (민수기 6장의 '나실인의 법'). 포도나무 소산을 먹지 않고, 머리에 삭도를 대지 않으며, 시체를 가까이하지 않아야 했습니다. 삼손, 사무엘, 세례 요한이 대표적입니다.",
        "events": "민수기 6장의 서원 규례, 삼손/사무엘의 헌신"
    },
    {
        "name_ko": "브돌",
        "name_en": "Pethor",
        "category": "지명",
        "meaning": "해석자, 점술의 장소",
        "summary": "메소포타미아 북부 유브라데 강변에 위치한 고대 성읍. 모압 왕 발락이 이스라엘을 저주하기 위해 불러온 유명한 복술가 발람의 고향입니다 (민수기 22:5).",
        "events": "발락이 발람을 부르기 위해 사신을 보낸 곳"
    },
    {
        "name_ko": "기럇후솟",
        "name_en": "Kiriath-huzoth",
        "category": "지명",
        "meaning": "거리들의 성읍, 넓은 거리의 도시",
        "summary": "모압 왕국의 주요 성읍 중 하나로, 모압 왕 발락이 브돌에서 온 복술가 발람을 영접하고 소와 양을 잡아 제사하며 연회를 베푼 장소입니다 (민수기 22:39).",
        "events": "발락이 발람을 영접하여 첫 제사를 드린 성읍"
    },
    {
        "name_ko": "말기수아",
        "name_en": "Malchishua",
        "category": "인명",
        "meaning": "나의 왕은 구원이시다",
        "summary": "이스라엘의 초대 왕 사울의 셋째 아들로 요나단의 형제입니다. 길보아 산 전투에서 블레셋 군대와 맞서 용감히 싸우다 아버지 사울, 형 요나단과 함께 전사하였습니다 (삼상 31:2).",
        "events": "길보아 산 전투에서 블레셋에 맞서 전사함"
    }
]

def apply_patches():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    for p in patches:
        cur.execute("SELECT id FROM bible_dictionary WHERE name_ko = ?", (p["name_ko"],))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE bible_dictionary
                SET category = ?, name_en = ?, meaning = ?, summary = ?, events = ?
                WHERE id = ?
            """, (p["category"], p["name_en"], p["meaning"], p["summary"], p["events"], row[0]))
            print(f"✅ 업데이트: {p['name_ko']} (ID: {row[0]})")
        else:
            cur.execute("""
                INSERT INTO bible_dictionary (name_ko, name_en, category, meaning, summary, events)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (p["name_ko"], p["name_en"], p["category"], p["meaning"], p["summary"], p["events"]))
            print(f"✨ 신규 추가: {p['name_ko']}")
            
    conn.commit()
    conn.close()
    
    print("\n📦 bible.db.gz 압축 갱신 중...")
    with open(DB_PATH, 'rb') as f_in:
        with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("🎉 완료!")

if __name__ == '__main__':
    apply_patches()
