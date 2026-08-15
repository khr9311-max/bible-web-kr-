const { DatabaseSync } = require('node:sqlite');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, 'data', 'bible.db');
const STRONG_DICT_PATH = path.join(__dirname, 'data', 'strong_dict.json');

let strongDict = {};
if (fs.existsSync(STRONG_DICT_PATH)) {
    try {
        strongDict = JSON.parse(fs.readFileSync(STRONG_DICT_PATH, 'utf-8'));
    } catch (e) {
        console.error('Failed to load strong dictionary:', e);
    }
}

const db = new DatabaseSync(DB_PATH);

// 1. 성경 66권 목록 조회
function getBooks() {
    return db.prepare('SELECT id, name, abbr, eng_name, eng_abbr, testament, category, chapters FROM books ORDER BY id ASC').all();
}

function getBook(bookId) {
    return db.prepare('SELECT * FROM books WHERE id = ?').get(bookId);
}

// 2. 장별 성경 본문 조회
function getChapterVerses(unitCode) {
    const verses = db.prepare(`
        SELECT unit_code, book_id, chapter, jeol, stitle_rv,
               phrase_rv, phrase_ko, phrase_nw, phrase_ez, phrase_wr,
               phrase_nv, phrase_nt, phrase_es, phrase_nb, phrase_kj
        FROM verses 
        WHERE unit_code = ? 
        ORDER BY jeol ASC
    `).all(unitCode);

    // 해당 장의 하이라이트 및 북마크, 메모 정보도 함께 첨부
    const highlights = db.prepare('SELECT jeol, color FROM user_highlights WHERE unit_code = ?').all(unitCode);
    const bookmarks = db.prepare('SELECT id, jeol, label FROM user_bookmarks WHERE unit_code = ?').all(unitCode);
    const notes = db.prepare('SELECT id, jeol, content, updated_at FROM user_notes WHERE unit_code = ?').all(unitCode);
    const readStatus = db.prepare('SELECT read_count, last_read_at FROM user_reading_log WHERE unit_code = ?').get(unitCode);

    const highlightMap = {};
    highlights.forEach(h => { highlightMap[h.jeol] = h.color; });

    const bookmarkMap = {};
    bookmarks.forEach(b => { bookmarkMap[b.jeol] = b; });

    const noteMap = {};
    notes.forEach(n => { noteMap[n.jeol] = n; });

    return {
        unit_code: unitCode,
        is_read: !!readStatus,
        read_info: readStatus || null,
        verses: verses.map(v => ({
            ...v,
            highlight: highlightMap[v.jeol] || null,
            bookmark: bookmarkMap[v.jeol] || null,
            note: noteMap[v.jeol] || null
        }))
    };
}

// 3. 특정 절 상세 정보 (원어 스트롱 분해 및 관주 포함)
function getVerseDetails(unitCode, jeol) {
    const verse = db.prepare('SELECT * FROM verses WHERE unit_code = ? AND jeol = ?').get(unitCode, jeol);
    if (!verse) return null;

    const strongs = db.prepare(`
        SELECT phrase_order, strong_code, phrase, bracket, space 
        FROM strong_phrases 
        WHERE unit_code = ? AND jeol = ? 
        ORDER BY phrase_order ASC
    `).all(unitCode, jeol);

    // 스트롱 사전 정보 확장
    const enrichedStrongs = strongs.map(s => {
        const dictInfo = s.strong_code ? strongDict[s.strong_code] : null;
        return {
            ...s,
            original: dictInfo ? dictInfo.original : (s.strong_code || ''),
            translit: dictInfo ? dictInfo.translit : '',
            pronounce: dictInfo ? dictInfo.pronounce : '',
            meaning: dictInfo ? dictInfo.meaning : '',
            definition: dictInfo ? dictInfo.definition : ''
        };
    });

    const crossRefs = db.prepare(`
        SELECT version, kind, mark, explains, link_ids 
        FROM cross_references 
        WHERE unit_code = ? AND jeol = ?
    `).all(unitCode, jeol);

    return {
        ...verse,
        strongs: enrichedStrongs,
        cross_references: crossRefs
    };
}

