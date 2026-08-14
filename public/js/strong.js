/**
 * 원어 성경 분해 및 스트롱 코드 사전 모듈 (strong.js)
 */

window.BibleStrong = {
    isOpen: false,

    init() {
        document.getElementById('btn-close-side-panel')?.addEventListener('click', () => {
            this.closeSidePanel();
        });
    },

    toggleSidePanel() {
        if (this.isOpen) {
            this.closeSidePanel();
        } else {
            const currentJeol = window.BibleApp.state.currentJeol || 1;
            this.showForVerse(window.BibleApp.state.currentUnitCode, currentJeol);
        }
    },

    openSidePanel(title = '원어 스트롱 분해') {
        const panel = document.getElementById('side-inspect-panel');
        const titleEl = document.getElementById('side-title-text');
        if (titleEl) titleEl.textContent = title;
        if (panel) {
            panel.classList.add('open');
            this.isOpen = true;
        }
    },

    closeSidePanel() {
        const panel = document.getElementById('side-inspect-panel');
        if (panel) {
            panel.classList.remove('open');
            this.isOpen = false;
        }
    },

    async showForVerse(unitCode, jeol) {
        this.openSidePanel('원어 스트롱 분해');
        await this.loadVerseStrongs(unitCode, jeol);
    },

    async loadVerseStrongs(unitCode, jeol) {
        const content = document.getElementById('side-panel-content');
        if (!content) return;

        content.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>원어 스트롱 데이터를 분석 중입니다...</p>
            </div>
        `;

        try {
            const data = await window.BibleApp.fetchApi(`/verse/${unitCode}/${jeol}`);
            this.renderStrongCards(data, jeol);
        } catch (e) {
            content.innerHTML = `
                <div class="panel-empty-state">
                    <p style="color:var(--accent-rose);">원어 데이터를 불러오지 못했습니다.</p>
                </div>
            `;
        }
    },

    renderStrongCards(verseData, jeol) {
        const content = document.getElementById('side-panel-content');
        if (!content) return;

        const bName = window.BibleApp.state.currentBookMeta.name;
        const ch = window.BibleApp.state.currentChapter;

        if (!verseData.strongs || verseData.strongs.length === 0) {
            content.innerHTML = `
                <div class="panel-empty-state">
                    <i data-lucide="info"></i>
                    <p>${bName} ${ch}:${jeol} 구절에는<br>등록된 원어 스트롱 분해 데이터가 없습니다.</p>
                </div>
            `;
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        let html = `
            <div style="margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--border-subtle);">
                <strong style="color:var(--brand-primary); font-size:15px;">${bName} ${ch}:${jeol} 원어 어휘 분해</strong>
                <p style="font-size:13px; color:var(--text-secondary); margin-top:4px;">단어별 히브리어/헬라어 원어 사전 정의입니다.</p>
            </div>
        `;

        verseData.strongs.forEach(s => {
            if (!s.phrase || !s.phrase.trim()) return;
            const codeTag = s.strong_code ? `<span class="strong-card-code">${s.strong_code}</span>` : '';
            const original = s.original || s.phrase;
            const translit = s.translit ? `(${s.translit})` : '';
            const pronounce = s.pronounce ? `[${s.pronounce}]` : '';
            const meaning = s.meaning || '성경 원어 단어';
            const def = s.definition || `한국어 본문 매핑: '${s.phrase}'`;

            html += `
                <div class="strong-entry-card">
                    <div class="strong-card-head">
                        <span class="strong-card-original">${original}</span>
                        ${codeTag}
                    </div>
                    <div class="strong-card-translit">${translit} ${pronounce}</div>
                    <div class="strong-card-meaning">의미: ${meaning}</div>
                    <div class="strong-card-def">${def}</div>
                </div>
            `;
        });

        content.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();
    }
};
