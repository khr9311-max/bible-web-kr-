/**
 * 말씀성경 웹 애플리케이션 코어 모듈 (app.js)
 * 전역 상태 관리, API 호출, 테마 및 환경설정, 모달 제어, 토스트 메시지
 */

window.BibleApp = {
    // 전역 상태
    state: {
        currentUnitCode: 1001, // 기본 창세기 1장
        currentBookId: 1,
        currentChapter: 1,
        currentJeol: 1,
        primaryVersion: 'rv',
        compareVersion: 'nv',
        isCompareMode: false,
        isStrongMode: false,
        theme: 'dark',
        fontSize: 14,
        lineHeight: 1.6,
        viewMode: 'verse', // 'verse' (절 단위) | 'paragraph' (문단 단위 붙여읽기)
        koreanFont: 'noto-serif',
        englishFont: 'eb-garamond',
        showStitles: true,
        showCrossrefs: true,
        showVerseNums: true,
        showRedLetters: true,
        isFocusMode: false,
        books: [],
        currentBookMeta: null,
        selectedVerseEl: null,
        selectedVerseData: null
    },

    // 초기화
    async init() {
        this.loadSettings();
        this.applyTheme(this.state.theme);
        this.applyViewerSettings();
        this.setupGlobalEvents();
        
        await this.loadBooks();
        await this.loadTodayWordOnStart();

        // URL 해시 파라미터 처리 (#unit=1001&jeol=1 등)
        this.handleUrlHash();

        // 뷰어 및 각 모듈 초기화
        window.BibleReader?.init();
        window.BibleNav?.init();
        window.BibleSearch?.init();
        window.BibleCrossRef?.init();
        window.BibleCardGen?.init();
        window.BibleReading?.init();

        // Lucide Icons 렌더링
        if (window.lucide) {
            window.lucide.createIcons();
        }

        // PWA 서비스 워커 등록
        this.registerServiceWorker();
    },

    // 1. API 래퍼
    async fetchApi(endpoint, options = {}) {
        try {
            const res = await fetch(`/api${endpoint}`, {
                headers: { 'Content-Type': 'application/json' },
                ...options
            });
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'API Request failed');
            return data.data;
        } catch (err) {
            console.error(`API Error on ${endpoint}:`, err);
            this.showToast(`오류 발생: ${err.message}`, 'error');
            throw err;
        }
    },

    // 2. 책 목록 로드
    async loadBooks() {
        try {
            const books = await this.fetchApi('/books');
            this.state.books = books;
            this.updateCurrentBookMeta();
        } catch (e) {
            console.error('Failed to load books:', e);
        }
    },

    updateCurrentBookMeta() {
        const bookId = Math.floor(this.state.currentUnitCode / 1000);
        this.state.currentBookId = bookId;
        this.state.currentChapter = this.state.currentUnitCode % 1000;
        this.state.currentBookMeta = this.state.books.find(b => b.id === bookId) || { 
            name: '창세기', abbr: '창', eng_name: 'Genesis', eng_abbr: 'Gen', 
            chapters: 50, category: '율법서', testament: 'OT' 
        };
        
        const engVers = ['nv', 'nt', 'es', 'nb', 'kj'];
        const isPriEng = engVers.includes(this.state.primaryVersion);
        const isCompEng = engVers.includes(this.state.compareVersion);

        const korName = `${this.state.currentBookMeta.name} ${this.state.currentChapter}장`;
        const engName = `${this.state.currentBookMeta.eng_name || this.state.currentBookMeta.name} ${this.state.currentChapter}`;

        let locText = isPriEng ? engName : korName;
        if (this.state.isCompareMode) {
            if (!isPriEng && isCompEng) {
                locText = `${korName} (${this.state.currentBookMeta.eng_name || ''} ${this.state.currentChapter})`;
            } else if (isPriEng && !isCompEng) {
                locText = `${engName} (${this.state.currentBookMeta.name} ${this.state.currentChapter}장)`;
            }
        }

        const locEl = document.getElementById('current-location-text');
        if (locEl) locEl.textContent = locText;

        const titleEl = document.getElementById('chapter-title');
        if (titleEl) titleEl.textContent = locText;

        const subEl = document.getElementById('chapter-subtitle');
        if (subEl) {
            if (isPriEng) {
                subEl.textContent = `${this.state.currentBookMeta.testament === 'OT' ? 'Old Testament' : 'New Testament'} / ${this.state.currentBookMeta.category}`;
            } else {
                subEl.textContent = `${this.state.currentBookMeta.testament === 'OT' ? '구약' : '신약'} / ${this.state.currentBookMeta.category}`;
            }
        }
    },

    // 3. 특정 장으로 이동
    async navigateTo(unitCode, targetJeol = 1) {
        this.state.currentUnitCode = parseInt(unitCode, 10);
        this.state.currentJeol = parseInt(targetJeol, 10) || 1;
        this.updateCurrentBookMeta();
        this.saveSettings();

        // 뷰어 새로고침
        if (window.BibleReader) {
            await window.BibleReader.loadChapter(this.state.currentUnitCode, this.state.currentJeol);
        }

        // 페이지 상단으로 부드럽게 스크롤
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // 내비게이션 UI 버튼 텍스트(이전 장/다음 장 이름) 갱신
        this.updateChapterNavigationUI();

        // URL 해시 갱신
        window.history.replaceState(null, '', `#unit=${this.state.currentUnitCode}&jeol=${this.state.currentJeol}`);

        // 모달들 닫기
        this.closeAllModals();
    },

    updateChapterNavigationUI() {
        const bookId = Math.floor(this.state.currentUnitCode / 1000);
        const ch = this.state.currentUnitCode % 1000;
        const currentBook = this.state.currentBookMeta;
        if (!currentBook) return;

        // 이전 장 정보 계산
        let prevLabel = '이전 장';
        if (ch > 1) {
            prevLabel = `${currentBook.name} ${ch - 1}장`;
        } else if (bookId > 1) {
            const prevBook = this.state.books.find(b => b.id === bookId - 1);
            if (prevBook) prevLabel = `${prevBook.name} ${prevBook.chapters}장`;
        }

        // 다음 장 정보 계산
        let nextLabel = '다음 장';
        if (ch < currentBook.chapters) {
            nextLabel = `${currentBook.name} ${ch + 1}장`;
        } else if (bookId < 66) {
            const nextBook = this.state.books.find(b => b.id === bookId + 1);
            if (nextBook) nextLabel = `${nextBook.name} 1장`;
        }

        // 하단 내비게이션 버튼 텍스트 갱신
        const bottomPrevBtn = document.getElementById('btn-bottom-prev');
        if (bottomPrevBtn) {
            bottomPrevBtn.innerHTML = `<i data-lucide="arrow-left"></i> ${prevLabel}`;
            bottomPrevBtn.title = `${prevLabel}으로 이동 (단축키: ← 또는 스와이프)`;
        }

        const bottomNextBtn = document.getElementById('btn-bottom-next');
        if (bottomNextBtn) {
            bottomNextBtn.innerHTML = `${nextLabel} <i data-lucide="arrow-right"></i>`;
            bottomNextBtn.title = `${nextLabel}으로 이동 (단축키: → 또는 스와이프)`;
        }

        const floatPrevBtn = document.getElementById('btn-prev-chapter');
        if (floatPrevBtn) floatPrevBtn.title = `${prevLabel}으로 이동 (단축키: ←)`;

        const floatNextBtn = document.getElementById('btn-next-chapter');
        if (floatNextBtn) floatNextBtn.title = `${nextLabel}으로 이동 (단축키: →)`;

        if (window.lucide) window.lucide.createIcons();
    },

    navigatePrevChapter() {
        const currentBook = this.state.currentBookMeta;
        if (!currentBook) return;

        let prevUnit = this.state.currentUnitCode - 1;
        const currentCh = this.state.currentUnitCode % 1000;

        if (currentCh <= 1) {
            // 이전 책의 마지막 장으로 이동
            const prevBookId = this.state.currentBookId - 1;
            if (prevBookId >= 1) {
                const prevBook = this.state.books.find(b => b.id === prevBookId);
                if (prevBook) {
                    prevUnit = (prevBook.id * 1000) + prevBook.chapters;
                }
            } else {
                this.showToast('성경의 첫 번째 장(창세기 1장)입니다.');
                return;
            }
        }
        this.navigateTo(prevUnit);
    },

    navigateNextChapter() {
        const currentBook = this.state.currentBookMeta;
        if (!currentBook) return;

        let nextUnit = this.state.currentUnitCode + 1;
        const currentCh = this.state.currentUnitCode % 1000;

        if (currentCh >= currentBook.chapters) {
            // 다음 책의 1장으로 이동
            const nextBookId = this.state.currentBookId + 1;
            if (nextBookId <= 66) {
                nextUnit = (nextBookId * 1000) + 1;
            } else {
                this.showToast('성경의 마지막 장(요한계시록 22장)입니다.');
                return;
            }
        }
        this.navigateTo(nextUnit);
    },

    // 좌우 스와이프 제스처 (안드로이드 / 삼성인터넷 / iOS 모바일 최적화)
    setupSwipeGestures() {
        let touchStartX = 0;
        let touchStartY = 0;
        let touchStartTime = 0;

        const handleTouchStart = (e) => {
            if (e.touches.length !== 1) return;
            
            // 모달이나 플로팅 툴바가 열려있으면 스와이프 제외
            if (document.querySelector('.modal-overlay.active') || document.querySelector('.floating-selection-toolbar.active')) {
                return;
            }

            const x = e.touches[0].clientX;
            const screenW = window.innerWidth || document.documentElement.clientWidth;

            // 삼성 인터넷 및 안드로이드 OS의 '가장자리 쓸어 뒤로가기' 제스처 충돌 방지 (좌우 40px 제외)
            if (x < 40 || x > screenW - 40) return;

            touchStartX = x;
            touchStartY = e.touches[0].clientY;
            touchStartTime = Date.now();
        };

        const handleTouchEnd = (e) => {
            if (e.changedTouches.length === 0 || touchStartX === 0) return;

            if (document.querySelector('.modal-overlay.active') || document.querySelector('.floating-selection-toolbar.active')) {
                touchStartX = 0;
                return;
            }

            const deltaX = e.changedTouches[0].clientX - touchStartX;
            const deltaY = e.changedTouches[0].clientY - touchStartY;
            const deltaTime = Date.now() - touchStartTime;

            touchStartX = 0; // 리셋

            // 스와이프 엄격 판정: 450ms 이내, 수평 80px 이상, 수평 이동이 수직 이동의 2.0배 이상 (상하 스크롤 오작동 100% 방지)
            if (deltaTime < 450 && Math.abs(deltaX) >= 80 && Math.abs(deltaX) >= Math.abs(deltaY) * 2.0) {
                if (deltaX < -80) {
                    // 오른쪽에서 왼쪽으로 쓱 쓸기 ➔ 다음 장
                    this.navigateNextChapter();
                } else if (deltaX > 80) {
                    // 왼쪽에서 오른쪽으로 쓱 쓸기 ➔ 이전 장
                    this.navigatePrevChapter();
                }
            }
        };

        window.addEventListener('touchstart', handleTouchStart, { passive: true });
        window.addEventListener('touchend', handleTouchEnd, { passive: true });
    },

    // 4. 오늘의 말씀 알림
    async loadTodayWordOnStart() {
        try {
            const today = await this.fetchApi('/today');
            if (today && today.one_line_thanks) {
                console.log('📖 오늘의 감사 말씀:', today.one_line_thanks);
            }
        } catch (e) {}
    },

    // 5. 전역 이벤트 및 단축키
    setupGlobalEvents() {
        // 스와이프 제스처 등록
        this.setupSwipeGestures();

        // 단축키 (좌/우 방향키로 장 이동, PageUp/PageDown, Ctrl+F로 검색, ESC로 집중모드/모달 닫기)
        window.addEventListener('keydown', (e) => {
            if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

            if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
                this.navigatePrevChapter();
            } else if (e.key === 'ArrowRight' || e.key === 'PageDown') {
                this.navigateNextChapter();
            } else if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                this.openModal('modal-search');
            } else if (e.key === 'Escape') {
                if (this.state.isFocusMode) {
                    this.toggleFocusMode(false);
                }
                this.closeAllModals();
            }
        });

        // 헤더 버튼들
        document.getElementById('btn-brand')?.addEventListener('click', () => {
            this.navigateTo(1001);
        });

        document.getElementById('btn-prev-chapter')?.addEventListener('click', () => this.navigatePrevChapter());
        document.getElementById('btn-next-chapter')?.addEventListener('click', () => this.navigateNextChapter());
        document.getElementById('btn-bottom-prev')?.addEventListener('click', () => this.navigatePrevChapter());
        document.getElementById('btn-bottom-next')?.addEventListener('click', () => this.navigateNextChapter());

        // 통독 체크 후 다음 장
        document.getElementById('btn-bottom-check-next')?.addEventListener('click', async () => {
            await window.BibleReader?.toggleCurrentChapterRead();
            this.navigateNextChapter();
        });

        // 집중 모드 토글 버튼들
        document.getElementById('btn-toggle-focus')?.addEventListener('click', () => {
            this.toggleFocusMode(!this.state.isFocusMode);
        });
        document.getElementById('btn-exit-focus')?.addEventListener('click', () => {
            this.toggleFocusMode(false);
        });

        // 모달 열기 버튼들
        document.getElementById('btn-open-nav')?.addEventListener('click', () => this.openModal('modal-navigator'));
        document.getElementById('btn-open-search')?.addEventListener('click', () => this.openModal('modal-search'));
        document.getElementById('btn-open-reading')?.addEventListener('click', () => {
            this.openModal('modal-reading');
            window.BibleReading?.loadData();
        });
        document.getElementById('btn-open-card-gen')?.addEventListener('click', () => {
            this.openModal('modal-card-gen');
            window.BibleCardGen?.prepareCard();
        });
        document.getElementById('btn-open-settings')?.addEventListener('click', () => this.openModal('modal-settings'));
        document.getElementById('btn-open-family-links')?.addEventListener('click', () => this.openModal('modal-family-links'));

        // 번역본 선택 모달 열기 버튼 (모바일/PC 공용)
        document.getElementById('btn-open-versions')?.addEventListener('click', () => {
            this.openVersionModal();
        });

        // 상시 노출 대조 모드 빠른 토글 버튼 (모바일/PC 공용)
        document.getElementById('btn-quick-toggle-compare')?.addEventListener('click', () => {
            this.state.isCompareMode = !this.state.isCompareMode;
            this.updateVersionUI();
            this.saveSettings();
            window.BibleReader?.reload();
            this.showToast(this.state.isCompareMode 
                ? `[${this.getVersionName(this.state.primaryVersion)}]와 [${this.getVersionName(this.state.compareVersion)}] 나란히 대조 보기가 활성화되었습니다.` 
                : '대조 보기가 해제되고 기본 번역본 뷰어로 전환되었습니다.');
        });

        // 번역본 선택 모달 탭 스위처
        document.getElementById('tab-primary-ver')?.addEventListener('click', () => {
            this.versionModalState.activeTab = 'primary';
            document.getElementById('tab-primary-ver')?.classList.add('active');
            document.getElementById('tab-compare-ver')?.classList.remove('active');
            this.updateVersionModalUI();
        });

        document.getElementById('tab-compare-ver')?.addEventListener('click', () => {
            this.versionModalState.activeTab = 'compare';
            document.getElementById('tab-compare-ver')?.classList.add('active');
            document.getElementById('tab-primary-ver')?.classList.remove('active');
            this.updateVersionModalUI();
        });

        // 모달 내부 대조 모드 토글
        document.getElementById('chk-modal-compare-mode')?.addEventListener('change', (e) => {
            this.versionModalState.tempIsCompare = e.target.checked;
            this.updateVersionModalUI();
        });

        // 10개 번역본 카드 클릭 이벤트 (모달이 바로 닫히지 않고 상태만 갱신)
        document.querySelectorAll('.version-card-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const ver = btn.dataset.ver;
                if (this.versionModalState.activeTab === 'primary') {
                    this.versionModalState.tempPrimary = ver;
                } else {
                    this.versionModalState.tempCompare = ver;
                    this.versionModalState.tempIsCompare = true;
                }
                this.updateVersionModalUI();
            });
        });

        // [적용하기] 버튼 클릭 시에만 본문 일괄 리로드
        document.getElementById('btn-apply-versions')?.addEventListener('click', () => {
            this.applySelectedVersions();
        });

        // 번역본 선택기 변경 (헤더 데스크톱 드롭다운)
        document.getElementById('select-primary-ver')?.addEventListener('change', (e) => {
            this.state.primaryVersion = e.target.value;
            this.updateVersionUI();
            this.saveSettings();
            window.BibleReader?.reload();
        });

        document.getElementById('select-compare-ver')?.addEventListener('change', (e) => {
            this.state.compareVersion = e.target.value;
            this.updateVersionUI();
            this.saveSettings();
            window.BibleReader?.reload();
        });

        // 대조 모드 토글 (헤더)
        document.getElementById('chk-compare-mode')?.addEventListener('change', (e) => {
            this.state.isCompareMode = e.target.checked;
            this.updateVersionUI();
            this.saveSettings();
            window.BibleReader?.reload();
        });

        // 모달 닫기 공통 이벤트
        document.querySelectorAll('[data-close]').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.getAttribute('data-close');
                this.closeModal(targetId);
            });
        });

        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.closeModal(overlay.id);
                }
            });
        });

        document.querySelectorAll('.modal-card').forEach(card => {
            card.addEventListener('click', (e) => e.stopPropagation());
            card.addEventListener('touchend', (e) => e.stopPropagation());
        });

        // 뷰어 설정 컨트롤러들 - 테마
        document.querySelectorAll('.theme-option-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const th = btn.dataset.theme;
                this.applyTheme(th);
                document.querySelectorAll('.theme-option-btn').forEach(b => b.classList.toggle('active', b === btn));
            });
        });

        // 붙여읽기 방식 (절 단위 vs 문단 단위)
        document.querySelectorAll('.viewmode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.state.viewMode = btn.dataset.mode;
                document.querySelectorAll('.viewmode-btn').forEach(b => b.classList.toggle('active', b === btn));
                this.applyViewerSettings();
                this.showToast(this.state.viewMode === 'paragraph' ? '문단 단위(붙여읽기) 모드가 적용되었습니다.' : '절 단위(줄바꿈) 모드가 적용되었습니다.');
            });
        });

        // 글자 크기 & 줄 간격 (실시간 GPU 가속 갱신 + 변경 완료 시 저장으로 깜빡임 100% 제거)
        const sliderFontSize = document.getElementById('slider-font-size');
        sliderFontSize?.addEventListener('input', (e) => {
            const val = parseInt(e.target.value, 10);
            this.state.fontSize = val;
            const label = document.getElementById('font-size-val');
            if (label) label.textContent = `${val}px`;
            requestAnimationFrame(() => {
                document.documentElement.style.setProperty('--scripture-size', `${val}px`);
            });
        });
        sliderFontSize?.addEventListener('change', () => {
            this.saveSettings();
        });

        const sliderLineHeight = document.getElementById('slider-line-height');
        sliderLineHeight?.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            this.state.lineHeight = val;
            const label = document.getElementById('line-height-val');
            if (label) label.textContent = `${val}`;
            requestAnimationFrame(() => {
                document.documentElement.style.setProperty('--scripture-line-height', `${val}`);
            });
        });
        sliderLineHeight?.addEventListener('change', () => {
            this.saveSettings();
        });

        // 한글 서체 선택
        document.querySelectorAll('.font-choice-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.state.koreanFont = btn.dataset.font;
                document.querySelectorAll('.font-choice-btn').forEach(b => b.classList.toggle('active', b === btn));
                this.applyViewerSettings();
            });
        });

        // 영문 서체 선택
        document.querySelectorAll('.font-eng-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.state.englishFont = btn.dataset.fontEng;
                document.querySelectorAll('.font-eng-btn').forEach(b => b.classList.toggle('active', b === btn));
                this.applyViewerSettings();
            });
        });

        // 상세 표시 옵션 체크박스들
        document.getElementById('chk-show-stitles')?.addEventListener('change', (e) => {
            this.state.showStitles = e.target.checked;
            this.applyViewerSettings();
        });

        document.getElementById('chk-show-crossref-marks')?.addEventListener('change', (e) => {
            this.state.showCrossrefs = e.target.checked;
            this.applyViewerSettings();
        });

        document.getElementById('chk-show-verse-nums')?.addEventListener('change', (e) => {
            this.state.showVerseNums = e.target.checked;
            this.applyViewerSettings();
        });

        document.getElementById('chk-show-red-letters')?.addEventListener('change', (e) => {
            this.state.showRedLetters = e.target.checked;
            this.applyViewerSettings();
        });

        document.getElementById('chk-focus-mode')?.addEventListener('change', (e) => {
            this.toggleFocusMode(e.target.checked);
        });
    },

    // 6. 테마 & 뷰어 스타일 적용
    applyTheme(theme) {
        this.state.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        const metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) {
            metaTheme.setAttribute('content', theme === 'dark' ? '#0c0e12' : (theme === 'sepia' ? '#f4ecd8' : '#f8fafc'));
        }
        this.saveSettings();
    },

    toggleFocusMode(forceState = null) {
        this.state.isFocusMode = forceState !== null ? forceState : !this.state.isFocusMode;
        document.body.classList.toggle('focus-mode-active', this.state.isFocusMode);
        
        const chk = document.getElementById('chk-focus-mode');
        if (chk) chk.checked = this.state.isFocusMode;

        this.showToast(this.state.isFocusMode ? '성경 본문만 보기(집중 모드)가 활성화되었습니다. (ESC로 해제)' : '집중 모드가 해제되었습니다.');
        this.saveSettings();
    },

    applyViewerSettings() {
        document.documentElement.style.setProperty('--scripture-size', `${this.state.fontSize}px`);
        document.documentElement.style.setProperty('--scripture-line-height', `${this.state.lineHeight}`);
        
        // 한글 폰트 패밀리 매핑
        const fontMap = {
            'noto-serif': "'Noto Serif KR', Georgia, serif",
            'nanum-myeongjo': "'Nanum Myeongjo', 'Noto Serif KR', serif",
            'pretendard': "'Pretendard', sans-serif",
            'noto-sans': "'Noto Sans KR', sans-serif",
            'nanum-gothic': "'Nanum Gothic', sans-serif",
            'system': "-apple-system, BlinkMacSystemFont, sans-serif"
        };
        const fontVal = fontMap[this.state.koreanFont] || fontMap['noto-serif'];
        document.documentElement.style.setProperty('--font-scripture', fontVal);

        // 영문 폰트 패밀리 매핑
        const engMap = {
            'eb-garamond': "'EB Garamond', Georgia, serif",
            'georgia': "Georgia, serif",
            'inter': "'Inter', sans-serif",
            'outfit': "'Outfit', sans-serif"
        };
        const engVal = engMap[this.state.englishFont] || engMap['eb-garamond'];
        document.documentElement.style.setProperty('--font-english', engVal);

        // 붙여읽기 (문단 단위 vs 절 단위)
        const viewport = document.getElementById('verses-viewport');
        if (viewport) {
            viewport.classList.toggle('mode-paragraph', this.state.viewMode === 'paragraph');
        }

        // 표시 옵션 클래스 토글
        document.body.classList.toggle('hide-stitles', !this.state.showStitles);
        document.body.classList.toggle('hide-crossrefs', !this.state.showCrossrefs);
        document.body.classList.toggle('hide-verse-nums', !this.state.showVerseNums);
        document.body.classList.toggle('show-red-letters', this.state.showRedLetters);
        document.body.classList.toggle('focus-mode-active', this.state.isFocusMode);

        this.updateVersionUI();
        this.saveSettings();
    },

    // 7. 번역본 UI 갱신 및 모달 제어
    updateVersionUI() {
        const pillText = document.getElementById('current-version-pill-text');
        const priName = this.getVersionName(this.state.primaryVersion);
        const compName = this.getVersionName(this.state.compareVersion);

        if (pillText) {
            pillText.textContent = this.state.isCompareMode 
                ? `${priName} | ${compName}` 
                : priName;
        }

        const priSelect = document.getElementById('select-primary-ver');
        if (priSelect) priSelect.value = this.state.primaryVersion;

        const compSelect = document.getElementById('select-compare-ver');
        if (compSelect) {
            compSelect.value = this.state.compareVersion;
            compSelect.style.display = this.state.isCompareMode ? 'block' : 'none';
        }

        const chkModal = document.getElementById('chk-modal-compare-mode');
        if (chkModal) chkModal.checked = this.state.isCompareMode;

        const chkHeader = document.getElementById('chk-compare-mode');
        if (chkHeader) chkHeader.checked = this.state.isCompareMode;

        // 상시 빠른 대조 버튼 스타일 & 텍스트 동기화
        const quickBtn = document.getElementById('btn-quick-toggle-compare');
        if (quickBtn) quickBtn.classList.toggle('active', this.state.isCompareMode);

        const quickText = document.getElementById('quick-compare-text');
        if (quickText) quickText.textContent = this.state.isCompareMode ? '대조 ON' : '대조';

        this.updateCurrentBookMeta();
    },

    getVersionName(code) {
        const names = {
            'rv': '개역개정', 'ko': '개역한글', 'ez': '쉬운성경', 'wr': '우리말성경',
            'nw': '새번역', 'nv': 'NIV', 'nt': 'NLT', 'es': 'ESV', 'nb': 'NASB', 'kj': 'KJV'
        };
        return names[code] || code.toUpperCase();
    },

    // 번역본 모달 임시 상태 관리
    versionModalState: {
        activeTab: 'primary',
        tempPrimary: 'rv',
        tempCompare: 'nv',
        tempIsCompare: false
    },

    openVersionModal() {
        this.versionModalState = {
            activeTab: 'primary',
            tempPrimary: this.state.primaryVersion,
            tempCompare: this.state.compareVersion,
            tempIsCompare: this.state.isCompareMode
        };

        // 탭 UI 초기화
        document.getElementById('tab-primary-ver')?.classList.add('active');
        document.getElementById('tab-compare-ver')?.classList.remove('active');

        this.updateVersionModalUI();
        this.openModal('modal-versions');
    },

    updateVersionModalUI() {
        const { activeTab, tempPrimary, tempCompare, tempIsCompare } = this.versionModalState;

        // 상단 요약 바 갱신
        const sumPri = document.getElementById('summary-primary-val');
        if (sumPri) sumPri.textContent = this.getVersionName(tempPrimary);

        const sumComp = document.getElementById('summary-compare-val');
        if (sumComp) {
            sumComp.textContent = tempIsCompare ? this.getVersionName(tempCompare) : '대조 안 함';
            sumComp.style.color = tempIsCompare ? 'var(--brand-primary)' : 'var(--text-muted)';
        }

        // 대조 탭일 때 또는 대조 활성화 체크박스 갱신
        const chkModal = document.getElementById('chk-modal-compare-mode');
        if (chkModal) chkModal.checked = tempIsCompare;

        // 활성 탭에 따른 카드 선택 스타일 갱신
        const currentSelected = activeTab === 'primary' ? tempPrimary : tempCompare;
        document.querySelectorAll('.version-card-btn').forEach(btn => {
            const v = btn.dataset.ver;
            btn.classList.toggle('active', v === currentSelected);
        });
    },

    applySelectedVersions() {
        const { tempPrimary, tempCompare, tempIsCompare } = this.versionModalState;
        
        this.state.primaryVersion = tempPrimary;
        this.state.compareVersion = tempCompare;
        this.state.isCompareMode = tempIsCompare;

        this.updateVersionUI();
        this.saveSettings();
        window.BibleReader?.reload();
        this.closeModal('modal-versions');

        const priName = this.getVersionName(tempPrimary);
        const compName = this.getVersionName(tempCompare);

        this.showToast(tempIsCompare 
            ? `[${priName}]와 [${compName}] 나란히 대조 보기가 적용되었습니다.` 
            : `기본 번역본 [${priName}]이 적용되었습니다.`);
    },

    // 8. 모달 제어
    openModal(modalId) {
        const m = document.getElementById(modalId);
        if (m) {
            m.classList.add('open');
            if (window.lucide) window.lucide.createIcons();
        }
    },

    closeModal(modalId) {
        const m = document.getElementById(modalId);
        if (m) m.classList.remove('open');
    },

    closeAllModals() {
        document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('open'));
    },

    // 8. 토스트 알림
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast-msg toast-${type}`;
        toast.innerHTML = `<i data-lucide="info" class="icon-small"></i> <span>${message}</span>`;
        container.appendChild(toast);

        if (window.lucide) window.lucide.createIcons();

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // 9. 로컬 저장소 환경설정 동기화
    saveSettings() {
        const config = {
            currentUnitCode: this.state.currentUnitCode,
            primaryVersion: this.state.primaryVersion,
            compareVersion: this.state.compareVersion,
            isCompareMode: this.state.isCompareMode,
            theme: this.state.theme,
            fontSize: this.state.fontSize,
            lineHeight: this.state.lineHeight,
            viewMode: this.state.viewMode,
            koreanFont: this.state.koreanFont,
            englishFont: this.state.englishFont,
            showStitles: this.state.showStitles,
            showCrossrefs: this.state.showCrossrefs,
            showVerseNums: this.state.showVerseNums,
            showRedLetters: this.state.showRedLetters,
            isFocusMode: this.state.isFocusMode
        };
        localStorage.setItem('wordbible_app_settings', JSON.stringify(config));
    },

    loadSettings() {
        try {
            const saved = JSON.parse(localStorage.getItem('wordbible_app_settings') || localStorage.getItem('godpeople_bible_settings'));
            if (saved) {
                this.state = { ...this.state, ...saved };
                
                // UI 동기화
                const priSelect = document.getElementById('select-primary-ver');
                if (priSelect) priSelect.value = this.state.primaryVersion;

                const compSelect = document.getElementById('select-compare-ver');
                if (compSelect) compSelect.value = this.state.compareVersion;

                const chkComp = document.getElementById('chk-compare-mode');
                if (chkComp) {
                    chkComp.checked = this.state.isCompareMode;
                    if (compSelect) compSelect.style.display = this.state.isCompareMode ? 'block' : 'none';
                }

                const fontSlider = document.getElementById('slider-font-size');
                if (fontSlider) fontSlider.value = this.state.fontSize;
                const fontLabel = document.getElementById('font-size-val');
                if (fontLabel) fontLabel.textContent = `${this.state.fontSize}px`;

                const lineSlider = document.getElementById('slider-line-height');
                if (lineSlider) lineSlider.value = this.state.lineHeight;
                const lineLabel = document.getElementById('line-height-val');
                if (lineLabel) lineLabel.textContent = `${this.state.lineHeight}`;

                const stitleChk = document.getElementById('chk-show-stitles');
                if (stitleChk) stitleChk.checked = this.state.showStitles;

                const crossChk = document.getElementById('chk-show-crossref-marks');
                if (crossChk) crossChk.checked = this.state.showCrossrefs;

                const numChk = document.getElementById('chk-show-verse-nums');
                if (numChk) numChk.checked = this.state.showVerseNums;

                const redChk = document.getElementById('chk-show-red-letters');
                if (redChk) redChk.checked = this.state.showRedLetters;

                const focusChk = document.getElementById('chk-focus-mode');
                if (focusChk) focusChk.checked = this.state.isFocusMode;

                // 뷰모드 버튼 동기화
                document.querySelectorAll('.viewmode-btn').forEach(b => {
                    b.classList.toggle('active', b.dataset.mode === this.state.viewMode);
                });

                // 서체 버튼 동기화
                document.querySelectorAll('.font-choice-btn').forEach(b => {
                    b.classList.toggle('active', b.dataset.font === this.state.koreanFont);
                });

                document.querySelectorAll('.font-eng-btn').forEach(b => {
                    b.classList.toggle('active', b.dataset.fontEng === this.state.englishFont);
                });
            }
        } catch (e) {}
    },

    handleUrlHash() {
        const hash = window.location.hash.substring(1);
        if (hash) {
            const params = new URLSearchParams(hash);
            const unit = params.get('unit');
            const jeol = params.get('jeol');
            if (unit) {
                this.state.currentUnitCode = parseInt(unit, 10);
                this.state.currentJeol = parseInt(jeol, 10) || 1;
            }
        }
    },

    // 10. PWA Service Worker 등록 및 즉시 강제 갱신
    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').then((reg) => {
                    // 배포 즉시 최신 버전 강제 체크
                    reg.update();
                }).catch(err => {
                    console.log('SW registration note:', err);
                });
            });
        }
    }
};

// DOM 로드 완료 시 구동
document.addEventListener('DOMContentLoaded', () => {
    window.BibleApp.init();
});