// 4. 스트롱 번호 사전 정보 단독 조회
function getStrongInfo(code) {
    const cleanCode = (code || '').toUpperCase().trim();
    if (strongDict[cleanCode]) {
        return { code: cleanCode, ...strongDict[cleanCode] };
    }
    // 사전에 없는 경우 기본 정보
    const isHebrew = cleanCode.startsWith('H');
    return {
        code: cleanCode,
        original: isHebrew ? '히브리어 어휘' : '헬라어 어휘',
        translit: cleanCode,
        pronounce: '',
        meaning: `Strong's ${cleanCode}`,
        definition: `성경 원어 번호 ${cleanCode}에 해당하는 어휘입니다.`
    };
}

// 5. 검색 엔진 (역본별 키워드 검색)
function searchVerses(query, version = 'rv', limit = 50, offset = 0) {
    if (!query || query.trim().length === 0) return { total: 0, items: [] };

    const colMap = {
        'rv': 'phrase_rv',
        'ko': 'phrase_ko',
        'nw': 'phrase_nw',
        'ez': 'phrase_ez',
        'wr': 'phrase_wr',
        'nv': 'phrase_nv',
        'nt': 'phrase_nt',
        'es': 'phrase_es',
        'nb': 'phrase_nb',
        'kj': 'phrase_kj'
    };

    const targetCol = colMap[version] || 'phrase_rv';
    const cleanQuery = `%${query.trim()}%`;

    const countRow = db.prepare(`
        SELECT count(*) as total 
        FROM verses 
        WHERE ${targetCol} LIKE ?
    `).get(cleanQuery);

    const rows = db.prepare(`
        SELECT v.unit_code, v.book_id, v.chapter, v.jeol, v.stitle_rv, v.${targetCol} as text,
               b.name as book_name, b.abbr as book_abbr
        FROM verses v
        JOIN books b ON v.book_id = b.id
        WHERE v.${targetCol} LIKE ?
        ORDER BY v.unit_code ASC, v.jeol ASC
        LIMIT ? OFFSET ?
    `).all(cleanQuery, limit, offset);

    return {
        query: query.trim(),
        version,
        total: countRow ? countRow.total : 0,
        items: rows
    };
}

// 6. 오늘의 말씀 & 한 줄 감사
function getTodayContent() {
    const todayWordsCount = db.prepare('SELECT count(*) as cnt FROM today_words').get().cnt;
    const thanksCount = db.prepare('SELECT count(*) as cnt FROM one_line_thanks').get().cnt;

    // 날짜 기반 일관된 인덱스 (1년 365일 순환)
    const now = new Date();
    const dayOfYear = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 1000 / 60 / 60 / 24);
    
    const wordId = (dayOfYear % (todayWordsCount || 1)) + 1;
    const thankId = (dayOfYear % (thanksCount || 1)) + 1;

    const tw = db.prepare('SELECT * FROM today_words WHERE id = ?').get(wordId);
    let todayVerse = null;
    if (tw) {
        const v = db.prepare('SELECT v.*, b.name as book_name FROM verses v JOIN books b ON v.book_id = b.id WHERE v.unit_code = ? AND v.jeol = ?').get(tw.unit_code, tw.jeol_start);
        todayVerse = v;
    }

    const thank = db.prepare('SELECT * FROM one_line_thanks WHERE id = ?').get(thankId);

    return {
        dayOfYear,
        today_word: todayVerse,
        one_line_thanks: thank ? thank.text : '항상 기뻐하라 쉬지 말고 기도하라 범사에 감사하라'
    };
}

// 7. 통독 계획표 조회
function getReadingPlan(day) {
    const targetDay = parseInt(day, 10) || 1;
    const plan = db.prepare('SELECT * FROM reading_plans WHERE day = ?').get(targetDay);
    
    // 전체 통독 통계
    const totalChapters = 1189;
    const readChapters = db.prepare('SELECT count(*) as cnt FROM user_reading_log').get().cnt;

    return {
        day: targetDay,
        plan,
        progress: {
            total: totalChapters,
            read: readChapters,
            percentage: Math.round((readChapters / totalChapters) * 1000) / 10
        }
    };
}

