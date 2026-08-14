import urllib.request
import json
import re

def clean_pure(raw):
    txt = re.sub(r'<cite>\d+</cite>', '', raw)
    txt = re.sub(r'<u class=["\']?[lnc]["\']?>[^<]*</u>', '', txt)
    txt = re.sub(r'<span class=["\']?crossref-mark["\']?[^>]*>[^<]*</span>', '', txt)
    txt = re.sub(r'<[^>]*>', '', txt)
    txt = re.sub(r'[○●§]', '', txt)
    return ' '.join(txt.split()).strip()

res = urllib.request.urlopen('http://localhost:3000/api/chapter/40005')
data = json.loads(res.read().decode('utf-8'))
v27 = next(v for v in data['data']['verses'] if v['jeol'] == 27)

header = '[마태복음 5:27]'
line = f'{v27["jeol"]} {clean_pure(v27["phrase_rv"])}'
with open('scripts/output_mat5_test.txt', 'w', encoding='utf-8') as f:
    f.write(f'{header}\n{line}')
print("Saved to scripts/output_mat5_test.txt")
