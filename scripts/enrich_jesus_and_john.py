import sqlite3
import gzip
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

entries = [
    {
        "name_ko": "예수",
        "name_en": "Jesus",
        "name_original": "יֵשׁוּעַ (히) / Ἰησοῦς (헬)",
        "category": "인명",
        "meaning": "여호와는 구원이시다, 자기 백성을 그들의 죄에서 구원할 자",
        "summary": "인류를 죄와 영원한 사망에서 구원하기 위해 성령으로 잉태되어 동정녀 마리아에게서 나신 하나님의 독생자이자 우리의 유일한 구주(Savior)이시며 만유의 주(Lord)이십니다. 참 하나님이자 참 사람으로서 십자가의 대속과 부활을 통해 영원한 생명을 주셨습니다.",
        "events": "동정녀 탄생(마 1:18-25) → 갈릴리와 유대 공생애 및 천국 복음 선포 → 십자가 대속의 죽음과 사흘 만의 부활 → 40일 후 승천 및 성령 강림 약속 → 다시 오실 재림의 주",
        "key_verses": "마 1:21; 눅 2:11; 요 1:14; 요 14:6; 행 4:12; 빌 2:9-11",
        "aliases": "주 예수, 예수님, Jesus"
    },
    {
        "name_ko": "예수 그리스도",
        "name_en": "Jesus Christ",
        "name_original": "Ἰησοῦς Χριστός",
        "category": "인명",
        "meaning": "기름 부음 받은 구원자이자 만왕의 왕, 영원한 대제사장, 참 선지자",
        "summary": "구약의 모든 율법과 선지자의 예언, 하나님의 언약을 온전히 성취하신 메시아 예수님을 고백하는 기독교 최고의 신앙 명칭입니다. 삼위일체 하나님의 제2위 성자 하나님으로서 인류의 죄를 대신 짊어지시고 십자가에서 영원한 속죄를 단번에 이루셨습니다.",
        "events": "영원 전부터 계신 말씀(로고스) → 성육신과 십자가의 대속 → 부활로 사망 권세를 이기심 → 하나님 보좌 우편 통치 및 만왕의 왕으로 재림",
        "key_verses": "마 1:1; 요 20:31; 롬 1:3-4; 딤전 2:5; 히 1:1-3; 계 19:16",
        "aliases": "그리스도 예수, 주 예수 그리스도, 메시아, 임마누엘, 예수그리스도"
    },
    {
        "name_ko": "세례 요한",
        "name_en": "John the Baptist",
        "name_original": "יוֹחָנָן (히) / Ἰωάννης (헬)",
        "category": "인명",
        "meaning": "여호와는 은혜로우시다 (주의 길을 곧게 예비하는 자)",
        "summary": "사도 요한과 명확히 구별되는 인물로, 제사장 사가랴와 엘리사벳 사이에서 태어난 나실인 선지자입니다. 유대 광야에서 '회개하라 천국이 가까이 왔느니라'를 외치며 백성들에게 회개의 세례를 베풀었고, 예수님께 세례를 베풀며 '보라 세상 죄를 지고 가는 하나님의 어린 양이로다'라고 증언한 구약의 마지막 선구자입니다.",
        "events": "천사의 수태고지와 기적적 출생(눅 1장) → 유대 광야 사역과 회개의 세례(마 3장) → 예수님께 세례 베풂(마 3:13-17) → 헤롯 안디바의 불의를 책망하다 옥에 갇혀 순교(마 14:1-12)",
        "key_verses": "마 3:1-12; 마 11:11; 눅 1:13-17; 요 1:29-34; 요 3:30",
        "aliases": "침례 요한, 세례자 요한, 광야의 외치는 자의 소리"
    },
    {
        "name_ko": "사도 요한",
        "name_en": "John the Apostle",
        "name_original": "Ἰωάννης",
        "category": "인명",
        "meaning": "여호와는 은혜로우시다 (사랑의 사도)",
        "summary": "세례 요한과 명확히 구별되는 인물로, 갈릴리 어부 세베대의 아들이자 사도 야고보의 형제입니다. 예수님의 열두 제자 중 '예수께서 사랑하시는 제자'로 불리며 최후의 만찬에서 주님의 품에 의지했고 십자가 곁에서 어머니 마리아를 부탁받았습니다. 요한복음, 요한일·이·삼서, 요한계시록을 기록한 사랑의 사도입니다.",
        "events": "갈릴리 바다에서 그물을 버려두고 주를 따름(마 4:21-22) → 변화산과 겟세마네 동행 → 십자가 아래에서 마리아를 위탁받음(요 19:26-27) → 밧모 섬에 유배되어 요한계시록 기록(계 1장)",
        "key_verses": "요 13:23; 요 19:26-27; 요 21:20-24; 요일 4:7-12; 계 1:9",
        "aliases": "사랑하시는 제자, 사도요한, 세베대의 아들 요한, 우레의 아들(보아너게)"
    },
    {
        "name_ko": "요한",
        "name_en": "John",
        "name_original": "Ἰωάννης",
        "category": "인명",
        "meaning": "여호와는 은혜로우시다",
        "summary": "신약성경의 핵심 인물들을 지칭하는 이름. ① 예수님의 오심을 예비하고 세례를 베푼 '세례 요한', ② 열두 제자 중 하나이자 요한복음·요한계시록 저자인 세베대의 아들 '사도 요한', ③ 바나바의 생질이자 마가복음 저자인 '마가라 하는 요한' 등이 있습니다.",
        "events": "세례 요한과 사도 요한의 구속사적 사역",
        "key_verses": "마 3:1; 요 1:6; 요 19:26; 행 12:12; 계 1:9",
        "aliases": "요한, 세례 요한, 사도 요한, 마가 요한"
    }
]

def update_entries():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for e in entries:
        cur.execute("SELECT id FROM bible_dictionary WHERE name_ko = ?", (e["name_ko"],))
        row = cur.fetchone()
        if row:
            cur.execute("""
                UPDATE bible_dictionary
                SET name_en = ?, name_original = ?, category = ?, meaning = ?, summary = ?, events = ?, key_verses = ?, aliases = ?
                WHERE id = ?
            """, (
                e["name_en"], e["name_original"], e["category"], e["meaning"], e["summary"],
                e["events"], e["key_verses"], e["aliases"], row[0]
            ))
            print(f"✅ 수정 완료: {e['name_ko']} (ID: {row[0]})")
        else:
            cur.execute("""
                INSERT INTO bible_dictionary (name_ko, name_en, name_original, category, meaning, summary, events, key_verses, aliases)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                e["name_ko"], e["name_en"], e["name_original"], e["category"], e["meaning"],
                e["summary"], e["events"], e["key_verses"], e["aliases"]
            ))
            print(f"✨ 신규 생성: {e['name_ko']}")

    conn.commit()
    conn.close()

    print("\n📦 bible.db.gz 최종 압축 갱신 중...")
    with open(DB_PATH, 'rb') as f_in:
        with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
            
    print("🎉 완료!")

if __name__ == '__main__':
    update_entries()
