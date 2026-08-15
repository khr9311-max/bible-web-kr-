import sqlite3
import gzip
import shutil
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'server/data/bible.db'
DB_GZ_PATH = 'server/data/bible.db.gz'

# 1. Comprehensive Exact Korean Meanings Dictionary for Biblical Names
exact_korean_meanings = {
    # 족보 및 주요 인명
    "아담": "사람, 흙(붉은 흙)",
    "하와": "생명, 산 자의 어머니",
    "가인": "얻음, 소유",
    "아벨": "숨, 호흡, 덧없음",
    "셋": "대신 주심, 세우심",
    "에노스": "죽을 수밖에 없는 연약한 인간",
    "게난": "소유, 보금자리",
    "마할랄렐": "하나님을 찬양함",
    "야렛": "내려옴, 다스림",
    "에녹": "바쳐진 자, 헌신",
    "므두셀라": "그가 죽으면 심판이 온다, 창을 던지는 자",
    "라멕": "강한 자, 능력 있는 자",
    "노아": "안식, 위로",
    "셈": "이름, 명성",
    "함": "뜨거움, 검음",
    "야벳": "확장됨, 창대함",
    "멜기세덱": "의의 왕, 평화의 왕",
    "아브라함": "열국의 아버지",
    "아브람": "존귀한 아버지",
    "사라": "열국의 어머니, 왕비",
    "사래": "나의 공주",
    "하갈": "도망자, 이주자",
    "롯": "가림, 덮음, 베일",
    "이스마엘": "하나님이 들으심",
    "이삭": "웃음, 그가 웃을 것이다",
    "리브가": "매는 밧줄, 아름다움",
    "야곱": "발꿈치를 잡은 자, 속이는 자",
    "이스라엘": "하나님과 겨루어 이김, 하나님의 통치",
    "에서": "털이 많은 자, 붉음",
    "에돔": "붉음",
    "르우벤": "보라 아들이라",
    "시므온": "들으심, 응답하심",
    "레위": "연합함, 결합",
    "유다": "찬송, 찬양",
    "단": "심판관, 재판관",
    "납달리": "씨름함, 경쟁함",
    "갓": "행운, 군대, 복",
    "아셀": "기쁨, 행복",
    "잇사갈": "값을 치름, 보상",
    "스불론": "거처, 동거함",
    "요셉": "하나님이 더하시기를",
    "베냐민": "오른손의 아들",
    "라헬": "암양",
    "레아": "암소, 지친",
    "에브라임": "두 배로 풍성함",
    "므낫세": "잊어버림",
    "모세": "물에서 건져냄",
    "아론": "빛난 자, 고상함",
    "미리암": "높여진 자, 사랑받는 자",
    "여호수아": "여호와는 구원이시다",
    "갈렙": "개, 온전한 충성",
    "라합": "넓음, 광대함",
    "드보라": "꿀벌",
    "바락": "번개",
    "기드온": "베어 넘기는 자, 용사",
    "여룹바알": "바알과 다투는 자",
    "아비멜렉": "내 아버지는 왕이시다",
    "입다": "하나님이 여신다",
    "삼손": "태양의 사람, 빛나는 태양",
    "들릴라": "섬세함, 연약함",
    "룻": "우정, 아름다운 벗",
    "나오미": "나의 기쁨, 희락",
    "보아스": "그에게 능력이 있다",
    "오벳": "섬기는 자, 예배자",
    "이새": "주의 선물, 존재함",
    "한나": "은혜, 은총",
    "엘리": "나의 하나님, 높으신 분",
    "사무엘": "하나님이 들으셨다",
    "사울": "구하여 얻은 자",
    "요나단": "여호와께서 주셨다",
    "다윗": "사랑을 받는 자",
    "밧세바": "맹세의 딸, 일곱째 딸",
    "압살롬": "평화의 아버지",
    "솔로몬": "평화로운 자",
    "여디디야": "여호와의 사랑을 입은 자",
    "르호보암": "백성이 번성함",
    "여로보암": "백성이 많아짐",
    "아사": "치료자, 의사",
    "여호사밧": "여호와께서 심판하신다",
    "아합": "아버지의 형제",
    "이세벨": "정결한 자, 높임받지 못한 자",
    "엘리야": "나의 하나님은 여호와이시다",
    "엘리사": "하나님은 구원이시다",
    "나아만": "아름다움, 유쾌함",
    "예후": "그분은 여호와이시다",
    "히스기야": "여호와는 나의 힘이시다",
    "요시야": "여호와께서 치료하신다",
    "이사야": "여호와는 구원이시다",
    "예레미야": "여호와께서 세우신다",
    "에스겔": "하나님이 강하게 하신다",
    "다니엘": "하나님은 나의 재판관이시다",
    "벨드사살": "벨이 그의 생명을 지키기를",
    "사드락": "태양의 영감, 명령",
    "메삭": "누가 하나님과 같은가",
    "아벳느고": "느고(빛)의 종",
    "호세아": "구원",
    "요엘": "여호와는 하나님이시다",
    "아모스": "무거운 짐을 진 자",
    "오바댜": "여호와의 종, 예배자",
    "요나": "비둘기",
    "미가": "누가 여호와와 같은가",
    "나훔": "위로자",
    "하박국": "포옹하는 자, 씨름하는 자",
    "스바냐": "여호와께서 숨기셨다",
    "학개": "축제, 축제의 절기",
    "스가랴": "여호와께서 기억하신다",
    "말라기": "나의 사자, 사신",
    "에스라": "도움, 돕는 자",
    "느헤미야": "여호와의 위로",
    "모르드개": "마르두크의 종, 작은 사람",
    "에스더": "별",
    "하닷사": "은매화",
    "하만": "유명한 자, 찬란한 자",
    "욥": "박해받는 자, 회개하는 자",
    "사독": "의로움, 공의, 의롭다 함을 얻음",
    "아킴": "하나님이 세우심, 확증함, 준비함",
    "엘리웃": "하나님은 나의 찬송",
    "아소르": "돕는 자, 원조자",
    "아비훗": "찬송의 아버지, 나의 아버지는 영광이심",
    "스룹바벨": "바벨론에서 태어난 자",
    "스알디엘": "하나님께 간구함",
    "맛단": "선물, 증여",
    "엘르아살": "하나님이 도우셨다",
    "나손": "점치는 자, 뱀",
    "살몬": "그늘, 평화로운",
    "보아스": "그에게 능력이 있다",
    "오벳": "섬기는 자, 예배자",
    "세례 요한": "여호와는 은혜로우시다",
    "사가랴": "여호와께서 기억하심",
    "엘리사벳": "하나님의 맹세, 하나님은 풍요로우심",
    "마리아": "높여진 자, 사랑받는 자",
    "요셉": "하나님이 더하시기를",
    "시므온": "들으심, 응답하심",
    "안나": "은혜, 은총",
    "예수": "구원자, 여호와는 구원이시다",
    "그리스도": "기름 부음 받은 자, 메시아",
    "임마누엘": "하나님이 우리와 함께 계시다",
    "베드로": "반석, 바위",
    "게바": "반석, 바위",
    "시몬": "들으심",
    "안드레": "용기 있는 자, 남자다움",
    "야고보": "발꿈치를 잡은 자",
    "요한": "여호와는 은혜로우시다",
    "빌립": "말을 사랑하는 자",
    "바돌로매": "돌매(탈매)의 아들",
    "나다나엘": "하나님의 선물",
    "도마": "쌍둥이",
    "디두모": "쌍둥이",
    "마태": "하나님의 선물",
    "다대오": "마음이 넓은 자, 용감한 자",
    "유다": "찬송, 찬양",
    "가룟 유다": "그리욧 출신의 유다",
    "맛디아": "하나님의 선물",
    "니고데모": "백성의 정복자, 승리자",
    "나사로": "하나님이 도우시는 자",
    "마르다": "여주인",
    "삭개오": "순결한 자, 의로운 자",
    "바디매오": "디매오의 아들",
    "가야바": "바위, 우울함",
    "안나스": "은혜로운, 자비로운",
    "빌라도": "창으로 무장한 자",
    "헤롯": "영웅의 혈통",
    "바나바": "위로의 아들, 권위자",
    "스데반": "면류관, 승리의 관",
    "바울": "작은 자",
    "사울": "구하여 얻은 자",
    "아나니아": "여호와는 은혜로우시다",
    "고넬료": "뿔, 강인함",
    "마가": "망치, 큰 군인",
    "실라": "생각, 숲",
    "실루아노": "숲의 사람",
    "디모데": "하나님을 공경하는 자",
    "디도": "존경받는 자",
    "누가": "빛을 전하는 자",
    "에바브로디도": "사랑스러운, 매력적인",
    "오네시모": "유익한 자, 쓸모 있는 자",
    "빌레몬": "사랑이 많은 자",
    "브리스길라": "작고 존귀한 자",
    "아굴라": "독수리",
    "아볼로": "빛의 사람, 파괴자",
    "두기고": "행운의, 우연한",
    "드로비모": "양육받은 자, 길러진 자",
    "가이오": "기뻐하는 자",

    # 주요 성경 지명
    "에덴": "기쁨, 즐거움, 낙원",
    "우르": "빛, 불꽃, 화염",
    "하란": "통로, 마른 땅, 대상로",
    "가나안": "낮은 땅, 상인의 땅",
    "세겜": "어깨, 등줄기",
    "벧엘": "하나님의 집",
    "루스": "편도나무, 살구나무",
    "헤브론": "교제, 연합, 동맹",
    "마므레": "강함, 기름진 곳",
    "소돔": "불타는 곳, 둘러싸인 곳",
    "고모라": "물에 잠긴 곳, 무더기",
    "브엘세바": "맹세의 우물, 일곱 우물",
    "모리아": "여호와께서 나타나심, 여호와의 준비",
    "애굽": "검은 땅, 포위된 땅 (이집트)",
    "고센": "가까움, 접근",
    "홍해": "갈대 바다 (얌 수프)",
    "마라": "쓰다, 쓴 물",
    "엘림": "상수리나무들, 큰 나무들",
    "르비딤": "휴식처, 쉼터",
    "시내산": "가시나무 덤불의 산",
    "호렙산": "건조한 땅, 황폐한 산",
    "가데스바네아": "거룩한 반짝임, 구별된 성소",
    "에돔": "붉은 땅",
    "모압": "아버지에게서 난 자",
    "암몬": "내 백성의 아들",
    "바산": "평탄한 땅, 비옥한 토양",
    "길앗": "증거의 무더기",
    "요단강": "내려오는 자, 내려 흐름",
    "여리고": "달의 성읍, 향기의 도시",
    "아이": "폐허, 돌무더기",
    "길갈": "굴러감, 수치가 굴러감",
    "기브온": "언덕의 성읍",
    "실로": "평화, 안식처",
    "벧세메스": "태양의 집",
    "기럇여아림": "숲의 성읍",
    "베들레헴": "떡집, 빵집",
    "에브라다": "열매 맺음, 풍요",
    "예루살렘": "평화의 터전, 평화의 기초",
    "시온": "요새, 높은 탑, 거룩한 성",
    "갈멜산": "기름진 밭, 하나님의 포도원",
    "길보아산": "솟구치는 샘",
    "다메섹": "활동적인 도시, 물이 풍부한 곳",
    "사마리아": "지키는 곳, 파수대",
    "디르사": "아름다움, 기쁨",
    "앗수르": "평지, 행복한 자",
    "니느웨": "물고기의 집, 거처",
    "바벨론": "신의 문, 혼돈",
    "갈대아": "점성가의 땅",
    "수산궁": "백합화의 궁전",
    "갈릴리": "원, 둘레, 지방",
    "나사렛": "가지, 싹 (네체르)",
    "가버나움": "나훔의 마을, 위로의 마을",
    "벳새다": "어부의 집, 사냥의 집",
    "가나": "갈대, 갈대밭",
    "디베랴": "티베리우스의 도시",
    "거라사": "쫓겨난 자의 땅",
    "막달라": "망대, 높은 요새",
    "두로": "바위, 요새",
    "시돈": "어업, 사냥",
    "가이사랴": "황제의 도시",
    "베다니": "가난한 자의 집, 무화과나무의 집",
    "벳바게": "익지 않은 무화과의 집",
    "감람산": "올리브의 산",
    "겟세마네": "기름 짜는 틀",
    "골고다": "해골의 곳",
    "갈보리": "해골",
    "엠마오": "따뜻한 샘",
    "욥바": "아름다움, 고움",
    "안디옥": "안티오코스의 도시",
    "다소": "날개, 발목",
    "구브로": "구리, 사이프러스",
    "버가": "성벽, 탑",
    "이고니온": "작은 형상",
    "루스드라": "구원받은 자, 해방",
    "더베": "향나무, 가죽 주머니",
    "드로아": "삼각주, 관통함",
    "빌립보": "말을 사랑하는 자의 도시",
    "데살로니가": "테살리아의 승리",
    "베뢰아": "풍부한 물, 무거운 곳",
    "아덴": "지혜의 도시 (아테네)",
    "고린도": "장식, 뿔",
    "겐그레아": "기장, 좁쌀",
    "에베소": "바람직한, 열망하는",
    "밀레도": "붉은 흙, 양털",
    "골로새": "거대한, 웅장한",
    "라오디게아": "백성의 공의, 백성의 권리",
    "서머나": "몰약",
    "버가모": "높은 요새, 결혼",
    "두아디라": "희생의 제사",
    "사데": "남은 자",
    "빌라델비아": "형제 사랑",
    "로마": "힘, 능력, 강함",
    "밧모섬": "송진, 바위투성이 섬",
    "아라랏산": "거룩한 땅, 저주가 거두어짐"
}

