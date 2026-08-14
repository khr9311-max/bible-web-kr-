/**
 * 성경 66권 및 장/절 선택기 내비게이터 모듈 (navigator.js)
 */

window.BibleNav = {
    currentTab: 'OT',
    selectedBook: null,

    init() {
        this.setupTabEvents();
        this.renderBooks();
    },

    setupTabEvents() {
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.currentTab = tab.dataset.tab;
                document.querySelectorAll('.nav-tab').forEach(t => t.classList.toggle('active', t === tab));
                this.renderBooks();
            });
        });

        document.getElementById('btn-nav-back-books')?.addEventListener('click', () => {
            this.showBooksView();
        });
    },

    renderBooks() {
        const container = document.getElementById('books-grid-container');
        if (!container) return;

        const books = window.BibleApp.state.books.filter(b => b.testament === this.currentTab);
        
        let html = '';
        books.forEach(b => {
            html += `
                <div class="book-btn-card" data-book-id="${b.id}">
                    <span class="book-btn-name">${b.name}</span>
                    <span class="book-btn-sub">${b.abbr} · ${b.chapters}장</span>
                </div>
            `;
        });

        container.innerHTML = html;

        // 책 클릭 시 장 선택 화면으로 전환
        container.querySelectorAll('.book-btn-card').forEach(card => {
            card.addEventListener('click', () => {
                const bId = parseInt(card.dataset.bookId, 10);
                this.selectBook(bId);
            });
        });
    },

    selectBook(bookId) {
        const book = window.BibleApp.state.books.find(b => b.id === bookId);
        if (!book) return;

        this.selectedBook = book;
        document.getElementById('nav-selected-book-name').textContent = book.name;
        document.getElementById('nav-selected-book-chapters').textContent = `총 ${book.chapters}장`;

        const chGrid = document.getElementById('chapters-grid-container');
        let html = '';
        for (let ch = 1; ch <= book.chapters; ch++) {
            html += `<button class="chapter-num-btn" data-ch="${ch}">${ch}</button>`;
        }
        chGrid.innerHTML = html;

        chGrid.querySelectorAll('.chapter-num-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const ch = parseInt(btn.dataset.ch, 10);
                const targetUnit = (book.id * 1000) + ch;
                window.BibleApp.navigateTo(targetUnit);
            });
        });

        this.showChaptersView();
    },

    showBooksView() {
        document.getElementById('nav-books-view').style.display = 'block';
        document.getElementById('nav-chapters-view').style.display = 'none';
    },

    showChaptersView() {
        document.getElementById('nav-books-view').style.display = 'none';
        document.getElementById('nav-chapters-view').style.display = 'block';
    }
};
