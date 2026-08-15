import sqlite3
import os
import sys
import json
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')

API_KEY = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

test_names = ["나손", "갈렙", "입다", "오벳", "이새", "여호사밧", "아몬", "웃시야", "아하스", "에봇", "달란트", "블레셋", "세겜"]

prompt = f"""
다음 성경 인명, 지명, 성경 단어(도량형/성물) 목록에 대해 각각:
1. 정확한 표준 영문 성경 이름 (name_en, 예: 나손 -> Nahshon, 갈렙 -> Caleb, 입다 -> Jephthah, 오벳 -> Obed, 이새 -> Jesse, 에봇 -> Ephod, 달란트 -> Talent 등)
2. 올바른 카테고리 (category: '인명', '지명', '단어')
3. 이름의 고유한 어원/뜻 (meaning: 1~5단어 한글)
4. 해당 인물/지명/단어 자체에 대한 정확하고 정통 신학적인 1~2문장 한글 요약 (summary)

목록: {', '.join(test_names)}
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
for r in results:
    print(f"[{r['category']}] {r['name_ko']} (영문: {r['name_en']}) | 뜻: {r['meaning']}")
    print(f"   요약: {r['summary']}\n")