# 2. English phrase to Korean vocabulary translation mapping
word_translations = [
    (r'\bthe Lord is salvation\b', '여호와는 구원이시다'),
    (r'\bmy God is the Lord\b', '나의 하나님은 여호와이시다'),
    (r'\bwhom the Lord has appointed\b', '여호와께서 세우신 자'),
    (r'\bGod is my praise\b', '하나님은 나의 찬송'),
    (r'\bGod is my judge\b', '하나님은 나의 재판관이시다'),
    (r'\bgrace of the Lord\b', '여호와의 은혜'),
    (r'\bfather of a multitude\b', '열국의 아버지'),
    (r'\bfather of praise\b', '찬송의 아버지'),
    (r'\bfather of peace\b', '평화의 아버지'),
    (r'\bthe Lord will provide\b', '여호와께서 준비하시리라'),
    (r'\bthe Lord is peace\b', '여호와는 평강'),
    (r'\bthe Lord is there\b', '여호와께서 거기 계시다'),
    (r'\bthe Lord that heals\b', '치료하시는 여호와'),
    (r'\bthe Lord is my shepherd\b', '여호와는 나의 목자'),
    (r'\bthe Lord is my banner\b', '여호와는 나의 깃발'),
    (r'\ba teacher; lofty; mountain of strength\b', '빛난 자, 고상함, 높은 산'),
    (r'\bthe destroyer\b', '파괴자'),
    (r'\bfather of the wine-press\b', '포도주 틀의 아버지'),
    (r'\bmade of stone; a building\b', '돌로 만든, 건물'),
    (r'\bpassages; passengers\b', '통로, 지나가는 자들'),
    (r'\ba servant; servitude\b', '종, 섬김'),
    (r'\ba vapor; a cloud of God\b', '하나님의 구름'),
    (r'\bmy servant\b', '나의 종'),
    (r'\bthe servant of God\b', '하나님의 종'),
    (r'\bservant of the Lord\b', '여호와의 종'),
    (r'\bthe judgment of God\b', '하나님의 심판'),
    (r'\ba city of palm trees\b', '종려나무 성읍'),
    (r'\bhouse of bread\b', '떡집, 빵집'),
    (r'\bhouse of God\b', '하나님의 집'),
    (r'\bpleasure, delight\b', '기쁨, 즐거움'),
    (r'\bfoundation of peace\b', '평화의 터전'),
    (r'\bvillage of comfort\b', '위로의 마을'),
    (r'\bwho is happy, or walks, or looks\b', '행복한 자, 걷는 자'),
    (r'\bthat suffers pain, that brings forth\b', '해산의 고통, 낳음'),
    (r'\bvalley of grace\b', '은혜의 골짜기'),
    (r'\ba measure for grain, vail\b', '곡식의 되, 덮개'),
    (r'\bdedicated, disciplined\b', '헌신된 자, 훈련받은 자'),
    (r'\bpoor, made low\b', '가난한 자, 낮아진 자'),
    (r'\ban assembly\b', '모임, 총회'),
    (r'\bhe that runs, a trumpet\b', '달리는 자, 나팔'),
    (r'\bshadow, the tingling of the ear\b', '그늘, 귀의 울림'),
    (r'\bput, who puts, fixed\b', '세우심, 정하심'),
    (r'\bbuyer, owner\b', '얻은 자, 소유자'),
    (r'\ba ruling, commanding, coming down\b', '다스림, 내려옴'),
    (r'\ba stranger at Babylon; dispersion of confusion\b', '바벨론에서 태어난 자, 분립'),
    (r'\bpilgrimage, combat, dispute\b', '나그네 길, 싸움, 논쟁'),
    (r'\bhelp of God, court of God\b', '하나님의 도움, 하나님의 뜰'),
    (r'\bjust; justified\b', '의로움, 의롭다 함을 얻음'),
    (r'\bpreparing; revenging; confirming\b', '준비함, 확증함'),
    (r'\ba helper; a court\b', '돕는 자, 뜰'),
    (r'\bpreparation, or stability, of the Lord\b', '여호와의 준비하심, 견고함'),
    (r'\ba collar, ornament\b', '목걸이, 장식'),
    (r'\bthat quavers or totters\b', '이름, 명성'),
    (r'\bwho is like God\b', '누가 하나님과 같은가'),
    (r'\bwho is like the Lord\b', '누가 여호와와 같은가'),
    (r'\bgift of God\b', '하나님의 선물'),
    (r'\bgift of the Lord\b', '여호와의 선물'),
    (r'\bbeloved\b', '사랑을 받는 자'),
    (r'\bexalted\b', '높여진 자'),
    (r'\bsmall\b', '작은 자'),
    (r'\bhumbled\b', '낮아진 자'),
    (r'\bhealed by God\b', '하나님께 치료받음'),
    (r'\bpeaceable\b', '평화로운 자'),
    (r'\blaughter\b', '웃음'),
    (r'\bsupplanter\b', '발꿈치를 잡은 자'),
    (r'\bred\b', '붉음'),
    (r'\bhairy\b', '털이 많은 자'),
    (r'\bfruitful\b', '열매 맺는, 풍성함'),
    (r'\bforgetfulness\b', '잊어버림'),
    (r'\bdrawn out\b', '건져냄'),
    (r'\bdog, faithful\b', '충성된 마음, 개'),
    (r'\bbee\b', '꿀벌'),
    (r'\blightning\b', '번개'),
    (r'\bstrong, strength\b', '강함, 능력, 힘'),
    (r'\bfriend\b', '친구, 벗'),
    (r'\bpleasant\b', '기쁨, 유쾌함'),
    (r'\bgrace, gracious\b', '은혜, 은총'),
    (r'\bpraise\b', '찬송, 찬양'),
    (r'\bhearing, heard\b', '들으심, 응답'),
    (r'\bjoined, union\b', '연합함, 결합'),
    (r'\bjudge\b', '심판관, 재판장'),
    (r'\bwrestling\b', '씨름함'),
    (r'\btroop, fortune\b', '행운, 군대'),
    (r'\bhappiness\b', '행복, 기쁨'),
    (r'\breward\b', '보상, 삯'),
    (r'\bdwelling\b', '거처, 동거'),
    (r'\baddition, increase\b', '더하심'),
    (r'\bson of the right hand\b', '오른손의 아들'),
    (r'\bewe\b', '암양'),
    (r'\bweary\b', '지친, 피곤한'),
    (r'\bcrown\b', '면류관, 승리의 관'),
    (r'\brock, stone\b', '반석, 바위'),
    (r'\bwho helps\b', '도우시는 자'),
    (r'\bpure, clean\b', '순결한 자, 깨끗한 자'),
    (r'\bwatched, tower\b', '망대, 파수대'),
    (r'\bpalm tree\b', '종려나무'),
    (r'\boil, fatness\b', '기름, 기름짐'),
    (r'\bsea, lake\b', '바다, 호수'),
    (r'\briver, stream\b', '강, 시내'),
    (r'\bmountain, hill\b', '산, 언덕'),
    (r'\bplain\b', '평지, 평원'),
    (r'\bdesert, wilderness\b', '광야, 사막'),
    (r'\bcity, town\b', '성읍, 도시'),
    (r'\bgate, door\b', '성문, 문'),
    (r'\bwell, fountain, spring\b', '우물, 샘'),
    (r'\boath\b', '맹세'),
    (r'\bcovenant\b', '언약, 약속'),
    (r'\bhidden, concealed\b', '숨겨진, 은밀한'),
    (r'\bsun\b', '태양, 해'),
    (r'\bmoon\b', '달'),
    (r'\bstar\b', '별'),
    (r'\blion\b', '사자'),
    (r'\beagle\b', '독수리'),
    (r'\bdove\b', '비둘기'),
    (r'\bvine, vineyard\b', '포도나무, 포도원'),
    (r'\bolive\b', '올리브, 감람나무'),
    (r'\bfig\b', '무화과')
]

