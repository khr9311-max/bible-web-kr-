/**
 * 고속 성경 키워드 전문 검색 모듈 (search.js)
 */

window.BibleSearch = {
    debounceTimer: null,

    init() {
        this.setupEvents();
    },

    setupEvents() {
        const input = document.getElementById('search-input');
        const clearBtn = document.getElementById('btn-clear-search');

        input?.addEventListener('input', (e) => {
            const val = e.target.value;
            if (clearBtn) clearBtn.style.display = val.length > 0 ? 'block' : 'none';

            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.performSearch(val);
            }, 250);
        });

        clearBtn?.addEventListener('click', () => {
            if (input) {
                input.value = '';
                input.focus();
            }
            if (clearBtn) clearBtn.style.display = 'none';
            this.performSearch('');
        });

        // 빠른 추천 태그 클릭
        document.querySelectorAll('.search-tag').forEach(tag => {
            tag.addEventListener('click', () => {
                const kw = tag.dataset.kw;
                if (input) {
                    input.value = kw;
                    if (clearBtn) clearBtn.style.display = 'block';
                    this.performSearch(kw);
                }
            });
        });
    },

    async performSearch(query) {
        const list = document.getElementById('search-results-list');
        const statsEl = document.getElementById('search-stats-text');
        if (!list) return;

        if (!query || query.trim().length === 0) {
            list.innerHTML = `
                <div class="empty-search-state">
                    <i data-lucide="sparkles"></i>
                    <p>성경 66권 전체 31,105구절에서 즉시 검색됩니다.</p>
                </div>
            `;
            if (statsEl) statsEl.textContent = '검색어를 입력하세요.';
            if (window.lucide) window.lucide.createIcons();
            return;
        }

        list.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>'${query}' 검색 중...</p>
            </div>
        `;

        try {
            const ver = window.BibleApp.state.primaryVersion || 'rv';
            const data = await window.BibleApp.fetchApi(`/search?q=${encodeURIComponent(query)}&version=${ver}&limit=50`);

            if (statsEl) {
                statsEl.textContent = `총 ${data.total}개의 구절이 검색되었습니다. (상위 ${data.items.length}개 표시)`;
            }

            if (data.items.length === 0) {
                list.innerHTML = `
                    <div class="empty-search-state">
                        <i data-lucide="search-x"></i>
                        <p>'${query}'에 대한 검색 결과가 없습니다.<br>다른 단어로 검색해 보세요.</p>
                    </div>
                `;
                if (window.lucide) window.lucide.createIcons();
                return;
            }

            let html = '';
            data.items.forEach(item => {
                const cleanText = window.BibleReader.cleanVerseHtml(item.text);
                const highlighted = this.highlightKeyword(cleanText, query);

                html += `
                    <div class="search-result-item" data-unit="${item.unit_code}" data-jeol="${item.jeol}">
                        <div class="search-result-ref">${item.book_name} ${item.chapter}:${item.jeol}</div>
                        <div class="search-result-text">${highlighted}</div>
                    </div>
                `;
            });

            list.innerHTML = html;

            list.querySelectorAll('.search-result-item').forEach(el => {
                el.addEventListener('click', () => {
                    const unit = parseInt(el.dataset.unit, 10);
                    const jeol = parseInt(el.dataset.jeol, 10);
                    window.BibleApp.navigateTo(unit, jeol);
                });
            });
        } catch (e) {
            list.innerHTML = `
                <div class="empty-search-state">
                    <p style="color:var(--accent-rose);">검색 중 오류가 발생했습니다.</p>
                </div>
            `;
        }
    },

    highlightKeyword(text, keyword) {
        if (!keyword) return text;
        const reg = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(reg, '<span class="search-hl">$1</span>');
    }
};
