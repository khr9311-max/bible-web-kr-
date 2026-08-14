import urllib.request, json

url = 'http://localhost:3000/api/lookup-ref?ref=%EB%A7%899:50;%EB%88%8514:34-35&version=rv'
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode('utf-8'))
    print('Success:', data.get('success'))
    verses = data['data']['verses']
    print(f'Total verses: {len(verses)}')
    for v in verses:
        b = v['book_name']
        ch = v['chapter']
        j = v['jeol']
        txt = v['phrase_rv']
        print(f"[{b} {ch}:{j}] {txt[:35]}...")
