# 말씀성경 (WordBible) 프리미엄 풀스택 웹 애플리케이션 (PWA)

풍부한 성경 역본 데이터와 스마트 기능들을 현대적 웹 표준으로 구현한 **차세대 풀스택 성경 웹 애플리케이션**입니다.  
PC, 태블릿, 스마트폰 브라우저에서 사용할 수 있으며, PWA(Progressive Web App)를 통해 네이티브 앱처럼 설치하여 오프라인에서도 사용할 수 있습니다.

---

## 🌟 주요 기능

1. **📖 성경 본문 뷰어 & 다역본 대조 (Compare View)**
   - 개역개정, 개역한글, 쉬운성경, 우리말성경, 새번역, NIV, NLT, ESV, NASB, KJV 등 10개 역본 지원
   - 2개 이상의 번역본을 나란히(Split View) 대조하여 열람
2. **🔤 원어 성경 분해 & 스트롱 코드 사전**
   - 37만 건의 히브리어/헬라어 원어 분해 데이터 내장
   - 단어별 원어 표기, 음역, 발음, 신학적 사전 정의 팝업 제공
3. **🔗 스마트 관주 (Cross-Reference) 탐색**
   - 20만 건 이상의 성경 상호 참조 관주를 우측 사이드 패널에서 즉시 탐색
4. **🎨 감성 말씀 이미지 카드 생성기**
   - 마음에 드는 구절을 모던한 그라데이션 배경 위에 배치하여 고해상도(1080x1080) PNG 다운로드 및 SNS 공유
5. **🔊 TTS 음성 낭독 & 구절별 실시간 하이라이트 (Audio Sync)**
   - 성경 구절을 실시간으로 읽어주며, 읽고 있는 절이 자동으로 하이라이트되고 스크롤
6. **📊 맥체인 통독 플래너 & 진도율 차트**
   - 365일 맥체인 성경 읽기표 스케줄 제공
   - 구약/신약 진도율 통계 및 도넛 차트 시각화
7. **🔍 초고속 키워드 전문 검색**
   - 31,105구절 전권 실시간 0.05초 고속 검색 및 하이라이트
8. **🖍️ 개인화 기능**
   - 4색 형광펜, 북마크, 묵상 메모, 통독 완료 체크 (서버 SQLite 및 브라우저 자동 저장)
9. **🌓 3가지 프리미엄 테마**
   - 딥 다크 모드 / 편안한 세피아 모드 / 깔끔한 라이트 모드

---

## 🚀 빠른 시작 (로컬 실행)

### 사전 요구사항
* Python 3.10+ (또는 Node.js v22 이상)

### 실행 방법
```bash
# Python 서버 실행
python server/server.py
```
웹 브라우저에서 `http://localhost:3000`으로 접속합니다.

---

## 🌐 서버 URL 배포 및 운영 가이드

### 방법 1: Docker 컨테이너 배포 (가장 추천)
```bash
# Docker 이미지 빌드
docker build -t wordbible-app .

# Docker 컨테이너 실행 (포트 80에 바인딩)
docker run -d -p 80:3000 --name bible-app --restart always wordbible-app
```

### 방법 2: PM2를 이용한 VPS / 클라우드 서버 배포
```bash
npm install -g pm2
cd server
pm2 start "node --experimental-sqlite server.js" --name "bible-app"
pm2 save
pm2 startup
```

### 방법 3: Nginx 리버스 프록시 연동 (HTTPS 적용)
```nginx
server {
    listen 80;
    server_name bible.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name bible.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/bible.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bible.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 📱 PWA 앱 설치 방법
1. 모바일(Safari/Chrome) 또는 PC 크롬 브라우저에서 배포된 URL로 접속합니다.
2. 브라우저 주소창 우측의 **[설치]** 아이콘 또는 모바일 브라우저 메뉴의 **[홈 화면에 추가]**를 클릭합니다.
3. 앱 스토어 없이 스마트폰 홈 화면에 아이콘이 생성되며, 전체화면으로 실행됩니다.