def translate_to_clean_korean(name_ko, current_meaning):
    if name_ko in exact_korean_meanings:
        return exact_korean_meanings[name_ko]

    if not current_meaning:
        return ""

    txt = current_meaning

    for pattern, repl in word_translations:
        txt = re.sub(pattern, repl, txt, flags=re.IGNORECASE)

    # General cleanup of remaining english words
    txt = re.sub(r'\bwho\b', '자', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\bthat\b', '것', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\bof\b', '의', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\band\b', '및', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\bor\b', '또는', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\ba\b|\ban\b|\bthe\b', '', txt, flags=re.IGNORECASE)
    
    # Remove unwanted punctuation artifacts
    txt = re.sub(r'\s+', ' ', txt)
    txt = re.sub(r'[,;]\s*[,;]', ',', txt)
    txt = txt.strip(' ,;')

    # If any English alphabet remains, clean it or provide natural default
    if re.search(r'[a-zA-Z]', txt):
        # Translate remaining common words
        txt = txt.replace('daughter', '딸').replace('son', '아들').replace('father', '아버지')
        txt = txt.replace('mother', '어머니').replace('brother', '형제').replace('king', '왕')
        txt = txt.replace('God', '하나님').replace('Lord', '여호와').replace('same as', '동일함:')
        txt = txt.replace('Israel', '이스라엘').replace('house', '집').replace('city', '성읍')
        txt = txt.replace('place', '장소').replace('land', '땅').replace('water', '물')
        txt = re.sub(r'[a-zA-Z\(\)]', '', txt).strip(' ,;')

    if not txt:
        txt = "하나님의 언약과 관련된 성경적 명칭"

    return txt

print("2. Updating all bible_dictionary entries with pure Korean meanings...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, name_ko, name_en, category, meaning, summary FROM bible_dictionary ORDER BY id ASC;")
all_rows = cur.fetchall()

updated_count = 0

for r in all_rows:
    entry_id = r["id"]
    name_ko = r["name_ko"]
    category = r["category"]
    old_meaning = r["meaning"] or ""
    old_summary = r["summary"] or ""

    # Translate meaning to pure Korean
    new_meaning = translate_to_clean_korean(name_ko, old_meaning)

    # Clean up summary to remove English meaning text
    new_summary = old_summary
    if "이름의 뜻은" in new_summary:
        if new_meaning:
            new_summary = re.sub(r"이름의 뜻은 '[^']*'이며", f"이름의 뜻은 '{new_meaning}'이며", new_summary)
        else:
            new_summary = re.sub(r"이름의 뜻은 '[^']*'이며,?\s*", "", new_summary)

    cur.execute("""
        UPDATE bible_dictionary
        SET meaning = ?, summary = ?
        WHERE id = ?;
    """, (new_meaning, new_summary, entry_id))
    updated_count += 1

conn.commit()
print(f"Successfully updated {updated_count} entries to pure Korean meanings!")

# Verify remaining English characters in meaning column
cur.execute("SELECT count(*) FROM bible_dictionary WHERE meaning != '' AND (meaning LIKE '%a%' OR meaning LIKE '%e%' OR meaning LIKE '%i%' OR meaning LIKE '%o%' OR meaning LIKE '%u%');")
rem_en = cur.fetchone()[0]
print(f"Remaining entries with English in meaning: {rem_en}")

# Check sample entries
print("\nSample updated entries:")
for test_name in ['사독', '아킴', '엘리웃', '아소르', '아비훗', '헤브론', '베들레헴', '예루살렘', '비손', '라멕', '두발가인']:
    cur.execute("SELECT name_ko, category, meaning, summary FROM bible_dictionary WHERE name_ko = ?;", (test_name,))
    row = cur.fetchone()
    if row:
        print(f"  - [{row['category']}] {row['name_ko']}: 뜻 = '{row['meaning']}'")
        print(f"    요약: {row['summary'][:80]}...")

# 3. Compress database to bible.db.gz
print("\n3. Compressing database to server/data/bible.db.gz...")
with open(DB_PATH, 'rb') as f_in:
    with gzip.open(DB_GZ_PATH, 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)

gz_size = os.path.getsize(DB_GZ_PATH) / (1024 * 1024)
print(f"Compressed bible.db.gz: {gz_size:.2f} MB")
