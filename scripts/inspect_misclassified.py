import sqlite3
import json
import urllib.request
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('server/data/bible.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Fetch OpenBible geocoding places (all historical biblical places)
openbible_url = "https://raw.githubusercontent.com/openbibleinfo/Bible-Geocoding-Data/master/ancient-places.json"
try:
    req = urllib.request.Request(openbible_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        ob_data = json.loads(resp.read().decode('utf-8'))
        features = ob_data.get("features", [])
        ob_places = set()
        for f in features:
            props = f.get("properties", {})
            title = props.get("title", "")
            if title:
                ob_places.add(title.strip().lower())
                # Handle variants like "Mount Sinai", "River Jordan"
                clean = re.sub(r'^(mount|river|valley|brook|plain|sea of|lake|wilderness of|desert of|land of|island of|waters of)\s+', '', title.strip().lower())
                ob_places.add(clean)
    print(f"Loaded {len(ob_places)} place names from OpenBible.info.")
except Exception as e:
    print(f"Error loading OpenBible: {e}")
    ob_places = set()

# 2. Check all entries currently categorized as '인명' that are actually places, nations, or terms
cur.execute("SELECT id, name_ko, name_en, category, meaning, summary FROM bible_dictionary;")
entries = cur.fetchall()

print(f"\nTotal entries in DB: {len(entries)}")

misclassified_as_person = []
for r in entries:
    name_ko = r["name_ko"]
    name_en = (r["name_en"] or "").lower().strip()
    cat = r["category"]
    summary = r["summary"] or ""
    meaning = r["meaning"] or ""

    if cat == "인명":
        # Check if it matches an ancient place in OpenBible
        if name_en in ob_places:
            misclassified_as_person.append((r["id"], name_ko, name_en, "OpenBible match"))

print(f"Found {len(misclassified_as_person)} entries categorized as '인명' that match OpenBible places!")
for item in misclassified_as_person[:30]:
    print(item)
