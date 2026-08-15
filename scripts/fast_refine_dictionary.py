import sqlite3
import os
import sys
import time
import json
import gzip
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-3.1-flash-lite"

def process_batch(batch_rows, batch_idx, total_batches):
    client = genai.Client(api_key=API_KEY)
    batch_names = [r["name_ko"] for r in batch_rows]
    
    prompt = f"""
다음 {len(batch_names)}개의 한글 성경 인명, 지명, 단어(성물/도량형/단위/용어)에 대해 각각:
1. name_ko: 주어진 한글 표제어 그대로 유지
2. name_en: 공인 표준 영문 성경 표기 (예: 나손 -> Nahshon, 갈렙 -> Caleb, 므낫세 -> Manasseh, 입다 -> Jephthah, 에봇 -> Ephod, 달란트 -> Talent 등)
3. category: '인명', '지명', '단어' 중 정확히 하나로 분류
4. meaning: 히브리어/헬라어 어원에 따른 고유한 뜻 (한글 1~5단어)
5. summary: 해당 표제어 자체에 대한 자연스럽고 정통 신학적인 1~2문장 한글 해설 (다른 사람이나 지명과 혼동하지 말고 정확히 기술)

목록: {', '.join(batch_names)}
"""

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
            print(f"✅ 배치 [{batch_idx}/{total_batches}] 성공 ({len(results)}건)", flush=True)
            return results
        except Exception as e:
            print(f"⚠️ 배치 [{batch_idx}/{total_batches}] 실패 (시도 {attempt+1}/3): {e}", flush=True)
            time.sleep(2)
            
    return []

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT id, name_ko, name_en, category, meaning, summary FROM bible_dictionary ORDER BY id ASC;")
    rows = cur.fetchall()
    total = len(rows)
    print(f"총 {total}개의 사전 항목을 병렬 고속 배치로 전수 정제합니다...", flush=True)

    BATCH_SIZE = 35
    batches = [rows[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    total_batches = len(batches)
    print(f"총 {total_batches}개 배치 생성 완료. 병렬 스레드 가동...", flush=True)

    all_results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(process_batch, batch, idx + 1, total_batches): batch for idx, batch in enumerate(batches)}
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_results.extend(res)

    print(f"\n총 {len(all_results)}개의 정제된 항목을 DB에 일괄 커밋합니다...", flush=True)
    res_map = {r["name_ko"].strip(): r for r in all_results if isinstance(r, dict) and "name_ko" in r}

    updated_cnt = 0
    for r in rows:
        ko = r["name_ko"].strip()
        if ko in res_map:
            item = res_map[ko]
            cur.execute("""
                UPDATE bible_dictionary
                SET name_en = ?, category = ?, meaning = ?, summary = ?
                WHERE id = ?
            """, (
                item.get("name_en", "").strip(),
                item.get("category", r["category"]).strip(),
                item.get("meaning", r["meaning"]).strip(),
                item.get("summary", r["summary"]).strip(),
                r["id"]
            ))
            updated_cnt += 1

    conn.commit()
    conn.close()
    print(f"🎉 SQLite DB 업데이트 완료: 총 {updated_cnt}건 반영됨!", flush=True)

    print("📦 bible.db.gz 최종 압축 생성 중...", flush=True)
    with open(DB_PATH, 'rb') as f_in:
        with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
            
    gz_size = os.path.getsize(DB_GZ_PATH) / (1024 * 1024)
    print(f"✅ 압축 완료: {gz_size:.2f} MB", flush=True)

if __name__ == '__main__':
    main()
