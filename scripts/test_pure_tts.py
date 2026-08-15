import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_pure_verse_text(raw):
    if not raw: return ''
    txt = raw
    txt = re.sub(r'<h\d[\s\S]*?</h\d>', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'<a\s+[^>]*href=[\'"]lnk\.spc\?[^\'"]+[\'"][^>]*>[\s\S]*?</a>', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'<cite>\d+</cite>', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'<u class=[\'"]?[lnc][\'"]?>[^<]*</u>', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'<span class=[\'"]?crossref-mark[\'"]?[^>]*>[^<]*</span>', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = txt.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    txt = re.sub(r'[○●§]', '', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt

conn = sqlite3.connect('server/data/bible.db')
cur = conn.cursor()

# Test NIV Genesis 1:27 (has <br>, <span class=tab1>, <u class=l>BU</u>)
cur.execute('SELECT phrase_nv FROM verses WHERE unit_code=1001 AND jeol=27;')
row = cur.fetchone()[0]
print('Raw NIV Gen 1:27:', row)
print('Pure NIV Gen 1:27:', get_pure_verse_text(row))

# Test RV Matthew 5:3
cur.execute('SELECT phrase_rv FROM verses WHERE unit_code=40005 AND jeol=3;')
row = cur.fetchone()[0]
print('Raw RV Mat 5:3:', row)
print('Pure RV Mat 5:3:', get_pure_verse_text(row))
