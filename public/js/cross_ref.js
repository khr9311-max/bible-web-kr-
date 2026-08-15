/**
 * 스마트 관주 및 상호 참조(Cross-Reference) 모듈 (cross_ref.js)
 */

window.BibleCrossRef = {
    init() {
        // 사이드 패널 닫기 버튼 이벤트 바인딩
        document.getElementById('btn-close-side-panel')?.addEventListener('click', () => {
            this.closeSidePanel();
        });

        // 탭 버튼 바인딩
        document.getElementById('tab-btn-crossref')?.addEventListener('click', () => {
            window.BibleDictionary?.switchTab('crossref');
        });
    },

    openSidePanel(title = '스마트 관주 탐색') {
        window.BibleDictionary?.switchTab('crossref');
        const panel = document.getElementById('side-inspect-panel');
        const titleEl = document.getElementById('side-title-text');
        if (titleEl) titleEl.textContent = title;
        if (panel) {
            panel.classList.add('open');
            document.body.classList.add('side-panel-open');
        }
    },

    closeSidePanel() {
        const panel = document.getElementById('side-inspect-panel');
        if (panel) {
            panel.classList.remove('open');
            document.body.classList.remove('side-panel-open');
        }
    },

    async showForVerse(unitCode, jeol, targetMark = null) {
        this.openSidePanel('스마트 관주 탐색');
        const content = document.getElementById('side-view-crossref');
        if (!content) return;

        const bName = window.BibleApp?.state?.currentBookMeta?.name || '본문';
        const ch = window.BibleApp?.state?.currentChapter || 1;

        content.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>${bName} ${ch}:${jeol}절 관주 참조 구절을 불러오는 중입니다...</p>
            </div>
        `;

        try {
            const data = await window.BibleApp.fetchApi(`/verse/${unitCode}/${jeol}`);
            this.renderCrossReferences(data, jeol, targetMark);
        } catch (e) {
            console.error('Failed to load cross references:', e);
            content.innerHTML = `
                <div class="panel-empty-state">
                    <p style="color:var(--accent-rose);">관주 데이터를 불러오지 못했습니다.</p>
                </div>
            `;
        }
    },

    renderCrossReferences(verseData, jeol, targetMark = null) {
        const content = document.getElementById('side-view-crossref');
        if (!content) return;

        const bName = window.BibleApp?.state?.currentBookMeta?.name || '본문';
        const ch = window.BibleApp?.state?.currentChapter || 1;

        if (!verseData || !verseData.cross_references || verseData.cross_references.length === 0) {
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
                <strong style="color:var(--brand-primary); font-size:15px;">${bName} ${ch}:${jeol} 관련 관주·각주</strong>
                <p style="font-size:12.5px; color:var(--text-muted); margin-top:4px;">기호나 구절을 클릭하면 연관 말씀을 바로 확인하실 수 있습니다.</p>
            </div>
        `;

        verseData.cross_references.forEach((cr, idx) => {
            const isTarget = targetMark && (cr.mark === targetMark || targetMark.includes(cr.mark) || cr.mark.includes(targetMark));
            const highlightClass = isTarget ? 'crossref-target-highlight' : '';
            const markBadge = cr.mark ? `<span class="crossref-mark-badge ${isTarget ? 'active-badge' : ''}">[${cr.mark}]</span>` : '';
            const verName = (cr.version || 'RV').toUpperCase();
            const explains = cr.explains || '';
            const links = cr.link_ids ? cr.link_ids.split(';').filter(Boolean) : [];

            // 링크 칩 생성 (클릭 시 해당 연관 구절 모달 즉시 오픈)
            let linkChipsHtml = '';
            links.forEach(l => {
                const cleanRef = l.trim();
                if (cleanRef) {
                    linkChipsHtml += `<button class="crossref-link-chip" data-ref="${cleanRef}" title="${cleanRef} 말씀 보기">${cleanRef}</button>`;
                }
            });

            html += `
                <div class="crossref-entry-card ${highlightClass}" id="crossref-card-${idx}">
                    <div class="crossref-entry-header">
                        ${markBadge}
                        <span class="crossref-version-label">${verName} ${cr.kind === 'note' ? '각주' : '관주'}</span>
                    </div>
                    <div class="crossref-explains-text">${explains}</div>
                    ${linkChipsHtml ? `<div class="crossref-chips-wrap">${linkChipsHtml}</div>` : ''}
                </div>
            `;
        });

        content.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();

        // 칩 클릭 시 연관 말씀 팝업 모달 연동
        content.querySelectorAll('.crossref-link-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                const ref = btn.dataset.ref;
                if (ref) {
                    window.BibleReader?.openParallelModal(ref);
                }
            });
        });

        // 만약 타겟 기호가 있으면 해당 카드로 스크롤
        if (targetMark) {
            setTimeout(() => {
                const targetCard = content.querySelector('.crossref-target-highlight');
                if (targetCard) {
                    targetCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }, 100);
        }
    }
};

