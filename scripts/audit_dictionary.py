import sqlite3
import pandas as pd
import codecs

DB_PATH = '../server/data/bible.db'

def audit_db():
    conn = sqlite3.connect(DB_PATH)
    
    with codecs.open("audit_report.txt", "w", encoding="utf-8") as f:
        # 1. 카테고리별 통계
        f.write("=== 카테고리별 항목 수 ===\n")
        df_cat = pd.read_sql_query("SELECT category, COUNT(*) as count FROM bible_dictionary GROUP BY category", conn)
        f.write(df_cat.to_string() + "\n\n")
        
        # 2. 내용이 부실한 항목 (summary나 meaning이 너무 짧은 경우)
        f.write("=== 내용 부실 의심 항목 (summary < 10자 또는 meaning < 10자) ===\n")
        df_short = pd.read_sql_query("""
            SELECT id, name_ko as name, category, length(summary) as sum_len, length(meaning) as mean_len, summary
            FROM bible_dictionary 
            WHERE length(summary) < 10 OR (meaning IS NOT NULL AND length(meaning) > 0 AND length(meaning) < 5)
        """, conn)
        f.write(f"총 발견된 항목 수: {len(df_short)}\n")
        f.write(df_short.head(50).to_string() + "\n\n")
        
        # 3. 템플릿 잔재 의심 항목
        f.write("=== 템플릿 잔재 의심 항목 ('뜻:' 등이 의미 필드 외에 포함된 경우) ===\n")
        df_template = pd.read_sql_query("""
            SELECT id, name_ko as name, category, summary 
            FROM bible_dictionary 
            WHERE summary LIKE '%뜻:%' OR summary LIKE '%의미:%' OR summary LIKE '%원어:%'
        """, conn)
        f.write(f"총 발견된 항목 수: {len(df_template)}\n")
        f.write(df_template.head(50).to_string() + "\n\n")

        # 4. 카테고리 오분류 의심
        f.write("=== 카테고리 오분류 의심 (지명 키워드인데 인명인 경우) ===\n")
        df_misclass = pd.read_sql_query("""
            SELECT id, name_ko as name, category, summary 
            FROM bible_dictionary 
            WHERE category = '인명' AND 
            (name_ko LIKE '%산' OR name_ko LIKE '%골짜기' OR name_ko LIKE '%성' OR name_ko LIKE '%바다' OR name_ko LIKE '%강' OR name_ko LIKE '%못'
            OR summary LIKE '%도시%' OR summary LIKE '%마을%' OR summary LIKE '%지역%' OR summary LIKE '%산맥%')
        """, conn)
        f.write(f"총 발견된 항목 수: {len(df_misclass)}\n")
        f.write(df_misclass.head(50).to_string() + "\n\n")
        
        # 5. 원어 의미(meaning) 누락 통계
        f.write("=== 원어 의미(meaning) 누락 통계 ===\n")
        df_null_meaning = pd.read_sql_query("""
            SELECT category, 
                   COUNT(*) as total, 
                   SUM(CASE WHEN meaning IS NULL OR meaning = '' THEN 1 ELSE 0 END) as missing_meaning 
            FROM bible_dictionary 
            GROUP BY category
        """, conn)
        df_null_meaning['missing_ratio(%)'] = (df_null_meaning['missing_meaning'] / df_null_meaning['total'] * 100).round(2)
        f.write(df_null_meaning.to_string() + "\n\n")

        # 6. 인명/지명/단어 데이터 확인 (무작위 5개씩)
        f.write("=== 카테고리별 샘플 데이터 ===\n")
        for cat in ['인명', '지명', '단어']:
            f.write(f"[{cat}]\n")
            df_sample = pd.read_sql_query(f"SELECT name_ko, meaning, summary FROM bible_dictionary WHERE category = '{cat}' LIMIT 5", conn)
            f.write(df_sample.to_string() + "\n\n")

    conn.close()

if __name__ == "__main__":
    audit_db()
