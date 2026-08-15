import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def clean_verse_html(raw):
    if not raw: return ''
    txt = raw
    txt = re.sub(r'<a\s+[^>]*href=[\'"]lnk\.spc\?([^\'"]+)[\'"][^>]*>([\s\S]*?)</a>', r'[\2]', txt)
    txt = re.sub(r'<h2>([\s\S]*?)</h2>', r'<div class="section-stitle inline-section-stitle">\1</div>', txt)
    txt = re.sub(r'<h4>([\s\S]*?)</h4>', r'<div class="inline-stitle-ref-wrap">\1</div>', txt)
    txt = re.sub(r'</?p>', '', txt)
    txt = re.sub(r'<cite>\d+</cite>', '', txt)
    txt = re.sub(r'<u class=[\'"]?[lnc][\'"]?>([^<]+)</u>', r'<span class="crossref-mark">\1</span>', txt)
    # Jesus words (<i> in NT)
    txt = re.sub(r'<i>', '<span class="jesus-word">', txt, flags=re.IGNORECASE)
    txt = re.sub(r'</i>', '</span>', txt, flags=re.IGNORECASE)
    return txt

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

# Test Genesis 4:23 (OT - should NOT have jesus-word)
cur.execute('SELECT phrase_rv FROM verses WHERE unit_code=1004 AND jeol=23;')
gen4 = cur.fetchone()[0]
print('OT Gen 4:23 ->', clean_verse_html(gen4))

# Test Matthew 5:3 (NT - SHOULD have jesus-word)
cur.execute('SELECT phrase_rv FROM verses WHERE unit_code=40005 AND jeol=3;')
mat5 = cur.fetchone()[0]
print('NT Mat 5:3 ->', clean_verse_html(mat5))

# Test John 3:16 (NT - SHOULD have jesus-word)
cur.execute('SELECT phrase_rv FROM verses WHERE unit_code=43003 AND jeol=16;')
jhn3 = cur.fetchone()[0]
print('NT John 3:16 ->', clean_verse_html(jhn3))
