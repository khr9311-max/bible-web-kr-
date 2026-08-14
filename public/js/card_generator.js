/**
 * Canvas 기반 감성 말씀 이미지 카드 생성기 모듈 (card_generator.js)
 */

window.BibleCardGen = {
    canvas: null,
    ctx: null,
    bgPreset: 'grad1',
    fontSize: 44,
    textAlign: 'center',

    init() {
        this.canvas = document.getElementById('card-canvas');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');

        this.setupEvents();
    },

    setupEvents() {
        // 배경 프리셋 선택
        document.querySelectorAll('.bg-preset-grid .bg-dot').forEach(dot => {
            dot.addEventListener('click', () => {
                this.bgPreset = dot.dataset.bg;
                document.querySelectorAll('.bg-preset-grid .bg-dot').forEach(d => d.classList.toggle('active', d === dot));
                this.drawCard();
            });
        });

        // 폰트 크기 슬라이더
        document.getElementById('card-font-slider')?.addEventListener('input', (e) => {
            this.fontSize = parseInt(e.target.value, 10);
            this.drawCard();
        });

        // 텍스트 정렬
        document.querySelectorAll('.align-btns .btn-mini').forEach(btn => {
            btn.addEventListener('click', () => {
                this.textAlign = btn.dataset.align;
                document.querySelectorAll('.align-btns .btn-mini').forEach(b => b.classList.toggle('active', b === btn));
                this.drawCard();
            });
        });

        // 텍스트 실시간 반영
        document.getElementById('card-text-input')?.addEventListener('input', () => this.drawCard());
        document.getElementById('card-ref-input')?.addEventListener('input', () => this.drawCard());

        // 다운로드 버튼
        document.getElementById('btn-download-card')?.addEventListener('click', () => this.downloadCard());
    },

    prepareCard() {
        const sorted = window.BibleReader?.getSelectedVersesSorted() || [];
        if (sorted.length > 0) {
            this.prepareCardWithMultipleVerses(sorted);
        } else {
            const verse = window.BibleReader?.chapterData?.verses?.[0];
            if (verse) {
                this.prepareCardWithMultipleVerses([verse]);
            } else {
                document.getElementById('card-text-input').value = '태초에 하나님이 천지를 창조하시니라';
                document.getElementById('card-ref-input').value = '창세기 1:1';
                this.drawCard();
            }
        }
    },

    prepareCardWithVerse(verse) {
        this.prepareCardWithMultipleVerses([verse]);
    },

    prepareCardWithMultipleVerses(verses) {
        if (!verses || verses.length === 0) return;
        const bName = window.BibleApp.state.currentBookMeta.name;
        const ch = window.BibleApp.state.currentChapter;

        let combinedText = '';
        let refText = '';

        if (verses.length === 1) {
            combinedText = window.BibleReader.getPureVerseText(verses[0].phrase_rv);
            refText = `${bName} ${ch}:${verses[0].jeol}`;
        } else {
            const isConsecutive = verses.every((val, idx) => idx === 0 || val.jeol === verses[idx - 1].jeol + 1);
            if (isConsecutive) {
                refText = `${bName} ${ch}:${verses[0].jeol}-${verses[verses.length - 1].jeol}`;
            } else {
                refText = `${bName} ${ch}:${verses.map(v => v.jeol).join(', ')}`;
            }
            combinedText = verses.map(v => `${v.jeol} ${window.BibleReader.getPureVerseText(v.phrase_rv)}`).join('\n');
        }

        // 글자 수에 따라 적절한 폰트 크기 자동 조절
        if (combinedText.length > 180) {
            this.fontSize = 28;
        } else if (combinedText.length > 100) {
            this.fontSize = 34;
        } else if (combinedText.length > 50) {
            this.fontSize = 40;
        } else {
            this.fontSize = 44;
        }

        const slider = document.getElementById('card-font-slider');
        if (slider) slider.value = this.fontSize;

        document.getElementById('card-text-input').value = combinedText;
        document.getElementById('card-ref-input').value = refText;
        this.drawCard();
    },

    drawCard() {
        if (!this.canvas || !this.ctx) return;
        const ctx = this.ctx;
        const width = this.canvas.width;
        const height = this.canvas.height;

        // 1. 배경 그리기
        this.drawBackground(ctx, width, height);

        // 2. 장식용 프레임 및 워터마크
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
        ctx.lineWidth = 2;
        ctx.strokeRect(60, 60, width - 120, height - 120);

        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.font = '600 24px "Outfit", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('HOLY BIBLE', width / 2, 110);

        // 3. 말씀 본문 텍스트
        const rawText = document.getElementById('card-text-input')?.value || '태초에 하나님이 천지를 창조하시니라';
        const refText = document.getElementById('card-ref-input')?.value || '창세기 1:1';

        ctx.fillStyle = '#ffffff';
        ctx.font = `600 ${this.fontSize}px "Noto Serif KR", Georgia, serif`;
        ctx.textAlign = this.textAlign;

        const maxTextWidth = width - 240;
        const lineHeight = this.fontSize * 1.6;
        const lines = this.wrapText(ctx, `"${rawText}"`, maxTextWidth);

        const totalTextHeight = lines.length * lineHeight;
        const startY = (height - totalTextHeight) / 2 + (this.fontSize * 0.4);

        const startX = this.textAlign === 'center' ? (width / 2) : 120;

        lines.forEach((line, i) => {
            ctx.fillText(line, startX, startY + (i * lineHeight));
        });

        // 4. 출처 텍스트 (성경 구절 위치)
        ctx.fillStyle = '#f59e0b';
        ctx.font = '600 28px "Pretendard", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`- ${refText} -`, width / 2, startY + totalTextHeight + 60);
    },

    drawBackground(ctx, w, h) {
        let grad;
        switch (this.bgPreset) {
            case 'grad1': // Deep Blue
                grad = ctx.createLinearGradient(0, 0, w, h);
                grad.addColorStop(0, '#1e3c72');
                grad.addColorStop(1, '#2a5298');
                break;
            case 'grad2': // Sunset Purple
                grad = ctx.createLinearGradient(0, 0, w, h);
                grad.addColorStop(0, '#833ab4');
                grad.addColorStop(0.5, '#fd1d1d');
                grad.addColorStop(1, '#fcb045');
                break;
            case 'grad3': // Mystic Teal
                grad = ctx.createLinearGradient(0, 0, w, h);
                grad.addColorStop(0, '#0f2027');
                grad.addColorStop(0.5, '#203a43');
                grad.addColorStop(1, '#2c5364');
                break;
            case 'grad4': // Nature Forest
                grad = ctx.createLinearGradient(0, 0, w, h);
                grad.addColorStop(0, '#134e5e');
                grad.addColorStop(1, '#71b280');
                break;
            case 'grad5': // Twilight
                grad = ctx.createLinearGradient(0, 0, w, h);
                grad.addColorStop(0, '#2b5876');
                grad.addColorStop(1, '#4e4376');
                break;
            case 'dark1': // Minimalist Dark
            default:
                grad = ctx.createLinearGradient(0, 0, w, h);
                grad.addColorStop(0, '#161922');
                grad.addColorStop(1, '#0b0c10');
                break;
        }

        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);
    },

    wrapText(ctx, text, maxWidth) {
        const words = text.split(' ');
        const lines = [];
        let currentLine = '';

        for (let i = 0; i < words.length; i++) {
            const testLine = currentLine ? `${currentLine} ${words[i]}` : words[i];
            const metrics = ctx.measureText(testLine);
            if (metrics.width > maxWidth && currentLine) {
                lines.push(currentLine);
                currentLine = words[i];
            } else {
                currentLine = testLine;
            }
        }
        if (currentLine) lines.push(currentLine);
        return lines;
    },

    downloadCard() {
        if (!this.canvas) return;
        const ref = document.getElementById('card-ref-input')?.value || '말씀카드';
        const cleanRef = ref.replace(/[\s:]+/g, '_');
        const link = document.createElement('a');
        link.download = `말씀카드_${cleanRef}.png`;
        link.href = this.canvas.toDataURL('image/png');
        link.click();

        window.BibleApp.showToast('말씀 카드가 성공적으로 다운로드되었습니다!');
    }
};
