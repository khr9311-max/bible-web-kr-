import sqlite3
import os
import sys
import time
import json
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = '../server/data/bible.db'

# Use existing API Key or throw error
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable is not set.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

def refine_dictionary():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Find entries that have bad translations (e.g. "출신의", "의 딸", "마헬살랄하스바스", "성경의 주요 인물로", or length < 20)
    # Also we skip explicit_places and those already manually updated (by checking if they don't have the typical bad substrings and have decent length? 
    # Actually, almost all of them have "성경의 주요 인물로" or are bad. Let's just select those that have specific bad patterns or very short text.
    
    query = """
        SELECT id, name_ko, name_en, category, meaning, summary, events 
        FROM bible_dictionary
        WHERE 
            summary LIKE '%성경의 주요 인물로%' OR
            summary LIKE '%마헬살랄하스바스%' OR
            summary LIKE '%출신의%' OR
            summary LIKE '%의 딸%' OR
            summary LIKE '%의 아들%' OR
            summary LIKE '%동일한 이름으로%' OR
            length(summary) < 20 OR
            length(meaning) < 2 OR
            meaning IS NULL
        ORDER BY id ASC
    """
    cur.execute(query)
    rows = cur.fetchall()
    
    print(f"총 {len(rows)}개의 항목을 AI 정제 대상으로 식별했습니다.")
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "meaning": {
                "type": "STRING",
                "description": "The original meaning of the name in Korean (e.g., '하나님의 집', '여호와는 구원이시다'). Keep it concise (1-5 words)."
            },
            "summary": {
                "type": "STRING",
                "description": "A clear, theologically sound, and natural Korean summary of the person/place/term (1-2 sentences). Do NOT use generic templates."
            },
            "category": {
                "type": "STRING",
                "description": "Must be exactly one of: '인명', '지명', '단어'"
            }
        },
        "required": ["meaning", "summary", "category"]
    }

    system_instruction = """
    You are an expert biblical theologian and translator. 
    Your task is to correct and refine broken Bible dictionary entries into authentic, natural, and accurate Korean.
    The input will provide the Korean name, English name, and the currently broken summary.
    Provide the precise original meaning of the name (meaning), a concise theological/biblical summary (summary), and correctly classify it as '인명'(Person), '지명'(Place), or '단어'(Term).
    Do not use unnatural machine translation artifacts like '성경의 주요 인물로', '출신의', or random names like '마헬살랄하스바스'.
    """
    
    updated_count = 0
    # Process in small batches for safety (I'll do 50 items just to show it works, then the user can run it fully later or we process all if time permits)
    # Actually, doing 3000 items sequentially via API in a script during this session might take ~1 hour and time out.
    # Let's process a batch of 50 to demonstrate, and save a script the user can run overnight.
    # Wait, the user said "진행해", I can process as many as possible or use asyncio for concurrent requests.
    
    # I'll use a smaller batch for this execution, but leave the script capable of running all.
    limit = 3000 # Adjust this if needed
    rows_to_process = rows[:limit]
    
    print(f"이번 실행에서는 {limit}개 항목을 정제합니다...")
    
    for row in rows_to_process:
        entry_id = row['id']
        name_ko = row['name_ko']
        name_en = row['name_en'] or ""
        old_cat = row['category']
        old_meaning = row['meaning'] or ""
        old_summary = row['summary'] or ""
        
        prompt = f"Korean Name: {name_ko}\nEnglish Name: {name_en}\nCurrent Category: {old_cat}\nCurrent Broken Meaning: {old_meaning}\nCurrent Broken Summary: {old_summary}"
        
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1
                )
            )
            
            result = json.loads(response.text)
            new_meaning = result.get('meaning', '').strip()
            new_summary = result.get('summary', '').strip()
            new_cat = result.get('category', old_cat).strip()
            
            cur.execute("""
                UPDATE bible_dictionary 
                SET meaning = ?, summary = ?, category = ? 
                WHERE id = ?
            """, (new_meaning, new_summary, new_cat, entry_id))
            
            conn.commit()
            updated_count += 1
            print(f"[{new_cat}] {name_ko} ({name_en}) - 뜻: {new_meaning} | {new_summary[:50]}...")
            
            time.sleep(0.1) # Rate limiting prevention
            
        except Exception as e:
            print(f"Failed to process {name_ko}: {e}")
            time.sleep(5)
            
    conn.close()
    print(f"\n정제 완료: {updated_count}개 항목 업데이트됨.")
    print("나머지 항목들을 처리하려면 limit 제한을 해제하고 스크립트를 백그라운드에서 실행하십시오.")

if __name__ == "__main__":
    refine_dictionary()
