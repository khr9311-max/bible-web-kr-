/**
 * 성경 통독 플래너 및 진도표 모듈 (reading_tracker.js)
 */

window.BibleReading = {
    init() {},

    async loadData() {
        await Promise.all([
            this.loadStats(),
            this.loadMCheynePlan()
        ]);
    },

    async loadStats() {
        try {
            const stats = await window.BibleApp.fetchApi('/reading-stats');
            
            // 통계 텍스트 업데이트
            document.getElementById('total-percent-text').textContent = `${stats.percentage}%`;
            document.getElementById('stat-read-total').textContent = `${stats.read_total} / ${stats.total}장`;
            document.getElementById('stat-ot-prog').textContent = `${stats.ot.percentage}% (${stats.ot.read}/${stats.ot.total}장)`;
            document.getElementById('stat-nt-prog').textContent = `${stats.nt.percentage}% (${stats.nt.read}/${stats.nt.total}장)`;

            // 도넛 차트 CSS 프로퍼티 주입
            const donut = document.getElementById('donut-progress-display');
            if (donut) {
                donut.style.setProperty('--percent', stats.percentage);
            }
        } catch (e) {
            console.error('Failed to load reading stats:', e);
        }
    },

    async loadMCheynePlan() {
        const list = document.getElementById('mcheyne-chapters-list');
        if (!list) return;

        // 현재 연중 일자 (1~365)
        const now = new Date();
        const start = new Date(now.getFullYear(), 0, 0);
        const diff = now - start;
        const oneDay = 1000 * 60 * 60 * 24;
        const dayOfYear = Math.floor(diff / oneDay);

        const badge = document.getElementById('mcheyne-day-badge');
        if (badge) badge.textContent = `Day ${dayOfYear}`;

        try {
            const planData = await window.BibleApp.fetchApi(`/reading-plan?day=${dayOfYear}`);
            const p = planData.plan;
            if (!p) return;

            const targets = [
                { tag: '구약 제1', unit: p.ot_1 },
                { tag: '구약 제2', unit: p.ot_2 },
                { tag: '신약', unit: p.nt_1 },
                { tag: '시편/시가', unit: p.psalm }
            ];

            let html = '';
            targets.forEach(t => {
                const uCode = parseInt(t.unit, 10);
                const bId = Math.floor(uCode / 1000);
                const ch = uCode % 1000;
                const book = window.BibleApp.state.books.find(b => b.id === bId) || { name: '창세기' };

                html += `
                    <div class="mcheyne-card" data-unit="${uCode}">
                        <div class="mcheyne-tag">${t.tag}</div>
                        <div class="mcheyne-ref">${book.name} ${ch}장</div>
                    </div>
                `;
            });

            list.innerHTML = html;

            list.querySelectorAll('.mcheyne-card').forEach(card => {
                card.addEventListener('click', () => {
                    const u = card.dataset.unit;
                    window.BibleApp.navigateTo(u);
                });
            });
        } catch (e) {
            console.error('Failed to load MCheyne plan:', e);
        }
    }
};
