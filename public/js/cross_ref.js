/**
 * 스마트 관주 및 상호 참조(Cross-Reference) 모듈 (cross_ref.js)
 */

window.BibleCrossRef = {
    init() {},

    async showForVerse(unitCode, jeol) {
        window.BibleStrong?.openSidePanel('스마트 관주 상호참조');
        const content = document.getElementById('side-panel-content');
        if (!content) return;

        content.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>관주 참조 구절을 불러오는 중입니다...</p>
            </div>
        `;

        try {
            const data = await window.BibleApp.fetchApi(`/verse/${unitCode}/${jeol}`);
            this.renderCrossReferences(data, jeol);
        } catch (e) {
            content.innerHTML = `
                <div class="panel-empty-state">
                    <p style="color:var(--accent-rose);">관주 데이터를 불러오지 못했습니다.</p>
                </div>
            `;
        }
    },

    renderCrossReferences(verseData, jeol) {
        const content = document.getElementById('side-panel-content');
        if (!content) return;

        const bName = window.BibleApp.state.currentBookMeta.name;
        const ch = window.BibleApp.state.currentChapter;

        if (!verseData.cross_references || verseData.cross_references.length === 0) {
            content.innerHTML = `
                <div class="panel-empty-state">
                    <i data-lucide="git-fork"></i>
                    <p>${bName} ${ch}:${jeol} 구절에는<br>등록된 관주 참조 구절이 없습니다.</p>
                </div>
            `;
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        let html = `
            <div style="margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--border-subtle);">
                <strong style="color:var(--brand-primary); font-size:15px;">${bName} ${ch}:${jeol} 관련 관주</strong>
                <p style="font-size:13px; color:var(--text-secondary); margin-top:4px;">상호 참조된 성경 구절 목록입니다.</p>
            </div>
        `;

        verseData.cross_references.forEach(cr => {
            const markBadge = cr.mark ? `<span style="font-weight:700; color:var(--brand-primary); margin-right:6px;">[${cr.mark}]</span>` : '';
            const explains = cr.explains || '참조 성경';
            const links = cr.link_ids ? cr.link_ids.split(';').filter(Boolean) : [];

            let linkChipsHtml = '';
            links.forEach(l => {
                linkChipsHtml += `<span class="search-tag" style="display:inline-block; margin:2px 4px 2px 0;">${l}</span>`;
            });

            html += `
                <div class="crossref-entry-item">
                    <div class="crossref-ref-tag">${markBadge} ${cr.version.toUpperCase()} 관주</div>
                    <div class="crossref-text">${explains}</div>
                    ${linkChipsHtml ? `<div style="margin-top:8px;">${linkChipsHtml}</div>` : ''}
                </div>
            `;
        });

        content.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();
    }
};
