import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

def is_para_start(v):
    if v['jeol'] == 1:
        return True
    raw_rv = v.get('phrase_rv') or ''
    raw_pri = v.get('phrase_pri') or ''
    
    # Check stitle
    if v.get('stitle_rv') or v.get('stitle_pri'):
        return True
    
    # Check paragraph markers in RV (the standard Korean marker)
    if '○' in raw_rv or '●' in raw_rv or '§' in raw_rv:
        return True
    if '<p>' in raw_rv:
        return True
    if '<h2>' in raw_rv:
        return True
        
    # Also check primary version if not RV
    if '○' in raw_pri or '●' in raw_pri or '§' in raw_pri:
        return True
    if '<p>' in raw_pri:
        return True
    if '<h2>' in raw_pri:
        return True
        
    return False

# Test Genesis 1
cur.execute("SELECT jeol, phrase_rv, stitle_rv FROM verses WHERE unit_code=1001 ORDER BY jeol;")
rows = cur.fetchall()
verses = [{'jeol': r[0], 'phrase_rv': r[1], 'stitle_rv': r[2]} for r in rows]

para_starts = [v['jeol'] for v in verses if is_para_start(v)]
print("Gen 1 paragraph starts at verses:", para_starts)

# Test Matthew 5
cur.execute("SELECT jeol, phrase_rv, stitle_rv FROM verses WHERE unit_code=40005 ORDER BY jeol;")
rows = cur.fetchall()
verses = [{'jeol': r[0], 'phrase_rv': r[1], 'stitle_rv': r[2]} for r in rows]

para_starts = [v['jeol'] for v in verses if is_para_start(v)]
print("Mat 5 paragraph starts at verses:", para_starts)

# Test Luke 1
cur.execute("SELECT jeol, phrase_rv, stitle_rv FROM verses WHERE unit_code=42001 ORDER BY jeol;")
rows = cur.fetchall()
verses = [{'jeol': r[0], 'phrase_rv': r[1], 'stitle_rv': r[2]} for r in rows]

para_starts = [v['jeol'] for v in verses if is_para_start(v)]
print("Luke 1 paragraph starts at verses:", para_starts)

# Test Psalm 23
cur.execute("SELECT jeol, phrase_rv, stitle_rv FROM verses WHERE unit_code=19023 ORDER BY jeol;")
rows = cur.fetchall()
verses = [{'jeol': r[0], 'phrase_rv': r[1], 'stitle_rv': r[2]} for r in rows]

para_starts = [v['jeol'] for v in verses if is_para_start(v)]
print("Psalm 23 paragraph starts at verses:", para_starts)

# Test Romans 8
cur.execute("SELECT jeol, phrase_rv, stitle_rv FROM verses WHERE unit_code=45008 ORDER BY jeol;")
rows = cur.fetchall()
verses = [{'jeol': r[0], 'phrase_rv': r[1], 'stitle_rv': r[2]} for r in rows]

para_starts = [v['jeol'] for v in verses if is_para_start(v)]
print("Romans 8 paragraph starts at verses:", para_starts)
