import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = '../server/data/bible.db'

def fix_categories():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 지명 의심 항목 재분류 (인명 -> 지명)
    place_keywords = ['산', '골짜기', '성', '바다', '강', '못']
    place_summary_keywords = ['도시', '마을', '지역', '산맥', '남쪽', '동쪽', '북쪽', '서쪽', '성읍']
    
    # 예외로 둘 진짜 인명
    person_exceptions = ['요나단', '나단', '에단', '호산', '엘르아살']
    
    # 카테고리가 '인명'인데 위 키워드들이 포함된 경우 '지명'으로 업데이트
    cur.execute("""
        SELECT id, name_ko, summary 
        FROM bible_dictionary 
        WHERE category = '인명'
    """)
    rows = cur.fetchall()
    
    reclassified_to_place = 0
    for row in rows:
        id_val, name_ko, summary = row
        summary = summary if summary else ""
        
        is_place = False
        if any(name_ko.endswith(kw) for kw in place_keywords) and name_ko not in person_exceptions:
            is_place = True
        
        if not is_place and any(kw in summary for kw in place_summary_keywords):
            # summary에 지명 키워드가 있지만 인명 힌트는 없는지 확인
            person_hints = ['아들', '딸', '아버지', '어머니', '남편', '아내', '왕', '제사장', '선지자', '사도', '인물']
            if not any(ph in summary for ph in person_hints):
                is_place = True
                
        if is_place:
            cur.execute("UPDATE bible_dictionary SET category = '지명' WHERE id = ?", (id_val,))
            reclassified_to_place += 1
            print(f"[인명 -> 지명] 변경됨: {name_ko}")

    # 단어(용어) 오분류 수정
    terms = ['에봇', '우림과 둠밈', '흉패', '언약궤', '법궤', '증거궤']
    reclassified_to_term = 0
    for term in terms:
        cur.execute("UPDATE bible_dictionary SET category = '단어' WHERE name_ko = ?", (term,))
        if cur.rowcount > 0:
            reclassified_to_term += cur.rowcount
            print(f"[기타 -> 단어] 변경됨: {term}")

    conn.commit()
    conn.close()
    
    print(f"\n총 {reclassified_to_place}건이 지명으로 변경되었습니다.")
    print(f"총 {reclassified_to_term}건이 단어로 변경되었습니다.")

if __name__ == "__main__":
    fix_categories()
