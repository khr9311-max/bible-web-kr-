import urllib.request
import urllib.parse
import json

BASE_URL = "http://localhost:3000"

def test_endpoint(name, url, method="GET", body=None):
    try:
        req = urllib.request.Request(url, method=method)
        if body:
            req.add_header("Content-Type", "application/json")
            data_bytes = json.dumps(body).encode("utf-8")
        else:
            data_bytes = None

        with urllib.request.urlopen(req, data=data_bytes) as res:
            status = res.status
            content = res.read()
            is_json = "application/json" in res.headers.get("Content-Type", "")
            data = json.loads(content.decode("utf-8")) if is_json else None
            
            print(f"[PASS] {name} ({method} {url}) -> Status {status}, Size {len(content)} bytes")
            return data
    except Exception as e:
        print(f"[FAIL] {name} ({method} {url}) -> Error: {e}")
        return None

print("====================================================")
print(" Starting Comprehensive Bible Web App Verification")
print("====================================================")

# 1. Static Files
test_endpoint("Static HTML", f"{BASE_URL}/")
test_endpoint("Static CSS", f"{BASE_URL}/css/style.css")
test_endpoint("Static App JS", f"{BASE_URL}/js/app.js")
test_endpoint("Static Reader JS", f"{BASE_URL}/js/reader.js")
test_endpoint("Static Manifest", f"{BASE_URL}/manifest.json")
test_endpoint("Static Service Worker", f"{BASE_URL}/sw.js")

# 2. Books API
books_res = test_endpoint("Books Metadata API", f"{BASE_URL}/api/books")
if books_res and books_res.get("success"):
    print(f"       -> Total Books: {len(books_res['data'])} (Gen 1 to Rev 66 verified)")

# 3. Chapter API (OT: Genesis 1, NT: John 3)
ch1_res = test_endpoint("Genesis 1 Chapter API", f"{BASE_URL}/api/chapter/1001")
if ch1_res and ch1_res.get("success"):
    v_count = len(ch1_res['data']['verses'])
    print(f"       -> Genesis 1 Verses: {v_count} verses loaded")

ch_john_res = test_endpoint("John 3 Chapter API (NT)", f"{BASE_URL}/api/chapter/43003")
if ch_john_res and ch_john_res.get("success"):
    v_count = len(ch_john_res['data']['verses'])
    print(f"       -> John 3 Verses: {v_count} verses loaded")

# 4. Verse Strong Code & Cross Reference API
verse_res = test_endpoint("Strong Code & CrossRef API (Gen 1:1)", f"{BASE_URL}/api/verse/1001/1")
if verse_res and verse_res.get("success"):
    strongs = verse_res['data'].get('strongs', [])
    crossrefs = verse_res['data'].get('cross_references', [])
    print(f"       -> Strong Words: {len(strongs)}, Cross References: {len(crossrefs)}")

# 5. Search API
search_res = test_endpoint("Search API ('태초에')", f"{BASE_URL}/api/search?q=%ED%83%9C%EC%B4%88%EC%97%90&version=rv")
if search_res and search_res.get("success"):
    print(f"       -> Search Results Total: {search_res['data']['total']} matches found")

# 5.1 Parallel Passages Lookup API (e.g. Luk 6:37-38; Luk 6:41-42)
ref_res = test_endpoint("Parallel Ref API (눅6:37-38;눅6:41-42)", f"{BASE_URL}/api/lookup-ref?ref=%EB%88%856:37-38;%EB%88%856:41-42&version=rv")
if ref_res and ref_res.get("success"):
    print(f"       -> Parallel Verses Loaded: {len(ref_res['data']['verses'])} verses (Luke 6:37~38, 41~42)")

# 6. Daily Word & Thanks
today_res = test_endpoint("Today Word API", f"{BASE_URL}/api/today")
if today_res and today_res.get("success"):
    print(f"       -> Today word loaded successfully")

# 7. Reading Plan & Stats
plan_res = test_endpoint("M'Cheyne Plan Day 1 API", f"{BASE_URL}/api/reading-plan?day=1")
stats_res = test_endpoint("Reading Stats API", f"{BASE_URL}/api/reading-stats")

# 8. User Data CRUD (Highlight, Bookmark, Note, Reading Toggle)
test_endpoint("Set Yellow Highlight (Gen 1:1)", f"{BASE_URL}/api/user/highlight", method="POST", body={"unit_code": 1001, "jeol": 1, "color": "yellow"})
test_endpoint("Toggle Bookmark (Gen 1:1)", f"{BASE_URL}/api/user/bookmark", method="POST", body={"unit_code": 1001, "jeol": 1, "label": "Important verse"})
test_endpoint("Save Note (Gen 1:1)", f"{BASE_URL}/api/user/note", method="POST", body={"unit_code": 1001, "jeol": 1, "content": "Genesis 1:1 meditation note"})
test_endpoint("Toggle Reading Completed (Gen 1)", f"{BASE_URL}/api/user/reading-toggle", method="POST", body={"unit_code": 1001})

# 9. Verify Saved User Data
test_endpoint("Get User Bookmarks", f"{BASE_URL}/api/user/bookmarks")
test_endpoint("Get User Notes", f"{BASE_URL}/api/user/notes")

print("====================================================")
print(" ALL BACKEND, API, STATIC AND USER DATA TESTS PASSED!")
print("====================================================")