// 8. 사용자 데이터 관리 (북마크, 형광펜, 메모, 통독 토글)
function setHighlight(unitCode, jeol, color) {
    const id = `${unitCode}_${jeol}`;
    if (!color || color === 'none') {
        db.prepare('DELETE FROM user_highlights WHERE unit_code = ? AND jeol = ?').run(unitCode, jeol);
        return { success: true, action: 'deleted' };
    } else {
        db.prepare(`
            INSERT INTO user_highlights (id, unit_code, jeol, color, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET color = excluded.color, updated_at = CURRENT_TIMESTAMP
        `).run(id, unitCode, jeol, color);
        return { success: true, action: 'saved', color };
    }
}

function toggleBookmark(unitCode, jeol, label = '') {
    const id = `${unitCode}_${jeol}`;
    const existing = db.prepare('SELECT * FROM user_bookmarks WHERE id = ?').get(id);
    if (existing) {
        db.prepare('DELETE FROM user_bookmarks WHERE id = ?').run(id);
        return { bookmarked: false };
    } else {
        db.prepare('INSERT INTO user_bookmarks (id, unit_code, jeol, label) VALUES (?, ?, ?, ?)').run(id, unitCode, jeol, label);
        return { bookmarked: true };
    }
}

function getAllBookmarks() {
    return db.prepare(`
        SELECT b.id, b.unit_code, b.jeol, b.label, b.created_at,
               bk.name as book_name, v.chapter, v.phrase_rv as text
        FROM user_bookmarks b
        JOIN verses v ON b.unit_code = v.unit_code AND b.jeol = v.jeol
        JOIN books bk ON v.book_id = bk.id
        ORDER BY b.created_at DESC
    `).all();
}

function saveNote(unitCode, jeol, content) {
    const id = `${unitCode}_${jeol}`;
    if (!content || !content.trim()) {
        db.prepare('DELETE FROM user_notes WHERE id = ?').run(id);
        return { success: true, action: 'deleted' };
    }
    db.prepare(`
        INSERT INTO user_notes (id, unit_code, jeol, content, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET content = excluded.content, updated_at = CURRENT_TIMESTAMP
    `).run(id, unitCode, jeol, content.trim());
    return { success: true, action: 'saved' };
}

function getAllNotes() {
    return db.prepare(`
        SELECT n.id, n.unit_code, n.jeol, n.content, n.updated_at,
               bk.name as book_name, v.chapter, v.phrase_rv as text
        FROM user_notes n
        JOIN verses v ON n.unit_code = v.unit_code AND n.jeol = v.jeol
        JOIN books bk ON v.book_id = bk.id
        ORDER BY n.updated_at DESC
    `).all();
}

function toggleReadingStatus(unitCode) {
    const existing = db.prepare('SELECT * FROM user_reading_log WHERE unit_code = ?').get(unitCode);
    if (existing) {
        db.prepare('DELETE FROM user_reading_log WHERE unit_code = ?').run(unitCode);
        return { is_read: false };
    } else {
        db.prepare('INSERT INTO user_reading_log (unit_code, read_count) VALUES (?, 1)').run(unitCode);
        return { is_read: true };
    }
}

function getReadingStats() {
    const readList = db.prepare('SELECT unit_code, read_count, last_read_at FROM user_reading_log').all();
    const readMap = {};
    readList.forEach(r => { readMap[r.unit_code] = r; });

    const totalChapters = 1189;
    const otTotal = 929;
    const ntTotal = 260;

    let otRead = 0;
    let ntRead = 0;

    readList.forEach(r => {
        const bookId = Math.floor(r.unit_code / 1000);
        if (bookId <= 39) otRead++;
        else ntRead++;
    });

    return {
        total: totalChapters,
        read_total: readList.length,
        percentage: Math.round((readList.length / totalChapters) * 1000) / 10,
        ot: { total: otTotal, read: otRead, percentage: Math.round((otRead / otTotal) * 1000) / 10 },
        nt: { total: ntTotal, read: ntRead, percentage: Math.round((ntRead / ntTotal) * 1000) / 10 },
        read_chapters: readMap
    };
}

