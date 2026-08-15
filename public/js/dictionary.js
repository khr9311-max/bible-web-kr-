/**
 * 성경 인물/지명 사전 모듈 (dictionary.js)
 * 개혁주의 / 복음주의 성경신학 기반 인물 및 지명 해설 & 구절 연계 사전
 */

window.BibleDictionary = {
    currentCategory: '', // '' (전체), '인물', '지명'
    searchDebounceTimer: null,
    cachedEntries: [],

    init() {
        this.bindEvents();
    },

    bindEvents() {
        // 사이드 패널 탭 전환 이벤트
        document.getElementById('tab-btn-crossref')?.addEventListener('click', () => {
            this.switchTab('crossref');
        });

        document.getElementById('tab-btn-dict')?.addEventListener('click', () => {
            this.switchTab('dict');
        });

        // 사전 검색창 이벤트
        const searchInput = document.getElementById('dict-search-input');
        searchInput?.addEventListener('input', (e) => {
            clearTimeout(this.searchDebounceTimer);
            const q = e.target.value.trim();
            this.searchDebounceTimer = setTimeout(() => {
                this.search(q, this.currentCategory);
            }, 250);
        });

        // 검색창 초기화 버튼
        document.getElementById('btn-clear-dict-search')?.addEventListener('click', () => {
            if (searchInput) {
                searchInput.value = '';
                searchInput.focus();
            }
            this.search('', this.currentCategory);
        });

        // 카테고리 필터 칩 클릭
        document.querySelectorAll('.dict-cat-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                document.querySelectorAll('.dict-cat-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.currentCategory = chip.dataset.category || '';
                const q = document.getElementById('dict-search-input')?.value.trim() || '';
                this.search(q, this.currentCategory);
            });
        });
    },

    switchTab(tabName) {
        const btnCross = document.getElementById('tab-btn-crossref');
        const btnDict = document.getElementById('tab-btn-dict');
        const viewCross = document.getElementById('side-view-crossref');
        const viewDict = document.getElementById('side-view-dict');

        if (tabName === 'dict') {
            btnCross?.classList.remove('active');
            btnDict?.classList.add('active');
            if (viewCross) viewCross.style.display = 'none';
            if (viewDict) viewDict.style.display = 'flex';
        } else {
            btnDict?.classList.remove('active');
            btnCross?.classList.add('active');
            if (viewDict) viewDict.style.display = 'none';
            if (viewCross) viewCross.style.display = 'block';
        }
        if (window.lucide) window.lucide.createIcons();
    },

    openSidePanel() {
        const panel = document.getElementById('side-inspect-panel');
        if (panel) {
            panel.classList.add('open');
            document.body.classList.add('side-panel-open');
        }
    },

    // 1. 특정 구절 선택 시 인물/지명 자동 감지 조회
    async showForVerse(unitCode, jeol) {
        this.openSidePanel();
        this.switchTab('dict');

        const container = document.getElementById('dict-results-container');
        if (!container) return;

        const bName = window.BibleApp?.state?.currentBookMeta?.name || '본문';
        const ch = window.BibleApp?.state?.currentChapter || 1;

        // 검색창 리셋
        const searchInput = document.getElementById('dict-search-input');
        if (searchInput) searchInput.value = '';

        container.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>${bName} ${ch}:${jeol} 구절의 인물·지명을 분석 중입니다...</p>
            </div>
        `;

        try {
            const data = await window.BibleApp.fetchApi(`/dictionary/verse?unit_code=${unitCode}&jeol=${jeol}`);
            this.renderVerseEntities(data, bName, ch, jeol);
        } catch (e) {
            console.error('Failed to load verse dictionary:', e);
            container.innerHTML = `
                <div class="panel-empty-state">
                    <p style="color:var(--accent-rose);">사전 데이터를 불러오지 못했습니다.</p>
                </div>
            `;
        }
    },

    renderVerseEntities(data, bName, ch, jeol) {
        const container = document.getElementById('dict-results-container');
        if (!container) return;

        if (!data || !data.entries || data.entries.length === 0) {
            container.innerHTML = `
                <div class="dict-verse-header">
                    <div class="dict-verse-title">
                        <span class="dict-ref-badge">${bName} ${ch}:${jeol}</span>
                        <span>언급된 인물 / 지명</span>
                    </div>
                </div>
                <div class="panel-empty-state dict-empty-state">
                    <i data-lucide="info"></i>
                    <p>해당 구절에서 직접 언급된 주요 인물/지명이 없습니다.</p>
                    <p class="dict-hint-text">위 검색창에서 찾으시는 성경 인물이나 지명을 직접 검색해보세요!</p>
                </div>
                <div class="dict-popular-section">
                    <span class="dict-section-label">🌟 주요 성경 인물 / 지명 바로가기</span>
                    <div class="dict-quick-chips">
                        <button class="dict-quick-chip" data-query="아브라함">아브라함</button>
                        <button class="dict-quick-chip" data-query="모세">모세</button>
                        <button class="dict-quick-chip" data-query="다윗">다윗</button>
                        <button class="dict-quick-chip" data-query="예수 그리스도">예수 그리스도</button>
                        <button class="dict-quick-chip" data-query="베드로">베드로</button>
                        <button class="dict-quick-chip" data-query="바울">바울</button>
                        <button class="dict-quick-chip" data-query="예루살렘">예루살렘</button>
                        <button class="dict-quick-chip" data-query="갈릴리">갈릴리</button>
                        <button class="dict-quick-chip" data-query="베들레헴">베들레헴</button>
                    </div>
                </div>
            `;
            this.bindQuickChips();
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        let html = `
            <div class="dict-verse-header">
                <div class="dict-verse-title">
                    <span class="dict-ref-badge">${bName} ${ch}:${jeol}</span>
                    <span>관련 인물 · 지명 <strong>(${data.entries.length}개)</strong></span>
                </div>
                <p class="dict-verse-desc">구절에 등장하는 인물과 지명의 배경 및 구속사적 의미입니다.</p>
            </div>
            <div class="dict-cards-list">
        `;

        data.entries.forEach(entry => {
            html += this.buildEntryCardHtml(entry);
        });

        html += `</div>`;
        container.innerHTML = html;
        this.bindCardInteractions();
        if (window.lucide) window.lucide.createIcons();
    },

    // 2. 키워드 검색
    async search(query, category = '') {
        const container = document.getElementById('dict-results-container');
        if (!container) return;

        if (!query && !category) {
            // 기본 전체 목록 조회
            try {
                const data = await window.BibleApp.fetchApi(`/dictionary/search?limit=30`);
                this.renderSearchResults(data, '');
            } catch (e) {
                console.error(e);
            }
            return;
        }

        container.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>'${query || category}' 검색 중...</p>
            </div>
        `;

        try {
            const data = await window.BibleApp.fetchApi(`/dictionary/search?q=${encodeURIComponent(query)}&category=${encodeURIComponent(category)}`);
            this.renderSearchResults(data, query);
        } catch (e) {
            console.error('Search dictionary failed:', e);
            container.innerHTML = `
                <div class="panel-empty-state">
                    <p style="color:var(--accent-rose);">검색 결과를 불러오지 못했습니다.</p>
                </div>
            `;
        }
    },

    renderSearchResults(data, query) {
        const container = document.getElementById('dict-results-container');
        if (!container) return;

        if (!data || !data.entries || data.entries.length === 0) {
            container.innerHTML = `
                <div class="panel-empty-state">
                    <i data-lucide="search-x"></i>
                    <p>'${query}'에 대한 검색 결과가 없습니다.</p>
                    <p class="dict-hint-text">다른 인물명이나 지명으로 검색해보세요.</p>
                </div>
            `;
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        let html = `
            <div class="dict-results-header">
                <span>검색 결과 <strong>${data.entries.length}개</strong></span>
            </div>
            <div class="dict-cards-list">
        `;

        data.entries.forEach(entry => {
            html += this.buildEntryCardHtml(entry, query);
        });

        html += `</div>`;
        container.innerHTML = html;
        this.bindCardInteractions();
        if (window.lucide) window.lucide.createIcons();
    },

    buildEntryCardHtml(entry, highlightQuery = '') {
        const isPerson = entry.category === '인물';
        const catBadgeClass = isPerson ? 'badge-person' : 'badge-place';
        const catIcon = isPerson ? '👤' : '📍';

        // 대표 관련 구절 링크 칩 생성
        let keyVerseChips = '';
        if (entry.key_verses) {
            const refs = entry.key_verses.split(';').map(r => r.trim()).filter(Boolean);
            refs.forEach(ref => {
                keyVerseChips += `<button class="dict-ref-chip stitle-ref-link" data-ref="${ref}" title="${ref} 말씀 바로보기">${ref}</button>`;
            });
        }

        const meaningHtml = entry.meaning 
            ? `<div class="dict-meaning-tag"><span class="dict-label">이름의 뜻:</span> <strong>${entry.meaning}</strong></div>` 
            : '';

        const origHtml = entry.name_original 
            ? `<span class="dict-orig-tag">${entry.name_original}</span>` 
            : '';

        const engHtml = entry.name_en 
            ? `<span class="dict-eng-name">${entry.name_en}</span>` 
            : '';

        return `
            <div class="dict-entry-card" id="dict-entry-${entry.id}">
                <div class="dict-card-top">
                    <div class="dict-name-wrap">
                        <span class="dict-cat-badge ${catBadgeClass}">${catIcon} ${entry.category}</span>
                        <h4 class="dict-entry-name">${entry.name_ko}</h4>
                        ${engHtml}
                        ${origHtml}
                    </div>
                </div>
                
                ${meaningHtml}

                <div class="dict-card-summary">
                    <p>${entry.summary}</p>
                </div>

                ${entry.events ? `
                    <div class="dict-card-events">
                        <div class="dict-events-title"><i data-lucide="history"></i> 주요 행적 및 사건</div>
                        <p>${entry.events}</p>
                    </div>
                ` : ''}

                ${keyVerseChips ? `
                    <div class="dict-card-verses">
                        <div class="dict-verses-title"><i data-lucide="book-open"></i> 관련 대표 구절</div>
                        <div class="dict-ref-chips-wrap">${keyVerseChips}</div>
                    </div>
                ` : ''}
            </div>
        `;
    },

    bindCardInteractions() {
        // 구절 칩 클릭 시 해당 말씀 바로보기 모달 오픈
        document.querySelectorAll('.dict-ref-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                const ref = btn.dataset.ref;
                if (ref && window.BibleReader?.lookupParallelRef) {
                    window.BibleReader.lookupParallelRef(ref);
                }
            });
        });
    },

    bindQuickChips() {
        document.querySelectorAll('.dict-quick-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                const q = btn.dataset.query;
                const searchInput = document.getElementById('dict-search-input');
                if (searchInput) searchInput.value = q;
                this.search(q, this.currentCategory);
            });
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.BibleDictionary.init();
});
