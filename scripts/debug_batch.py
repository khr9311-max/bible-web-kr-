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

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, name_ko, name_en, category, meaning, summary FROM bible_dictionary ORDER BY id ASC;")
rows = cur.fetchall()
total = len(rows)
print(f"Total: {total}", flush=True)

# Test first batch of 30
batch_rows = rows[:30]
batch_names = [r["name_ko"] for r in batch_rows]
print("Batch names:", batch_names, flush=True)

prompt = f"""
다음 {len(batch_names)}개의 한글 성경 인명, 지명, 단어(성물/도량형/단위/용어)에 대해 각각:
1. name_ko: 주어진 한글 표제어 그대로 유지
2. name_en: 표준 영문 성경 표기 (예: 아담 -> Adam, 하와 -> Eve, 가인 -> Cain, 아벨 -> Abel 등)
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

t0 = time.time()
print("Calling API...", flush=True)
response = client.models.generate_content(
    model=MODEL_NAME,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.1
    )
)
print(f"API returned in {time.time() - t0:.2f}s", flush=True)
results = json.loads(response.text)
print(f"Got {len(results)} items from API", flush=True)
for r in results[:5]:
    print(r, flush=True)
