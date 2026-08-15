import sqlite3
import gzip
import shutil
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# 1. Create bible_dictionary table and indexes
cur.execute("""
CREATE TABLE IF NOT EXISTS bible_dictionary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ko TEXT NOT NULL,
    name_en TEXT,
    name_original TEXT,
    category TEXT NOT NULL, -- '인물' | '지명'
    meaning TEXT,
    summary TEXT NOT NULL,
    events TEXT,
    key_verses TEXT,
    aliases TEXT
);
""")

cur.execute("CREATE INDEX IF NOT EXISTS idx_dict_name_ko ON bible_dictionary(name_ko);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_dict_category ON bible_dictionary(category);")
cur.execute("CREATE INDEX IF NOT EXISTS idx_dict_aliases ON bible_dictionary(aliases);")

# Clear existing dictionary entries if re-running
cur.execute("DELETE FROM bible_dictionary;")

print("Created bible_dictionary schema.")
