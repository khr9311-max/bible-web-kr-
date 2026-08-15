const express = require('express');
const cors = require('cors');
const path = require('path');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// 정적 파일 호스팅 (SPA 프론트엔드)
app.use(express.static(path.join(__dirname, '..', 'public')));

// 1. 성경 66권 메타데이터 API
app.get('/api/books', (req, res) => {
    try {
        const books = db.getBooks();
        res.json({ success: true, data: books });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

// 2. 장별 성경 본문 API (소제목 + 다역본 + 사용자 상태)
app.get('/api/chapter/:unitCode', (req, res) => {
    try {
        const unitCode = parseInt(req.params.unitCode, 10);
        if (!unitCode || isNaN(unitCode)) {
            return res.status(400).json({ success: false, error: 'Invalid unit code' });
        }
        const data = db.getChapterVerses(unitCode);
        res.json({ success: true, data });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

// 3. 특정 절 상세 (원어 스트롱 분해 + 관주 상호참조)
app.get('/api/verse/:unitCode/:jeol', (req, res) => {
    try {
        const unitCode = parseInt(req.params.unitCode, 10);
        const jeol = parseInt(req.params.jeol, 10);
        const data = db.getVerseDetails(unitCode, jeol);
        if (!data) return res.status(404).json({ success: false, error: 'Verse not found' });
        res.json({ success: true, data });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

// 4. 스트롱 코드 사전 API
app.get('/api/strong/:code', (req, res) => {
    try {
        const info = db.getStrongInfo(req.params.code);
        res.json({ success: true, data: info });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

// 5. 성경 키워드 검색 API
app.get('/api/search', (req, res) => {
    try {
        const query = req.query.q || '';
        const version = req.query.version || 'rv';
        const limit = parseInt(req.query.limit, 10) || 50;
        const offset = parseInt(req.query.offset, 10) || 0;

        const results = db.searchVerses(query, version, limit, offset);
        res.json({ success: true, data: results });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

// 6. 오늘의 말씀 & 한 줄 감사
app.get('/api/today', (req, res) => {
    try {
        const data = db.getTodayContent();
        res.json({ success: true, data });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

// 7. 통독 플래너 및 통계
app.get('/api/reading-plan', (req, res) => {
    try {
        const day = req.query.day || 1;
        const data = db.getReadingPlan(day);
        res.json({ success: true, data });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.get('/api/reading-stats', (req, res) => {
    try {
        const stats = db.getReadingStats();
        res.json({ success: true, data: stats });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

// 8. 사용자 데이터 관리 (형광펜, 북마크, 메모, 통독 토글)
app.post('/api/user/highlight', (req, res) => {
    try {
        const { unit_code, jeol, color } = req.body;
        const result = db.setHighlight(parseInt(unit_code, 10), parseInt(jeol, 10), color);
        res.json({ success: true, data: result });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.post('/api/user/bookmark', (req, res) => {
    try {
        const { unit_code, jeol, label } = req.body;
        const result = db.toggleBookmark(parseInt(unit_code, 10), parseInt(jeol, 10), label);
        res.json({ success: true, data: result });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.get('/api/user/bookmarks', (req, res) => {
    try {
        const list = db.getAllBookmarks();
        res.json({ success: true, data: list });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.post('/api/user/note', (req, res) => {
    try {
        const { unit_code, jeol, content } = req.body;
        const result = db.saveNote(parseInt(unit_code, 10), parseInt(jeol, 10), content);
        res.json({ success: true, data: result });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.get('/api/user/notes', (req, res) => {
    try {
        const list = db.getAllNotes();
        res.json({ success: true, data: list });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.post('/api/user/reading-toggle', (req, res) => {
    try {
        const { unit_code } = req.body;
        const result = db.toggleReadingStatus(parseInt(unit_code, 10));
        res.json({ success: true, data: result });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

// 성경 인물/지명 사전 API
app.get('/api/dictionary/verse', (req, res) => {
    try {
        const { unit_code, jeol } = req.query;
        const entries = db.getDictionaryVerse(parseInt(unit_code, 10) || 0, parseInt(jeol, 10) || 1);
        res.json({ success: true, data: { unit_code, jeol, count: entries.length, entries } });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.get('/api/dictionary/search', (req, res) => {
    try {
        const { q, category } = req.query;
        const entries = db.searchDictionary((q || '').trim(), (category || '').trim());
        res.json({ success: true, data: { query: q, category, count: entries.length, entries } });
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

app.get('/api/dictionary/entry/:id', (req, res) => {
    try {
        const entry = db.getDictionaryEntry(parseInt(req.params.id, 10));
        if (entry) {
            res.json({ success: true, data: entry });
        } else {
            res.status(404).json({ success: false, error: 'Entry not found' });
        }
    } catch (e) {
        res.status(500).json({ success: false, error: e.message });
    }
});

// SPA Fallback (새로고침 시 메인 페이지 서빙)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`====================================================`);
    console.log(` 📖 WordBible Full-Stack Server Running on:`);
    console.log(` 🌐 Local:   http://localhost:${PORT}`);
    console.log(`====================================================`);
});
