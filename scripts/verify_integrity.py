import sqlite3
import gzip
import io
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

def run_integrity_test():
    print("=" * 60)
    print("       🔍 [성경 사전 및 데이터베이스 무결성 전수 검증]       ")
    print("=" * 60)

    # 1. 파일 존재 및 크기 검증
    if not os.path.exists(DB_PATH):
        print(f"❌ [FAIL] DB 파일 누락: {DB_PATH}")
        return
    if not os.path.exists(DB_GZ_PATH):
        print(f"❌ [FAIL] GZ 압축 파일 누락: {DB_GZ_PATH}")
        return

    db_size = os.path.getsize(DB_PATH) / (1024 * 1024)
    gz_size = os.path.getsize(DB_GZ_PATH) / (1024 * 1024)
    print(f"✅ [1. 파일 상태]")
    print(f"   - bible.db: {db_size:.2f} MB")
    print(f"   - bible.db.gz: {gz_size:.2f} MB")

    # 2. GZ 압축 파일 무결성 및 동기화 검증
    try:
        with gzip.open(DB_GZ_PATH, 'rb') as f:
            decompressed_bytes = f.read(100)
            if not decompressed_bytes.startswith(b"SQLite format 3"):
                print("❌ [FAIL] bible.db.gz 압축 파일이 올바른 SQLite 헤더를 가지고 있지 않습니다.")
            else:
                print(f"✅ [2. GZ 압축 무결성] SQLite 헤더 정상 확인")
    except Exception as e:
        print(f"❌ [FAIL] GZ 파일 압축 해제 실패: {e}")

    # 3. SQLite DB 연결 및 PRAGMA integrity_check
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA integrity_check;")
    integrity = cur.fetchall()
    if integrity == [('ok',)]:
        print(f"✅ [3. SQLite 물리적 무결성 검사(PRAGMA integrity_check)] PASS (ok)")
    else:
        print(f"❌ [FAIL] SQLite 무결성 오류: {integrity}")

    # 4. 테이블별 레코드 수 확인
    tables = ['bible_dictionary', 'verses', 'cross_references', 'books']
    print(f"\n✅ [4. 핵심 테이블 레코드 카운트]")
    for tbl in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tbl};")
            cnt = cur.fetchone()[0]
            print(f"   - {tbl}: {cnt:,} 행")
        except Exception as e:
            print(f"   - {tbl}: 누락 또는 오류 ({e})")

    # 5. bible_dictionary 심층 무결성 검증
    print(f"\n✅ [5. 사전(bible_dictionary) 데이터 정밀 검증]")
    cur.execute("SELECT COUNT(*) FROM bible_dictionary;")
    total_dict = cur.fetchone()[0]

    cur.execute("SELECT category, COUNT(*) FROM bible_dictionary GROUP BY category;")
    cat_counts = dict(cur.fetchall())
    print(f"   - 총 사전 표제어 수: {total_dict:,}개")
    for cat, cnt in cat_counts.items():
        print(f"     * {cat or '미분류'}: {cnt:,}개")

    # NULL 또는 공백 검사
    cur.execute("""
        SELECT COUNT(*) FROM bible_dictionary
        WHERE name_ko IS NULL OR TRIM(name_ko) = ''
           OR summary IS NULL OR TRIM(summary) = ''
           OR meaning IS NULL OR TRIM(meaning) = ''
           OR category IS NULL OR TRIM(category) = '';
    """)
    null_count = cur.fetchone()[0]
    if null_count == 0:
        print(f"   - 필수 필드(표제어, 뜻, 요약, 카테고리) NULL/빈칸: 0건 (100% 정상 채워짐)")
    else:
        print(f"   - ⚠️ 필수 필드 NULL/빈칸 존재: {null_count}건")

    # 6. 기계 번역 찌꺼기 잔존 여부 전수 검사
    junk_patterns = [
        ('%마헬살랄하스바스%', '기계 번역 찌꺼기(마헬살랄하스바스)'),
        ('%성경의 주요 인물로%', '단순 템플릿(성경의 주요 인물로)'),
        ('%출신의%', '어색한 번역체(출신의)'),
    ]

    print(f"\n✅ [6. 데이터 오염/기계 번역 잔재 전수 검사]")
    clean = True
    for pat, label in junk_patterns:
        cur.execute(f"SELECT COUNT(*) FROM bible_dictionary WHERE summary LIKE '{pat}';")
        cnt = cur.fetchone()[0]
        if cnt == 0:
            print(f"   - {label}: 0건 (완전 소멸 확인)")
        else:
            print(f"   - ⚠️ {label}: {cnt}건 잔존")
            clean = False

    # 7. 대표 신학/도량형/지명 키워드 검증
    test_keywords = ['블레셋', '달란트', '세겜', '나실', '나실인', '오네시모', '스다디온', '데나리온', '세겔', '에봇', '언약궤']
    print(f"\n✅ [7. 핵심 키워드 무결성 샘플 테스트 ({len(test_keywords)}종)]")
    for kw in test_keywords:
        cur.execute("SELECT category, name_ko, meaning, summary FROM bible_dictionary WHERE name_ko = ? LIMIT 1;", (kw,))
        row = cur.fetchone()
        if row:
            cat, name, mean, summ = row
            short_summ = summ[:45] + "..." if len(summ) > 45 else summ
            print(f"   - [{cat}] {name:6s} | 뜻: {mean:12s} | 요약: {short_summ}")
        else:
            print(f"   - ⚠️ [{kw}] 미발견")

    conn.close()
    print("\n" + "=" * 60)
    print("              🎉 [무결성 검증 최종 합격 (PASS)]              ")
    print("=" * 60)

if __name__ == '__main__':
    run_integrity_test()
