import sqlite3
import os
import sys
import time
import json
import gzip
import shutil
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

def fix_all_dictionary():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, name_ko, name_en, category, meaning, summary FROM bible_dictionary ORDER BY id ASC;")
    rows = cur.fetchall()
    total = len(rows)
    print(f"총 {total}개의 사전 항목을 배치(Batch)로 전수 정제합니다...")

    schema = {
        "type": "ARRAY",
        "items": {
            "type": "OBJECT",
            "properties": {
                "name_ko": {"type": "STRING"},
                "name_en": {"type": "STRING"},
                "category": {"type": "STRING"},
                "meaning": {"type": "STRING"},
                "summary": {"type": "STRING"}
            },
            "required": ["name_ko", "name_en", "category", "meaning", "summary"]
        }
    }

    BATCH_SIZE = 40
    updated_total = 0

    for i in range(0, total, BATCH_SIZE):
        batch_rows = rows[i:i + BATCH_SIZE]
        batch_names = [r["name_ko"] for r in batch_rows]
        
        prompt = f"""
다음 {len(batch_names)}개의 한글 성경 인명, 지명, 단어(성물/도량형/단위/용어)에 대해 각각:
1. name_ko: 주어진 한글 표제어 그대로 유지
2. name_en: 표준 영문 성경 표기 (예: 나손 -> Nahshon, 갈렙 -> Caleb, 므낫세 -> Manasseh, 입다 -> Jephthah, 에봇 -> Ephod, 달란트 -> Talent 등)
3. category: '인명', '지명', '단어' 중 정확히 하나로 분류
4. meaning: 히브리어/헬라어 어원에 따른 고유한 뜻 (한글 1~5단어)
5. summary: 해당 표제어 자체에 대한 자연스럽고 정통 신학적인 1~2문장 한글 해설 (다른 사람이나 지명과 혼동하지 말고 정확히 기술)

목록: {', '.join(batch_names)}
"""
        
        success = False
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=0.1
                    )
                )
                
                results = json.loads(response.text)
                res_map = {r["name_ko"].strip(): r for r in results if isinstance(r, dict) and "name_ko" in r}
                
                for row in batch_rows:
                    ko = row["name_ko"].strip()
                    if ko in res_map:
                        item = res_map[ko]
                        cur.execute("""
                            UPDATE bible_dictionary
                            SET name_en = ?, category = ?, meaning = ?, summary = ?
                            WHERE id = ?
                        """, (
                            item.get("name_en", "").strip(),
                            item.get("category", row["category"]).strip(),
                            item.get("meaning", row["meaning"]).strip(),
                            item.get("summary", row["summary"]).strip(),
                            row["id"]
                        ))
                        updated_total += 1
                
                conn.commit()
                print(f"[{i + len(batch_rows)}/{total}] 완료 (업데이트 {updated_total}건)")
                success = True
                break
            except Exception as e:
                print(f"⚠️ 배치 {i}~{i+BATCH_SIZE} 처리 중 오류 (시도 {attempt+1}/3): {e}")
                time.sleep(2)
        
        time.sleep(0.1)

    conn.close()
    print(f"\n🎉 전체 {updated_total}건 정제 완료!")

    print("📦 bible.db.gz 최종 압축 중...")
    with open(DB_PATH, 'rb') as f_in:
        with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
            
    gz_size = os.path.getsize(DB_GZ_PATH) / (1024 * 1024)
    print(f"✅ 압축 완료: {gz_size:.2f} MB")

if __name__ == '__main__':
    fix_all_dictionary()
