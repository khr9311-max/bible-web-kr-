/**
 * 성경 뷰어 및 렌더링 모듈 (reader.js)
 * 다역본 대조 뷰, 절 선택 툴바, 형광펜, 북마크, 메모, TTS 음성 낭독 싱크
 */

window.BibleReader = {
    chapterData: null,
    selectedVerse: null,
    tts: {
        synth: window.speechSynthesis,
        utterance: null,
        isPlaying: false,
        currentVerseIndex: 0,
        rate: 1.0,
        voices: []
    },

    init() {
        this.setupToolbarEvents();
        this.setupTtsEvents();
        this.setupNoteModal();
        this.loadChapter(window.BibleApp.state.currentUnitCode, window.BibleApp.state.currentJeol);
    },

    async reload() {
        await this.loadChapter(window.BibleApp.state.currentUnitCode, this.selectedVerse?.jeol || 1);
    },

    // 1. 장별 성경 말씀 로드 및 렌더링
    async loadChapter(unitCode, targetJeol = 1) {
        const viewport = document.getElementById('verses-viewport');
        if (!viewport) return;

        viewport.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>성경 말씀을 불러오는 중입니다...</p>
            </div>
        `;

        try {
            const data = await window.BibleApp.fetchApi(`/chapter/${unitCode}`);
            this.chapterData = data;
            this.renderVerses(data);

            // 통독 버튼 상태 갱신
            this.updateReadButtonState(data.is_read);

            // 목표 절로 스크롤
            if (targetJeol) {
                setTimeout(() => {
                    this.scrollToVerse(targetJeol);
                }, 100);
            }
        } catch (e) {
            viewport.innerHTML = `
                <div class="loading-state">
                    <p style="color:var(--accent-rose);">말씀을 불러오지 못했습니다. 다시 시도해 주세요.</p>
                </div>
            `;
        }
    },

    // 2. 본문 렌더링 (단일 뷰 or 대조 뷰)
    renderVerses(data) {
        const viewport = document.getElementById('verses-viewport');
        if (!viewport) return;

        const priVer = window.BibleApp.state.primaryVersion;
        const compVer = window.BibleApp.state.compareVersion;
        const isCompare = window.BibleApp.state.isCompareMode;

        const priCol = `phrase_${priVer}`;
        const compCol = `phrase_${compVer}`;

        let html = '';
        const engVers = ['nv', 'nt', 'es', 'nb', 'kj'];
        const bookMeta = window.BibleApp?.state?.currentBookMeta || { name: '창세기', eng_name: 'Genesis' };
        const currentChap = window.BibleApp?.state?.currentChapter || 1;

        const priBookName = engVers.includes(priVer) ? `${bookMeta.eng_name || bookMeta.name} ${currentChap}` : `${bookMeta.name} ${currentChap}장`;
        const compBookName = engVers.includes(compVer) ? `${bookMeta.eng_name || bookMeta.name} ${currentChap}` : `${bookMeta.name} ${currentChap}장`;

        if (isCompare) {
            // 대조 모드 (2열 분할)
            html += `
                <div class="compare-col-header">
                    <span>${this.getVersionName(priVer)} — ${priBookName}</span>
                    <span>${this.getVersionName(compVer)} — ${compBookName}</span>
                </div>
                <div class="compare-mode-wrap">
            `;

            data.verses.forEach(v => {
                const hlClass = v.highlight ? `hl-${v.highlight}` : '';
                const priStitle = v[`stitle_${priVer}`] || (priVer === 'rv' ? v.stitle_rv : '');
                const compStitle = v[`stitle_${compVer}`] || (compVer === 'rv' ? v.stitle_rv : '');

                let stitleRowHtml = '';
                if (priStitle || compStitle) {
                    stitleRowHtml = `
                        <div class="compare-stitle-row">
                            <div class="compare-pri-stitle">${priStitle ? this.formatStitle(priStitle) : ''}</div>
                            <div class="compare-sec-stitle">${compStitle ? this.formatStitle(compStitle) : ''}</div>
                        </div>
                    `;
                }

                const priText = this.cleanVerseHtml(v[priCol] || v.phrase_rv || '');
                const compText = this.cleanVerseHtml(v[compCol] || '');

                const bookmarkBadge = v.bookmark ? `<i data-lucide="bookmark" class="verse-badge-icon icon-bookmark-tag"></i>` : '';
                const noteBadge = v.note ? `<i data-lucide="edit-3" class="verse-badge-icon icon-note-tag"></i>` : '';

                html += `
                    ${stitleRowHtml}
                    <div class="verse-compare-row ${hlClass}" id="verse-${v.jeol}" data-jeol="${v.jeol}" data-unit="${v.unit_code}">
                        <div class="compare-pri-col">
                            <span class="verse-num">${v.jeol}</span>
                            <span class="verse-text">${priText}</span>
                            ${bookmarkBadge}
                            ${noteBadge}
                        </div>
                        <div class="compare-sec-col">
                            <span class="verse-text compare-sec-text">${compText}</span>
                        </div>
                    </div>
                `;
            });

            html += `</div>`;
        } else {
            // 단일 뷰어 모드
            data.verses.forEach(v => {
                const hlClass = v.highlight ? `hl-${v.highlight}` : '';
                const priStitle = v[`stitle_${priVer}`] || v.stitle_rv || '';
                const stitleHtml = priStitle ? `<div class="section-stitle">${this.formatStitle(priStitle)}</div>` : '';
                const verseText = this.cleanVerseHtml(v[priCol] || v.phrase_rv || '');

                const bookmarkBadge = v.bookmark ? `<i data-lucide="bookmark" class="verse-badge-icon icon-bookmark-tag"></i>` : '';
                const noteBadge = v.note ? `<i data-lucide="edit-3" class="verse-badge-icon icon-note-tag"></i>` : '';

                html += `
                    ${stitleHtml}
                    <div class="verse-item ${hlClass}" id="verse-${v.jeol}" data-jeol="${v.jeol}" data-unit="${v.unit_code}">
                        <span class="verse-num">${v.jeol}</span>
                        <span class="verse-text">${verseText}</span>
                        ${bookmarkBadge}
                        ${noteBadge}
                    </div>
                `;
            });
        }

        viewport.innerHTML = html;
        viewport.classList.toggle('mode-paragraph', window.BibleApp.state.viewMode === 'paragraph');

        if (window.lucide) window.lucide.createIcons();

        // 절 클릭 이벤트 바인딩
        this.bindVerseClickEvents();
    },

    formatStitle(raw) {
        if (!raw) return '';
        
        // 1. <a ... href='lnk.spc?REF'>TEXT</a> 패턴을 순수 텍스트 링크로 변환
        let formatted = raw.replace(/<a\s+[^>]*href=['"]lnk\.spc\?([^'"]+)['"][^>]*>([\s\S]*?)<\/a>/gi, (match, ref, text) => {
            let cleanText = text.trim();
            if (!cleanText.startsWith('[') && !cleanText.startsWith('(')) {
                cleanText = `[${cleanText}]`;
            }
            return `<a class="stitle-ref-link" data-ref="${ref}" href="javascript:void(0)" title="병행 연관 말씀 보기">${cleanText}</a>`;
        });

        // 2. <h\d> 태그 정리
        formatted = formatted.replace(/<\/?h\d>/gi, ' ');
        return formatted.trim();
    },

    cleanVerseHtml(raw) {
        if (!raw) return '';
        let txt = raw.replace(/<p>/gi, '').replace(/<\/p>/gi, '');
        txt = txt.replace(/<cite>\d+<\/cite>/gi, '');
        
        // 관주(l)/각주(n)/구약인용구(c) 기호 마크업 변환 (예: <u class=c>M</u> -> <span class="crossref-mark">M</span>)
        txt = txt.replace(/<u class=["']?[lnc]["']?>([^<]+)<\/u>/gi, '<span class="crossref-mark" title="관주/인용/각주 보기">$1</span>');
        
        // 예수님 말씀 인용구 태그
        txt = txt.replace(/<q>/gi, '<q class="jesus-word">');
        return txt;
    },

    // 복사 및 카드용 순수 텍스트 정제 (관주/각주/인용 기호 M, ㄱ, 1, 단락 기호 ○, HTML 태그 완전 제거)
    getPureVerseText(raw) {
        if (!raw) return '';
        let txt = raw.replace(/<cite>\d+<\/cite>/gi, '');
        // 관주/각주/인용 태그 및 내부 기호(M, ㄱ, 1 등) 제거
        txt = txt.replace(/<u class=["']?[lnc]["']?>[^<]*<\/u>/gi, '');
        txt = txt.replace(/<span class=["']?crossref-mark["']?[^>]*>[^<]*<\/span>/gi, '');
        // 모든 남은 HTML 태그 제거
        txt = txt.replace(/<[^>]*>/g, '');
        // 단락 구분 기호(○, ●, § 등) 제거
        txt = txt.replace(/[○●§]/g, '');
        // 공백 정리
        txt = txt.replace(/\s+/g, ' ').trim();
        return txt;
    },

    getVersionName(code) {
        const names = {
            'rv': '개역개정', 'ko': '개역한글', 'ez': '쉬운성경', 'wr': '우리말성경',
            'nw': '새번역', 'nv': 'NIV', 'nt': 'NLT', 'es': 'ESV', 'nb': 'NASB', 'kj': 'KJV'
        };
        return names[code] || code.toUpperCase();
    },

    // 다중 선택 상태
    selectedVerses: new Set(),
    selectionAnchor: null,

    // 3. 절 클릭 및 스마트 범위 선택 처리 (모바일/터치 기본 지원)
    bindVerseClickEvents() {
        // 소제목 연관 구절 텍스트 링크 클릭 이벤트
        document.querySelectorAll('.stitle-ref-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const ref = link.dataset.ref;
                if (ref) this.openParallelModal(ref);
            });
        });

        const items = document.querySelectorAll('.verse-item, .verse-compare-row');
        items.forEach(el => {
            el.addEventListener('click', (e) => {
                // 연관 구절 링크 클릭 시
                if (e.target.closest('.stitle-ref-link')) {
                    return;
                }

                // 관주 기호 클릭 시
                if (e.target.classList.contains('crossref-mark')) {
                    e.stopPropagation();
                    const jeol = parseInt(el.dataset.jeol, 10);
                    window.BibleCrossRef?.showForVerse(window.BibleApp.state.currentUnitCode, jeol);
                    return;
                }

                const jeol = parseInt(el.dataset.jeol, 10);
                this.toggleVerseSelection(jeol);
            });
        });
    },

    // 3.1 소제목 연관 구절 (병행 본문) 팝업 모달
    async openParallelModal(ref) {
        window.BibleApp.openModal('modal-parallel-verses');
        const modalBody = document.getElementById('parallel-modal-body');
        const modalTitle = document.getElementById('parallel-modal-title');
        const gotoWrap = document.getElementById('parallel-goto-buttons-wrap');

        if (modalTitle) modalTitle.textContent = `연관 말씀 (${ref.replace(/;/g, ', ')})`;
        if (modalBody) {
            modalBody.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>연관 성경 말씀을 불러오는 중입니다...</p>
                </div>
            `;
        }
        if (gotoWrap) gotoWrap.innerHTML = '';

        try {
            const priVer = window.BibleApp.state.primaryVersion;
            const data = await window.BibleApp.fetchApi(`/lookup-ref?ref=${encodeURIComponent(ref)}&version=${priVer}`);
            
            if (!data.verses || data.verses.length === 0) {
                if (modalBody) {
                    modalBody.innerHTML = `
                        <div class="panel-empty-state">
                            <i data-lucide="alert-circle"></i>
                            <p>연관 구절 데이터를 불러올 수 없습니다.</p>
                        </div>
                    `;
                    if (window.lucide) window.lucide.createIcons();
                }
                return;
            }

            // 고유한 책/장 목록 수집
            const uniqueChapters = new Map();
            data.verses.forEach(v => {
                const key = `${v.unit_code}`;
                if (!uniqueChapters.has(key)) {
                    uniqueChapters.set(key, {
                        unit_code: v.unit_code,
                        book_name: v.book_name,
                        chapter: v.chapter,
                        first_jeol: v.jeol
                    });
                }
            });

            let html = '<div class="parallel-verses-list">';
            data.verses.forEach(v => {
                const text = this.cleanVerseHtml(v[`phrase_${priVer}`] || v.phrase_rv || '');
                html += `
                    <div class="parallel-verse-card">
                        <div class="parallel-verse-ref">
                            <div class="parallel-ref-info">
                                <span class="parallel-book-badge">${v.book_name} ${v.chapter}:${v.jeol}</span>
                                <span class="parallel-ver-tag">${this.getVersionName(priVer)}</span>
                            </div>
                            <button class="parallel-card-goto-btn" data-unit="${v.unit_code}" data-jeol="${v.jeol}" title="${v.book_name} ${v.chapter}장으로 이동">
                                <i data-lucide="external-link"></i> <span>${v.book_name} ${v.chapter}장 이동</span>
                            </button>
                        </div>
                        <div class="parallel-verse-body">${text}</div>
                    </div>
                `;
            });
            html += '</div>';

            if (modalBody) modalBody.innerHTML = html;

            // 푸터에 등장하는 모든 책/장 이동 버튼 추가
            if (gotoWrap) {
                let btnsHtml = '';
                uniqueChapters.forEach(info => {
                    btnsHtml += `
                        <button class="btn-primary parallel-footer-goto-btn" data-unit="${info.unit_code}" data-jeol="${info.first_jeol}">
                            <i data-lucide="book-open"></i> ${info.book_name} ${info.chapter}장으로 이동
                        </button>
                    `;
                });
                gotoWrap.innerHTML = btnsHtml;
            }

            if (window.lucide) window.lucide.createIcons();

            // 카드 및 푸터 이동 버튼 이벤트 바인딩
            document.querySelectorAll('.parallel-card-goto-btn, .parallel-footer-goto-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const unit = parseInt(btn.dataset.unit, 10);
                    const jeol = parseInt(btn.dataset.jeol, 10);
                    window.BibleApp.closeModal('modal-parallel-verses');
                    window.BibleApp.navigateTo(unit, jeol);
                });
            });

        } catch (e) {
            console.error('Failed to lookup parallel ref:', e);
            if (modalBody) {
                modalBody.innerHTML = `<div class="panel-empty-state"><p>말씀을 불러오는 중 오류가 발생했습니다.</p></div>`;
            }
        }
    },

    toggleVerseSelection(jeol) {
        // 1. 선택된 절이 없는 경우: 시작점(Anchor) 설정 및 단일 선택
        if (this.selectedVerses.size === 0) {
            this.selectedVerses.add(jeol);
            this.selectionAnchor = jeol;
        } 
        // 2. 1개만 선택된 상태에서 동일한 절을 다시 탭: 선택 해제
        else if (this.selectedVerses.size === 1 && this.selectedVerses.has(jeol)) {
            this.selectedVerses.clear();
            this.selectionAnchor = null;
        } 
        // 3. 다른 절 탭 시: 시작점(Anchor)부터 탭한 절까지 자동으로 연속 범위 일괄 선택!
        else {
            const anchor = this.selectionAnchor !== null ? this.selectionAnchor : Math.min(...this.selectedVerses);
            const start = Math.min(anchor, jeol);
            const end = Math.max(anchor, jeol);

            this.selectedVerses.clear();
            for (let j = start; j <= end; j++) {
                this.selectedVerses.add(j);
            }
        }

        this.updateSelectionUI();
    },

    updateSelectionUI() {
        const toolbar = document.getElementById('verse-action-toolbar');
        const label = document.getElementById('toolbar-verse-label');
        const countBadge = document.getElementById('toolbar-verse-count');

        // 모든 절의 선택 스타일 갱신
        document.querySelectorAll('.verse-item, .verse-compare-row').forEach(el => {
            const j = parseInt(el.dataset.jeol, 10);
            if (this.selectedVerses.has(j)) {
                el.classList.add('selected');
            } else {
                el.classList.remove('selected');
            }
        });

        if (this.selectedVerses.size === 0) {
            if (toolbar) toolbar.classList.remove('active');
            this.selectedVerse = null;
            window.BibleApp.state.selectedVerseData = null;
            return;
        }

        if (toolbar) toolbar.classList.add('active');

        const sorted = Array.from(this.selectedVerses).sort((a, b) => a - b);
        const bName = window.BibleApp.state.currentBookMeta.name;
        const ch = window.BibleApp.state.currentChapter;

        // 대표 구절
        this.selectedVerse = this.chapterData.verses.find(v => v.jeol === sorted[0]);
        window.BibleApp.state.selectedVerseData = this.selectedVerse;
        window.BibleApp.state.currentJeol = sorted[0];

        // 라벨 생성 (연속 범위 vs 불연속)
        let labelText = '';
        if (sorted.length === 1) {
            labelText = `${bName} ${ch}:${sorted[0]}`;
        } else {
            const isConsecutive = sorted.every((val, idx) => idx === 0 || val === sorted[idx - 1] + 1);
            if (isConsecutive) {
                labelText = `${bName} ${ch}:${sorted[0]}~${sorted[sorted.length - 1]}`;
            } else {
                labelText = `${bName} ${ch}:${sorted.join(', ')}`;
            }
        }

        if (label) label.textContent = labelText;

        if (countBadge) {
            countBadge.style.display = sorted.length > 1 ? 'inline-block' : 'none';
            countBadge.textContent = `${sorted.length}개 절`;
        }

        if (window.lucide) window.lucide.createIcons();

        // 사이드 패널이 열려있으면 첫 번째 선택된 절로 갱신
        if (window.BibleStrong?.isOpen) {
            window.BibleStrong.loadVerseStrongs(window.BibleApp.state.currentUnitCode, sorted[0]);
        }
    },

    clearSelection() {
        this.selectedVerses.clear();
        this.selectionAnchor = null;
        this.updateSelectionUI();
    },

    getSelectedVersesSorted() {
        if (!this.chapterData || this.selectedVerses.size === 0) return [];
        const sortedNums = Array.from(this.selectedVerses).sort((a, b) => a - b);
        return sortedNums.map(j => this.chapterData.verses.find(v => v.jeol === j)).filter(Boolean);
    },

    scrollToVerse(jeol) {
        const target = document.getElementById(`verse-${jeol}`);
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            target.classList.add('selected');
            setTimeout(() => {
                if (!this.selectedVerses.has(jeol)) {
                    target.classList.remove('selected');
                }
            }, 1500);
        }
    },

    // 4. 플로팅 툴바 액션들 (다중 선택 일괄 처리)
    setupToolbarEvents() {
        // 선택 해제 버튼
        document.getElementById('btn-clear-selection')?.addEventListener('click', () => {
            this.clearSelection();
        });

        // 일괄 형광펜 색상 클릭
        document.querySelectorAll('.highlight-picker .color-dot').forEach(dot => {
            dot.addEventListener('click', async () => {
                const sorted = this.getSelectedVersesSorted();
                if (sorted.length === 0) return;

                const color = dot.dataset.color;
                const unit = window.BibleApp.state.currentUnitCode;

                // 병렬로 모든 선택된 절에 형광펜 적용
                await Promise.all(sorted.map(v => {
                    return window.BibleApp.fetchApi('/user/highlight', {
                        method: 'POST',
                        body: JSON.stringify({ unit_code: unit, jeol: v.jeol, color })
                    });
                }));

                // UI 즉시 일괄 업데이트
                sorted.forEach(v => {
                    const el = document.getElementById(`verse-${v.jeol}`);
                    if (el) {
                        el.className = el.className.replace(/hl-(yellow|green|pink|cyan)/g, '').trim();
                        if (color !== 'none') el.classList.add(`hl-${color}`);
                    }
                    v.highlight = color === 'none' ? null : color;
                });

                window.BibleApp.showToast(color === 'none' 
                    ? `${sorted.length}개 구절의 형광펜이 지워졌습니다.` 
                    : `${sorted.length}개 구절에 형광펜이 칠해졌습니다.`);
            });
        });

        // 일괄 북마크
        document.getElementById('btn-action-bookmark')?.addEventListener('click', async () => {
            const sorted = this.getSelectedVersesSorted();
            if (sorted.length === 0) return;

            const unit = window.BibleApp.state.currentUnitCode;
            await Promise.all(sorted.map(v => {
                return window.BibleApp.fetchApi('/user/bookmark', {
                    method: 'POST',
                    body: JSON.stringify({ unit_code: unit, jeol: v.jeol })
                });
            }));

            await this.reload();
            window.BibleApp.showToast(`${sorted.length}개 구절의 북마크가 업데이트되었습니다.`);
        });

        // 메모 모달 열기
        document.getElementById('btn-action-note')?.addEventListener('click', () => {
            const sorted = this.getSelectedVersesSorted();
            if (sorted.length === 0) return;

            const bName = window.BibleApp.state.currentBookMeta.name;
            const ch = window.BibleApp.state.currentChapter;

            let versesSummary = '';
            if (sorted.length === 1) {
                versesSummary = `${bName} ${ch}:${sorted[0].jeol} - ${this.cleanVerseHtml(sorted[0].phrase_rv)}`;
            } else {
                versesSummary = `${bName} ${ch}:${sorted[0].jeol}~${sorted[sorted.length - 1].jeol} (${sorted.length}개 구절)\n` +
                    sorted.map(v => `${v.jeol}. ${this.cleanVerseHtml(v.phrase_rv)}`).join('\n');
            }

            document.getElementById('note-verse-text').textContent = versesSummary;
            document.getElementById('note-textarea').value = sorted[0].note ? sorted[0].note.content : '';

            const delBtn = document.getElementById('btn-delete-note');
            if (delBtn) delBtn.style.display = sorted[0].note ? 'inline-block' : 'none';

            window.BibleApp.openModal('modal-note');
        });

        // 일괄 말씀 카드 만들기
        document.getElementById('btn-action-card')?.addEventListener('click', () => {
            const sorted = this.getSelectedVersesSorted();
            if (sorted.length === 0) return;

            window.BibleApp.openModal('modal-card-gen');
            window.BibleCardGen?.prepareCardWithMultipleVerses(sorted);
        });

        // 원어 사전 보기
        document.getElementById('btn-action-strong')?.addEventListener('click', () => {
            const sorted = this.getSelectedVersesSorted();
            if (sorted.length === 0) return;
            window.BibleStrong?.showForVerse(window.BibleApp.state.currentUnitCode, sorted[0].jeol);
        });

        // 관주 보기
        document.getElementById('btn-action-crossref')?.addEventListener('click', () => {
            const sorted = this.getSelectedVersesSorted();
            if (sorted.length === 0) return;
            window.BibleCrossRef?.showForVerse(window.BibleApp.state.currentUnitCode, sorted[0].jeol);
        });

        // 일괄 구절 복사
        document.getElementById('btn-action-copy')?.addEventListener('click', () => {
            const sorted = this.getSelectedVersesSorted();
            if (sorted.length === 0) return;

            const bName = window.BibleApp.state.currentBookMeta.name;
            const ch = window.BibleApp.state.currentChapter;
            const priVer = window.BibleApp.state.primaryVersion;

            let headerRef = '';
            const isConsecutive = sorted.every((val, idx) => idx === 0 || val.jeol === sorted[idx - 1].jeol + 1);
            if (sorted.length === 1) {
                headerRef = `[${bName} ${ch}:${sorted[0].jeol}]`;
            } else if (isConsecutive) {
                headerRef = `[${bName} ${ch}:${sorted[0].jeol}-${sorted[sorted.length - 1].jeol}]`;
            } else {
                headerRef = `[${bName} ${ch}:${sorted.map(v => v.jeol).join(', ')}]`;
            }

            const lines = sorted.map(v => {
                const pureText = this.getPureVerseText(v[`phrase_${priVer}`] || v.phrase_rv);
                return `${v.jeol} ${pureText}`;
            });

            const copyStr = `${headerRef}\n${lines.join('\n')}`;

            navigator.clipboard.writeText(copyStr).then(() => {
                window.BibleApp.showToast(`${sorted.length}개 말씀 구절이 클립보드에 복사되었습니다!`);
            });
        });
    },

    // 5. 메모 모달 저장/삭제 로직
    setupNoteModal() {
        document.getElementById('btn-save-note')?.addEventListener('click', async () => {
            if (!this.selectedVerse) return;
            const content = document.getElementById('note-textarea').value;
            const unit = window.BibleApp.state.currentUnitCode;
            const jeol = this.selectedVerse.jeol;

            await window.BibleApp.fetchApi('/user/note', {
                method: 'POST',
                body: JSON.stringify({ unit_code: unit, jeol, content })
            });

            window.BibleApp.closeModal('modal-note');
            await this.reload();
            window.BibleApp.showToast('묵상 메모가 저장되었습니다.');
        });

        document.getElementById('btn-delete-note')?.addEventListener('click', async () => {
            if (!this.selectedVerse) return;
            const unit = window.BibleApp.state.currentUnitCode;
            const jeol = this.selectedVerse.jeol;

            await window.BibleApp.fetchApi('/user/note', {
                method: 'POST',
                body: JSON.stringify({ unit_code: unit, jeol, content: '' })
            });

            window.BibleApp.closeModal('modal-note');
            await this.reload();
            window.BibleApp.showToast('메모가 삭제되었습니다.');
        });
    },

    // 6. 통독 체크 토글
    async toggleCurrentChapterRead() {
        const unit = window.BibleApp.state.currentUnitCode;
        const res = await window.BibleApp.fetchApi('/user/reading-toggle', {
            method: 'POST',
            body: JSON.stringify({ unit_code: unit })
        });
        this.updateReadButtonState(res.is_read);
        window.BibleApp.showToast(res.is_read ? '통독 완료로 체크되었습니다!' : '통독 체크가 해제되었습니다.');
    },

    updateReadButtonState(isRead) {
        const btn = document.getElementById('btn-toggle-read');
        const label = document.getElementById('read-btn-label');
        if (!btn || !label) return;

        if (isRead) {
            btn.classList.add('read-completed');
            label.textContent = '통독 완료 됨 ✓';
        } else {
            btn.classList.remove('read-completed');
            label.textContent = '통독 완료 체크';
        }
    },

    // 7. Web Speech API (TTS) 음성 낭독 & 싱크
    setupTtsEvents() {
        document.getElementById('btn-toggle-read')?.addEventListener('click', () => this.toggleCurrentChapterRead());

        // 헤더 낭독 토글 버튼
        document.getElementById('btn-toggle-tts')?.addEventListener('click', () => {
            this.toggleAudioBar();
        });

        // 구절 선택 툴바 낭독 버튼
        document.getElementById('btn-action-tts')?.addEventListener('click', () => {
            const firstJeol = this.selectedVerses.size > 0 
                ? Math.min(...Array.from(this.selectedVerses)) 
                : (this.selectedVerse?.jeol || 1);
            
            const targetIdx = this.chapterData ? this.chapterData.verses.findIndex(v => v.jeol === firstJeol) : 0;
            this.clearSelection();
            this.playTtsFrom(targetIdx >= 0 ? targetIdx : 0);
        });

        // 오디오 재생 버튼
        document.getElementById('btn-audio-play')?.addEventListener('click', () => {
            if (this.tts.isPlaying) {
                this.pauseTts();
            } else {
                this.playTtsFrom(this.tts.currentVerseIndex);
            }
        });

        document.getElementById('btn-audio-stop')?.addEventListener('click', () => this.stopTts());
        document.getElementById('btn-audio-prev')?.addEventListener('click', () => {
            const nextIdx = Math.max(0, this.tts.currentVerseIndex - 1);
            this.playTtsFrom(nextIdx);
        });
        document.getElementById('btn-audio-next')?.addEventListener('click', () => {
            const nextIdx = this.tts.currentVerseIndex + 1;
            if (this.chapterData && nextIdx < this.chapterData.verses.length) {
                this.playTtsFrom(nextIdx);
            }
        });

        document.getElementById('audio-speed-select')?.addEventListener('change', (e) => {
            this.tts.rate = parseFloat(e.target.value);
            if (this.tts.isPlaying) {
                this.playTtsFrom(this.tts.currentVerseIndex);
            }
        });

        document.getElementById('btn-audio-close')?.addEventListener('click', () => {
            this.stopTts();
            this.toggleAudioBar(false);
        });
    },

    toggleAudioBar(forceState = null) {
        const audioBar = document.getElementById('floating-audio-bar');
        if (!audioBar) return;

        const willBeActive = forceState !== null ? forceState : !audioBar.classList.contains('active');
        audioBar.classList.toggle('active', willBeActive);

        const headerBtn = document.getElementById('btn-toggle-tts');
        if (headerBtn) headerBtn.classList.toggle('active', willBeActive);

        if (willBeActive && !this.tts.isPlaying) {
            // 바가 열릴 때 제목/구절 기본 텍스트 갱신
            const priVer = window.BibleApp.state.primaryVersion;
            const bName = window.BibleApp.state.currentBookMeta.name;
            const ch = window.BibleApp.state.currentChapter;
            const firstVerse = this.chapterData?.verses?.[this.tts.currentVerseIndex || 0];
            
            document.getElementById('audio-now-title').textContent = `${bName} ${ch}장 (${this.getVersionName(priVer)})`;
            if (firstVerse) {
                const text = this.cleanVerseHtml(firstVerse[`phrase_${priVer}`] || firstVerse.phrase_rv);
                document.getElementById('audio-now-verse').textContent = `${firstVerse.jeol}절: ${text.substring(0, 30)}...`;
            }
        }
    },

    playTtsFrom(index) {
        if (!this.chapterData || !this.chapterData.verses.length) return;
        if (index >= this.chapterData.verses.length) {
            this.stopTts();
            window.BibleApp.showToast('장 낭독이 완료되었습니다.');
            return;
        }

        this.toggleAudioBar(true);
        this.tts.synth.cancel();
        this.tts.currentVerseIndex = index;
        const verse = this.chapterData.verses[index];
        const priVer = window.BibleApp.state.primaryVersion;
        const text = this.cleanVerseHtml(verse[`phrase_${priVer}`] || verse.phrase_rv);

        const bName = window.BibleApp.state.currentBookMeta.name;
        const ch = window.BibleApp.state.currentChapter;

        document.getElementById('audio-now-title').textContent = `${bName} ${ch}장 (${this.getVersionName(priVer)})`;
        document.getElementById('audio-now-verse').textContent = `${verse.jeol}절: ${text.substring(0, 35)}...`;

        // 하이라이트 싱크
        document.querySelectorAll('.verse-item.audio-active, .verse-compare-row.audio-active').forEach(el => el.classList.remove('audio-active'));
        const activeEl = document.getElementById(`verse-${verse.jeol}`);
        if (activeEl) {
            activeEl.classList.add('audio-active');
            activeEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        const utterText = `${verse.jeol}절. ${text}`;
        const utter = new SpeechSynthesisUtterance(utterText);
        utter.rate = this.tts.rate;
        utter.lang = (priVer === 'nv' || priVer === 'kj' || priVer === 'es' || priVer === 'nt' || priVer === 'nb') ? 'en-US' : 'ko-KR';

        utter.onend = () => {
            if (this.tts.isPlaying) {
                this.playTtsFrom(this.tts.currentVerseIndex + 1);
            }
        };

        utter.onerror = (e) => {
            console.warn('TTS error:', e);
            this.stopTts();
        };

        this.tts.utterance = utter;
        this.tts.isPlaying = true;
        this.updateAudioPlayIcon(true);
        this.tts.synth.speak(utter);
    },

    pauseTts() {
        this.tts.isPlaying = false;
        this.tts.synth.cancel();
        this.updateAudioPlayIcon(false);
    },

    stopTts() {
        this.tts.isPlaying = false;
        this.tts.currentVerseIndex = 0;
        this.tts.synth.cancel();
        this.updateAudioPlayIcon(false);
        document.querySelectorAll('.verse-item.audio-active, .verse-compare-row.audio-active').forEach(el => el.classList.remove('audio-active'));
    },

    updateAudioPlayIcon(isPlaying) {
        const icon = document.getElementById('audio-play-icon');
        if (icon) {
            icon.setAttribute('data-lucide', isPlaying ? 'pause' : 'play');
            if (window.lucide) window.lucide.createIcons();
        }
        const anim = document.getElementById('audio-wave-anim');
        if (anim) anim.style.opacity = isPlaying ? '1' : '0.3';
    }
};
