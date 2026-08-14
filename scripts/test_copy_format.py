import urllib.request
import json
import re

def clean_pure(raw):
    txt = re.sub(r'<cite>\d+</cite>', '', raw)
    txt = re.sub(r'<u class=["\']?[ln]["\']?>[^<]*</u>', '', txt)
    txt = re.sub(r'<span class=["\']?crossref-mark["\']?[^>]*>[^<]*</span>', '', txt)
    txt = re.sub(r'<[^>]*>', '', txt)
    txt = re.sub(r'[○●§]', '', txt)
    return ' '.join(txt.split()).strip()

res = urllib.request.urlopen('http://localhost:3000/api/chapter/1001')
data = json.loads(res.read().decode('utf-8'))
verses = [v for v in data['data']['verses'] if 12 <= v['jeol'] <= 15]

b_name = '창세기'
ch = 1
header = f'[{b_name} {ch}:{verses[0]["jeol"]}-{verses[-1]["jeol"]}]'
lines = [f'{v["jeol"]} {clean_pure(v["phrase_rv"])}' for v in verses]
final_copy = f'{header}\n' + '\n'.join(lines)

print('=== SIMULATED COPIED SCRIPTURE RESULT ===')
print(final_copy)