// 12. 성경 인물/지명 사전 조회
function getDictionaryVerse(unitCode, jeol) {
    const verse = db.prepare('SELECT phrase_rv, phrase_ko, phrase_nv FROM verses WHERE unit_code = ? AND jeol = ?').get(unitCode, jeol);
    if (!verse) return [];

    const rawRv = verse.phrase_rv || '';
    const rawKo = verse.phrase_ko || '';
    const txtNv = (verse.phrase_nv || '').toLowerCase();

    // 1. 태깅된 고유명사 (<b>...</b>) 추출
    const bNames = Array.from(new Set([...(rawRv.match(/<b>([^<]+)<\/b>/g) || []), ...(rawKo.match(/<b>([^<]+)<\/b>/g) || [])]))
        .map(s => s.replace(/<\/?b>/g, '').trim())
        .filter(Boolean);

    const matchedMap = new Map();
    if (bNames.length > 0) {
        const placeholders = bNames.map(() => '?').join(',');
        const rows = db.prepare(`SELECT * FROM bible_dictionary WHERE name_ko IN (${placeholders}) ORDER BY id ASC`).all(...bNames);
        rows.forEach(r => matchedMap.set(r.id, r));
    }

    // 2. 주요 인물, 별칭, 도량형 및 성경 단어 보정
    const coreRows = db.prepare(`SELECT * FROM bible_dictionary WHERE category = '단어' OR aliases != '' OR id <= 80 ORDER BY id ASC`).all();
    const combKo = `${rawRv} ${rawKo}`;

    coreRows.forEach(entry => {
        if (matchedMap.has(entry.id)) return;
        let isMatch = false;
        if (entry.name_ko && combKo.includes(entry.name_ko)) isMatch = true;
        if (!isMatch && entry.aliases) {
            const list = entry.aliases.split(',').map(s => s.trim()).filter(Boolean);
            for (const a of list) {
                if (a.length >= 2 && combKo.includes(a)) {
                    isMatch = true;
                    break;
                }
            }
        }
        if (!isMatch && entry.name_en && entry.name_en.length >= 3 && txtNv.includes(entry.name_en.toLowerCase())) {
            isMatch = true;
        }
        if (isMatch) matchedMap.set(entry.id, entry);
    });

    return Array.from(matchedMap.values());
}

function searchDictionary(q, category, limit = 60) {
    let sql = 'SELECT * FROM bible_dictionary WHERE 1=1';
    const params = [];
    if (category && (category === '인명' || category === '인물' || category === '지명' || category === '단어')) {
        const catVal = category === '인물' ? '인명' : category;
        sql += ' AND category = ?';
        params.push(catVal);
    }
    if (q) {
        sql += ' AND (name_ko LIKE ? OR name_en LIKE ? OR aliases LIKE ? OR meaning LIKE ? OR summary LIKE ?)';
        const p = `%${q}%`;
        params.push(p, p, p, p, p);
    }
    sql += ' ORDER BY id ASC LIMIT ?';
    params.push(limit);
    return db.prepare(sql).all(...params);
}

function getDictionaryEntry(id) {
    return db.prepare('SELECT * FROM bible_dictionary WHERE id = ?').get(id);
}

module.exports = {
    getBooks,
    getBook,
    getChapterVerses,
    getVerseDetails,
    getStrongInfo,
    searchVerses,
    getTodayContent,
    getReadingPlan,
    setHighlight,
    toggleBookmark,
    getAllBookmarks,
    saveNote,
    getAllNotes,
    toggleReadingStatus,
    getReadingStats,
    getDictionaryVerse,
    searchDictionary,
    getDictionaryEntry
};
