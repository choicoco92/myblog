# ✅ 통합된 자동 포스팅 스크립트: 트렌드 뉴스 + 쿠팡 상품 삽입 (og:image 적용 포함 전체코드)

import requests, json, openai, hashlib, hmac, re, time, random
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from config import *
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import quote
from urllib.parse import urlparse, unquote
from datetime import datetime
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경변수에서 API 키 로드
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WP_URL = os.getenv('WP_URL')
WP_USERNAME = os.getenv('WP_USERNAME')
WP_PASSWORD = os.getenv('WP_PASSWORD')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
CP_ACCESS_KEY = os.getenv('CP_ACCESS_KEY')
CP_SECRET_KEY = os.getenv('CP_SECRET_KEY')

print("🔑 OPENAI_API_KEY:", OPENAI_API_KEY[:10] + "...")
print("🌐 WP_URL:", WP_URL)

openai.api_key = OPENAI_API_KEY

CATEGORY_MAP = {
    "today-trend": "🌍 오늘의 트렌드",
    "ai-tech": "🤖 AI & 기술",
    "life-hacks": "🧠 생활정보",
    "finance": "💰 금융/재테크",
    "health": "💪 건강/웰빙",
    "tech": "🔌 테크/가젯",
    "life": "🏠 라이프스타일",
    "education": "📚 교육/자격증",
    "beauty": "💄 뷰티/패션",
    "ai_generated": "🎯 AI 추천"
}

COUPANG_CATEGORY_SLUG_MAP = {
    1001: "hot-now", 1002: "hot-now", 1010: "hot-now", 1011: "kids-life",
    1013: "home-living", 1014: "daily-pick", 1015: "home-living", 1016: "tech-gadgets",
    1017: "travel-leisure", 1018: "daily-pick", 1019: "daily-pick", 1020: "daily-pick",
    1021: "daily-pick", 1024: "daily-pick", 1025: "travel-leisure", 1026: "travel-leisure",
    1029: "pet-picks", 1030: "kids-life"
}

HIGH_CPC_KEYWORDS = {
    "finance": [
        "대출", "신용카드", "보험", "주식 투자", "부동산", "펀드", "골드", "암호화폐", 
        "연봉 협상", "세금 절약", "재테크", "투자 상담", "금융 상품", "은퇴 준비",
        "개인대출", "사업자대출", "담보대출", "신용대출", "전세자금대출", "주택담보대출",
        "카드 추천", "연회비 면제", "포인트 적립", "캐시백", "할인 혜택", "무이자 할부",
        "생명보험", "건강보험", "실비보험", "암보험", "종신보험", "정기보험", "연금보험",
        "주식 매수", "ETF 투자", "펀드 투자", "채권 투자", "원자재 투자", "해외주식",
        "부동산 투자", "아파트 투자", "상가 투자", "토지 투자", "REITs", "부동산 펀드",
        "연봉 인상", "급여 협상", "성과급", "상여금", "퇴직금", "연말정산", "세무신고",
        "절세 방법", "공제 혜택", "세금 환급", "부가세", "소득세", "양도소득세",
        "재테크 방법", "투자 전략", "자산 관리", "포트폴리오", "리스크 관리",
        "투자 상담사", "재무설계", "자산 배분", "투자 성향", "투자 목표",
        "금융 상품 비교", "예금", "적금", "MMF", "CMA", "RP", "CD",
        "은퇴 준비", "노후 준비", "연금 설계", "노후 자금", "은퇴 자금",
        "가계부", "가계 수지", "가족 재무", "가정 경제", "가계 경제",
        "금융 문맹", "금융 교육", "투자 교육", "재테크 강의", "금융 상식",
        "경제 뉴스", "금융 뉴스", "투자 정보", "시장 동향", "경제 전망",
        "금리 변동", "환율 변동", "원달러", "원엔", "원유로", "원위안",
        "인플레이션", "디플레이션", "스태그플레이션", "경기 침체", "경기 회복",
        "부동산 시장", "주식 시장", "채권 시장", "외환 시장", "원자재 시장",
        "투자 심리", "시장 심리", "공포 지수", "탐욕 지수", "시장 동향",
        "투자 타이밍", "매수 타이밍", "매도 타이밍", "분산 투자", "리스크 분산"
    ],
    "health": [
        "다이어트 보조제", "영양제 추천", "탈모 치료", "건강 검진", "운동 기구", 
        "건강식품", "비타민", "프로바이오틱스", "오메가3", "콜라겐", "유산균", 
        "다이어트 식단", "헬스장", "요가", "필라테스", "마사지", "치과", "피부과",
        "다이어트 방법", "체중 감량", "살 빼는 법", "복부 지방", "허벅지 지방",
        "팔뚝 지방", "뱃살 빼기", "옆구리 빼기", "턱살 빼기", "이중턱 빼기",
        "영양제 종류", "비타민A", "비타민B", "비타민C", "비타민D", "비타민E",
        "비타민K", "칼슘", "마그네슘", "아연", "셀레늄", "크롬", "망간",
        "탈모 원인", "탈모 예방", "탈모 치료제", "탈모 샴푸", "탈모 영양제",
        "탈모 마사지", "탈모 체크", "탈모 진단", "탈모 상담", "탈모 클리닉",
        "건강 검진 항목", "종합 검진", "암 검진", "심장 검진", "뇌 검진",
        "간 검진", "신장 검진", "갑상선 검진", "유방 검진", "자궁경부 검진",
        "운동 기구 추천", "홈짐", "덤벨", "바벨", "런닝머신", "자전거",
        "스텝퍼", "크로스핏", "TRX", "요가매트", "폼롤러", "스트레칭 밴드",
        "건강식품 종류", "슈퍼푸드", "견과류", "씨앗", "건조과일", "해조류",
        "발효식품", "김치", "된장", "청국장", "나토", "요구르트", "케피어",
        "헬스장 추천", "PT", "개인트레이너", "그룹운동", "스피닝", "줌바",
        "요가 종류", "하타요가", "아쉬탕가요가", "빈야사요가", "아이엔가요가",
        "필라테스 종류", "매트 필라테스", "리포머 필라테스", "캐딜락 필라테스",
        "마사지 종류", "스웨디시 마사지", "타이 마사지", "아로마 마사지",
        "치과 추천", "치아 교정", "임플란트", "틀니", "치아 미백", "충치 치료",
        "피부과 추천", "여드름 치료", "흉터 치료", "모공 축소", "피부 재생"
    ],
    "tech": [
        "노트북 추천", "게이밍 마우스", "클라우드 호스팅", "AI 서비스", "스마트폰", 
        "태블릿", "스마트워치", "블루투스 이어폰", "게이밍 키보드", "모니터", 
        "프린터", "카메라", "드론", "로봇청소기", "스마트홈", "VPN", "웹호스팅",
        "노트북 종류", "게이밍 노트북", "업무용 노트북", "학생용 노트북", "맥북",
        "삼성 노트북", "LG 노트북", "델 노트북", "HP 노트북", "레노버 노트북",
        "게이밍 마우스 추천", "로지텍 마우스", "레이저 마우스", "스틸시리즈 마우스",
        "게이밍 키보드 추천", "기계식 키보드", "멤브레인 키보드", "무선 키보드",
        "클라우드 호스팅 비교", "AWS", "구글 클라우드", "애저", "네이버 클라우드",
        "AI 서비스 종류", "챗GPT", "클로바X", "구글 바드", "빙 챗", "AI 이미지",
        "스마트폰 추천", "아이폰", "갤럭시", "픽셀", "원플러스", "샤오미",
        "태블릿 추천", "아이패드", "갤럭시탭", "갤럭시북", "서피스", "레노버 태블릿",
        "스마트워치 추천", "애플워치", "갤럭시워치", "피트비트", "샤오미 밴드",
        "블루투스 이어폰 추천", "에어팟", "갤럭시버즈", "소니 이어폰", "보스 이어폰",
        "모니터 추천", "게이밍 모니터", "업무용 모니터", "울트라와이드", "커브드",
        "프린터 추천", "레이저 프린터", "잉크젯 프린터", "복합기", "포토 프린터",
        "카메라 추천", "DSLR", "미러리스", "액션캠", "인스턴트 카메라",
        "드론 추천", "DJI 드론", "파라로트 드론", "스카이로봇", "드론 촬영",
        "로봇청소기 추천", "다이슨", "삼성 로봇청소기", "LG 로봇청소기", "샤오미",
        "스마트홈 추천", "스마트 조명", "스마트 도어락", "스마트 카메라", "스마트 스피커",
        "VPN 추천", "노드VPN", "익스프레스VPN", "서프샤크", "프로톤VPN",
        "웹호스팅 추천", "가비아", "후이즈", "고도호스팅", "카페24", "아임웹"
    ],
    "life": [
        "이사 준비", "셀프 인테리어", "결혼 준비", "자동차 보험", "여행 상품", 
        "호텔 예약", "항공권", "렌터카", "패키지 여행", "골프", "등산", "캠핑", 
        "요리", "베이킹", "가드닝", "반려동물", "애완동물", "반려식물", "독서", "영화",
        "이사 업체", "이사 비용", "이사 체크리스트", "이사 용품", "이사 박스",
        "셀프 인테리어 방법", "인테리어 디자인", "가구 배치", "컬러 조합", "조명",
        "결혼 준비 체크리스트", "웨딩 플래너", "결혼식장", "드레스", "스튜디오",
        "자동차 보험 비교", "자동차보험료", "보험 할인", "무사고 할인", "보험 갱신",
        "여행 상품 추천", "해외여행", "국내여행", "패키지여행", "자유여행",
        "호텔 예약 사이트", "부킹닷컴", "아고다", "호텔스닷컴", "에어비앤비",
        "항공권 예약", "대한항공", "아시아나항공", "제주항공", "에어서울",
        "렌터카 예약", "렌터카 비교", "렌터카 할인", "렌터카 보험", "렌터카 업체",
        "패키지 여행 추천", "동남아 여행", "유럽 여행", "일본 여행", "중국 여행",
        "골프장 추천", "골프 레슨", "골프 클럽", "골프 용품", "골프 연습장",
        "등산 코스", "등산 용품", "등산복", "등산화", "등산 배낭",
        "캠핑장 추천", "캠핑 용품", "텐트", "침낭", "캠핑 의자",
        "요리 레시피", "요리 도구", "조리법", "요리 강의", "요리책",
        "베이킹 레시피", "베이킹 도구", "오븐", "반죽", "크림",
        "가드닝 방법", "화분", "씨앗", "비료", "정원 도구",
        "반려동물 용품", "강아지 용품", "고양이 용품", "펫샵", "동물병원",
        "반려식물 추천", "다육식물", "공기정화식물", "화분", "식물 관리",
        "독서 추천", "베스트셀러", "도서관", "독서모임", "책장",
        "영화 추천", "넷플릭스", "왓챠", "티빙", "영화관"
    ],
    "education": [
        "온라인 강의", "어학원", "자격증", "공무원 시험", "토익", "토플", "JLPT", 
        "HSK", "컴퓨터 자격증", "운전면허", "요리학원", "댄스 학원", "음악 학원", 
        "미술 학원", "스포츠 강습", "코딩 강의", "디자인 강의",
        "온라인 강의 플랫폼", "인프런", "클래스101", "스킬쉐어", "유데미",
        "어학원 추천", "영어학원", "일본어학원", "중국어학원", "스페인어학원",
        "자격증 종류", "컴퓨터활용능력", "워드프로세서", "한글", "엑셀", "파워포인트",
        "공무원 시험 정보", "행정고시", "사법고시", "외무고시", "경찰공무원",
        "토익 공부법", "토익 점수", "토익 문제", "토익 강의", "토익 교재",
        "토플 공부법", "토플 점수", "토플 문제", "토플 강의", "토플 교재",
        "JLPT 공부법", "JLPT 레벨", "일본어 문법", "일본어 회화", "일본어 교재",
        "HSK 공부법", "HSK 레벨", "중국어 문법", "중국어 회화", "중국어 교재",
        "컴퓨터 자격증 종류", "사무자동화산업기사", "정보처리기사", "컴퓨터활용능력",
        "운전면허 학원", "운전면허 시험", "운전면허 필기", "운전면허 실기",
        "요리학원 추천", "한식 요리학원", "양식 요리학원", "중식 요리학원", "일식 요리학원",
        "댄스 학원 추천", "힙합 댄스", "재즈 댄스", "발레", "현대무용",
        "음악 학원 추천", "피아노 학원", "기타 학원", "드럼 학원", "바이올린 학원",
        "미술 학원 추천", "수채화", "유화", "드로잉", "캘리그래피",
        "스포츠 강습", "수영 강습", "테니스 강습", "골프 강습", "스키 강습",
        "코딩 강의 추천", "파이썬", "자바", "자바스크립트", "HTML", "CSS",
        "디자인 강의 추천", "포토샵", "일러스트레이터", "피그마", "스케치"
    ],
    "beauty": [
        "화장품", "스킨케어", "헤어케어", "네일아트", "미용실", "에스테틱", 
        "다이어트", "성형", "치과", "피부과", "탈모 치료", "레이저", "보톡스", 
        "필러", "리프팅", "마사지", "마스크팩", "선케어", "메이크업",
        "화장품 브랜드", "이니스프리", "에뛰드하우스", "미샤", "네이처리퍼블릭",
        "스킨케어 루틴", "클렌징", "토너", "에센스", "크림", "선크림",
        "헤어케어 제품", "샴푸", "린스", "트리트먼트", "헤어에센스", "헤어스프레이",
        "네일아트 디자인", "젤네일", "아크릴네일", "네일아트 도안", "네일샵",
        "미용실 추천", "헤어스타일", "커트", "펌", "염색", "업스타일",
        "에스테틱 시술", "피부 관리", "마사지", "팩", "필링", "보습",
        "다이어트 방법", "운동 다이어트", "식단 다이어트", "다이어트 약", "다이어트 보조제",
        "성형 수술", "눈 성형", "코 성형", "턱 성형", "지방흡입", "보톡스",
        "치과 추천", "치아 교정", "임플란트", "틀니", "치아 미백", "충치 치료",
        "피부과 추천", "여드름 치료", "흉터 치료", "모공 축소", "피부 재생",
        "탈모 치료", "탈모 원인", "탈모 예방", "탈모 치료제", "탈모 샴푸",
        "레이저 시술", "레이저 제모", "레이저 피부", "레이저 흉터", "레이저 문신",
        "보톡스 시술", "보톡스 효과", "보톡스 부작용", "보톡스 가격", "보톡스 주사",
        "필러 시술", "필러 종류", "필러 효과", "필러 부작용", "필러 가격",
        "리프팅 시술", "리프팅 효과", "리프팅 부작용", "리프팅 가격", "리프팅 종류",
        "마사지 종류", "스웨디시 마사지", "타이 마사지", "아로마 마사지", "지압 마사지",
        "마스크팩 추천", "보습 마스크팩", "미백 마스크팩", "진정 마스크팩", "클렌징 마스크팩",
        "선케어 제품", "선크림", "선블록", "선스프레이", "선스틱", "선쿠션",
        "메이크업 방법", "베이스 메이크업", "아이 메이크업", "립 메이크업", "치크 메이크업"
    ]
}

# 전역 변수로 사용된 키워드 기록
used_keywords = set()

def generateHmac(method, full_url_path, secretKey, accessKey):
    from time import gmtime, strftime
    signed_date = strftime('%y%m%dT%H%M%SZ', gmtime())
    path, query = full_url_path.split('?', 1) if '?' in full_url_path else (full_url_path, "")
    message = signed_date + method + path + query
    signature = hmac.new(secretKey.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={accessKey}, signed-date={signed_date}, signature={signature}"

def get_random_best_product():
    for _ in range(5):
        category_id = random.choice(list(COUPANG_CATEGORY_SLUG_MAP.keys()))
        path = f"/v2/providers/affiliate_open_api/apis/openapi/products/bestcategories/{category_id}?limit=30"
        url = f"https://api-gateway.coupang.com{path}"
        auth_header = generateHmac("GET", path, CP_SECRET_KEY, CP_ACCESS_KEY)
        r = requests.get(url, headers={"Authorization": auth_header})
        if r.status_code == 200 and r.json().get("data"):
            p = random.choice(r.json()["data"])
            return {
                "name": p["productName"],
                "image": p["productImage"],
                "url": p["productUrl"]
            }
    return None

def get_news_title_from_url(news_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(news_url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("meta", property="og:title")
        if title_tag:
            return title_tag["content"].strip()
        return soup.title.string.strip() if soup.title else None
    except Exception as e:
        print(f"⚠️ 뉴스 제목 추출 실패: {e}")
        return None


def extract_og_image(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        og_tag = soup.find("meta", property="og:image")
        if og_tag and og_tag.get("content"):
            return og_tag["content"]
    except Exception as e:
        print("⚠️ og:image 추출 실패:", e)
    return None

def map_keyword_to_category(keyword):
    keyword = keyword.lower()
    if any(k in keyword for k in ["ai", "chatgpt", "gpt", "suno"]):
        return "ai-tech"
    elif any(k in keyword for k in ["다이어트", "생활", "정리", "절약"]):
        return "life-hacks"
    elif any(k in keyword for k in ["유튜브", "youtube", "영상", "쇼츠"]):
        return "today-video"
    elif any(k in keyword for k in ["뉴스", "속보", "헤드라인"]):
        return "briefing"
    elif any(k in keyword for k in ["결산", "요약", "통계", "톱10"]):
        return "archive"
    else:
        return "today-trend"

def get_trending_with_news(count=3):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://trends.google.co.kr/trends/trendingsearches/daily?geo=KR")
    time.sleep(3)

    elements = driver.find_elements(By.XPATH, '//tr[@role="row"]/td[2]/div[1]')
    keywords = [el.text.strip() for el in elements if el.text.strip()]
    driver.quit()

    selected = keywords[:count]
    results = []

    for keyword in selected:
        print(f"🔍 키워드: {keyword}")
        news_url, image_url, news_title = get_news_url_and_og_image(keyword)
        category = map_keyword_to_category(keyword)

        if not news_url:
            continue

        news_titles = [news_title] if news_title else [keyword]
        results.append((keyword, news_titles, category, image_url))

    return results

def get_news_url_and_og_image(keyword):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        query = quote(keyword)
        url = f"https://search.naver.com/search.naver?query={query}"
        driver.get(url)

        wait = WebDriverWait(driver, 5)
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='n.news.naver.com']")
        news_url = None
        for link in links:
            href = link.get_attribute("href")
            if href:
                news_url = href
                break

        if not news_url:
            print(f"❌ [{keyword}] 뉴스 링크 없음")
            return None, None, None

        image_url = extract_og_image(news_url)
        news_title = get_news_title_from_url(news_url)
        return news_url, image_url, news_title

    except Exception as e:
        print(f"⚠️ [{keyword}] 뉴스 URL/이미지 추출 실패: {e}")
        return None, None, None
    finally:
        driver.quit()


# 블로그 글 생성

def generate_meta_description(title):
    current_year = datetime.now().year
    return f"{title}에 대한 {current_year}년 최신 정보와 전문가 분석을 확인하세요. 상세한 비교 분석, 구매 가이드, 추천 순위까지 한 번에 알아보세요."

def generate_blog_content(keyword, news_titles, category):
    current_year = datetime.now().year
    joined_titles = "\n".join([f"- {t}" for t in news_titles])
    prompt = f"""
📰 '{keyword}'에 대한 상세하고 포괄적인 구매/이용 가이드를 작성해주세요.
뉴스 제목: {joined_titles}
카테고리: {category}

독자가 실제로 행동할 수 있는 구체적이고 상세한 정보를 제공해야 합니다.

⚠️ **중요한 규칙**:
- 글은 최소 800단어 이상으로 작성해주세요.
- 글은 항상 최대한 최신정보 기준으로 해주세요 

⚠️ **중요한 키워드 사용 규칙**:
- 핵심 키워드 "{keyword}"는 전체 글에서 정확히 6회만 사용하세요
- 키워드 밀도는 1~2% 이하로 유지하세요
- 같은 문단이나 문장에 키워드가 반복되지 않도록 하세요
- 키워드 대신 동의어나 유사어를 적극 활용하세요
"""
    messages = [
        {
            "role": "system",
            "content": (
                "당신은 상세하고 포괄적인 구매/이용 가이드 전문가입니다. 다음 지침을 엄격히 준수하여 한국어로 블로그 글을 작성해주세요.\n"
                "1. **분량**: 최소 800단어 이상, 1200-1500단어 권장으로 매우 상세하고 포괄적인 내용을 다룹니다.\n"
                "2. **구체성**: 추상적인 설명 대신 구체적인 수치, 가격, 방법을 제시합니다.\n"
                "3. **실제 정보**: 가상의 XX, YY 대신 실제 브랜드명, 제품명, 서비스명을 사용합니다.\n"
                "4. **구체적 혜택**: 실제 혜택과 조건을 정확히 제시합니다 (예: '연회비 3만원', '할인율 20%', '무료 배송').\n"
                f"5. **최신 정보**: {current_year}년 기준으로 최신 제품, 서비스, 가격 정보를 사용합니다. 2021년, 2022년 등 오래된 정보는 사용하지 않습니다.\n"
                f"   - 스마트폰: iPhone 16 Pro Max, Galaxy S25 Ultra, Pixel 9 Pro 등 {current_year}년 최신 모델 사용\n"
                f"   - 노트북: MacBook Pro M4, Galaxy Book5 Ultra, Dell XPS 16 등 {current_year}년 최신 모델 사용\n"
                f"   - 신용카드: {current_year}년 최신 혜택과 조건 사용\n"
                f"   - 보험: {current_year}년 최신 상품과 보장 내용 사용\n"
                "6. **키워드 중심 소제목**: 키워드와 직접적으로 관련된 구체적인 소제목을 사용합니다. 예시:\n"
                f"   - 키워드가 '노트북 추천'인 경우: '{current_year}년 최고의 노트북 추천 TOP 7', '용도별 노트북 추천 가이드', '가격대별 노트북 추천', '노트북 구매 시 체크포인트', '실제 사용자 후기', '자주 묻는 질문', '마무리' 등\n"
                f"   - 키워드가 '신용카드 추천'인 경우: '{current_year}년 최고의 신용카드 추천 TOP 5', '연봉별 신용카드 추천', '혜택별 신용카드 추천', '신용카드 신청 시 주의사항', '실제 혜택 비교', '자주 묻는 질문', '마무리' 등\n"
                f"   - 키워드가 '보험 추천'인 경우: '{current_year}년 최고의 보험 추천 TOP 6', '나이별 보험 추천', '상품별 보험 추천', '보험 가입 시 체크리스트', '실제 보장 비교', '자주 묻는 질문', '마무리' 등\n"
                "7. **상세한 구조**: 키워드와 직접적으로 관련된 자연스러운 소제목들로 구성합니다. 예시:\n"
                f"   - 키워드가 '노트북 추천'인 경우: '{current_year}년 최고의 노트북 추천 TOP 7', '용도별 노트북 추천 가이드', '가격대별 노트북 추천', '노트북 구매 시 체크포인트', '실제 사용자 후기', '자주 묻는 질문', '마무리' 등\n"
                f"   - 키워드가 '신용카드 추천'인 경우: '{current_year}년 최고의 신용카드 추천 TOP 5', '연봉별 신용카드 추천', '혜택별 신용카드 추천', '신용카드 신청 시 주의사항', '실제 혜택 비교', '자주 묻는 질문', '마무리' 등\n"
                f"   - 키워드가 '보험 추천'인 경우: '{current_year}년 최고의 보험 추천 TOP 6', '나이별 보험 추천', '상품별 보험 추천', '보험 가입 시 체크리스트', '실제 보장 비교', '자주 묻는 질문', '마무리' 등\n"
                "8. **실용성**: 독자가 바로 따라할 수 있는 구체적인 단계를 제공합니다.\n"
                "9. **신뢰성**: 실제 검증 가능한 정보와 구체적인 사례를 포함합니다.\n"
                "10. **비교 정보**: 최소 5-7개의 구체적인 옵션을 실제 정보로 비교 분석합니다.\n"
                "11. **가격 정보**: 가능한 한 구체적인 가격 범위를 제시합니다.\n"
                "12. **주의사항**: 실제 이용 시 주의해야 할 점들을 구체적으로 명시합니다.\n"
                "13. **FAQ 섹션**: 키워드와 관련된 자주 묻는 질문과 답변을 포함합니다.\n"
                "14. **행동 유도**: 글 마지막에 명확하고 구체적인 행동 단계를 제시합니다.\n"
                "15. **키워드 밀도**: 핵심 키워드를 자연스럽게 2-3회만 사용하되, 키워드 밀도는 1-2% 이하로 유지합니다. 키워드와 의미가 같은 동의어를 적극 활용하여 자연스러운 문장을 만듭니다.\n"
                "15-1. **키워드 배치**: 키워드는 제목, 첫 문단, 마무리 부분에만 자연스럽게 배치합니다. 중간 내용에서는 동의어나 관련 표현을 사용합니다.\n"
                "15-2. **동의어 활용**: 키워드 대신 의미가 같은 다른 표현들을 적극적으로 사용합니다. 예: '부동산' → '부동산 시장', '부동산 투자', '부동산 상품', '부동산 관련', '부동산 분야' 등\n"
                "16. **긴급성**: '지금', '바로', '서둘러' 등 긴급성을 강조하는 표현을 적절히 사용합니다.\n"
                "17. **HTML 태그**: <h2>, <h3>, <h4>, <p>, <ul>, <li>, <strong>, <em> 태그를 적절히 사용하여 구조화합니다.\n"
                "18. **이모지**: 각 섹션에 적절한 이모지를 사용하여 가독성을 높입니다.\n"
                "19. **실제 링크**: 가능한 경우 실제 신청 링크나 공식 홈페이지 정보를 포함합니다.\n"
                "20. **상세한 설명**: 각 섹션에서 충분히 상세한 설명을 제공합니다.\n"
                "21. **키워드 연관성**: 모든 소제목과 내용이 키워드와 직접적으로 관련되도록 작성합니다.\n"
                "22. **SEO 최적화**: 제목 태그(H1)는 한 번만 사용하고, 키워드가 포함되도록 합니다.\n"
                "23. **내부 링크**: 관련 키워드나 개념에 대한 내부 링크를 반드시 포함합니다. 예시: <a href='/finance/신용카드-추천' target='_blank'>신용카드 추천</a>, <a href='/finance/보험-추천' target='_blank'>보험 추천</a> 등\n"
                "24. **외부 링크**: 신뢰할 수 있는 외부 소스에 대한 링크를 포함합니다.\n"
                "25. **이미지 최적화**: 이미지에 적절한 alt 태그를 포함합니다.\n"
                "26. **마무리 링크**: 글 마지막에 언급된 제품이나 서비스의 실제 링크를 HTML <a> 태그로 포함합니다. 예시: <a href='https://www.apple.com/kr/' target='_blank'>아이폰 16 Pro Max</a>\n"
                "27. **국내 데이터 우선**: 반드시 한국에서 실제로 이용 가능한 서비스, 강의, 브랜드, 상품만 소개합니다. 해외 서비스, 해외 브랜드, 해외 강의는 절대 포함하지 않습니다. 국내 플랫폼(예: 클래스101, 만개의레시피, 에피큐리언, 쿠킹박스, 해먹남녀, 백종원의 요리비책 등) 위주로 추천하세요.\n"
                "28. **키워드 반복 강력 제한**: 포커스 키워드는 본문 전체에서 2~3회만 자연스럽게 사용하고, 그 외에는 반드시 동의어나 유사어로 대체하세요. 같은 문단이나 문장에 키워드가 반복되지 않도록 하세요. 키워드가 4회 이상 등장하면 반드시 동의어로 바꿔서 작성하세요. 키워드 밀도는 1~2% 이하로 유지하세요.\n"
            )
        },
        {"role": "user", "content": prompt}
    ]

    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=4000
    )
    return res['choices'][0]['message']['content']



def extract_tags_from_text(keyword, news_titles):
    base = " ".join(news_titles) + " " + keyword
    words = re.findall(r'[가-힣a-zA-Z]{2,20}', base)
    return list(set(words))[:5]


def get_or_create_category(slug):
    name = CATEGORY_MAP.get(slug, slug.replace('-', ' ').title())
    url = f"{WP_URL.replace('/posts', '/categories')}"
    r = requests.get(f"{url}?slug={slug}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    if r.status_code == 200 and r.json():
        return r.json()[0]['id']
    
    res = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps({"name": name, "slug": slug}),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )
    if res.status_code == 201:
        return res.json().get('id')
    print(f"⚠️ 카테고리 생성/조회 실패: {res.text}")
    return None


def get_or_create_tags(tag_names):
    tag_ids = []
    url = f"{WP_URL.replace('/posts', '/tags')}"
    for tag in tag_names:
        r = requests.get(f"{url}?search={tag}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
        if r.status_code == 200 and r.json():
            tag_ids.append(r.json()[0]['id'])
        else:
            res = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"name": tag}),
                auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
            )
            if res.status_code == 201:
                tag_ids.append(res.json().get("id"))
    return tag_ids


def reword_title(keyword):
    current_year = datetime.now().year
    patterns = [
        f"{current_year}년 {keyword} 완벽 가이드",
        f"{current_year}년 {keyword} TOP 5 추천",
        f"{keyword} {current_year}년 최신 정보",
        f"{keyword} 선택하는 7가지 방법",
        f"{keyword} 비교 분석 TOP 6",
        f"{keyword} 알아보기 - {current_year}년 전문가 조언",
        f"{keyword} 구매 전 10가지 체크리스트",
        f"{keyword} {current_year}년 최신 추천 순위",
        f"{keyword} 완전 분석 - 5가지 선택 기준",
        f"{keyword} 가이드 - {current_year}년 실전 활용법",
        f"{keyword} 비교 및 구매 가이드 TOP 8",
        f"{keyword} 추천 - {current_year}년 전문가 선택법",
        f"{current_year}년 {keyword} 완전 정복 가이드",
        f"{keyword} {current_year}년 최고의 선택 TOP 7"
    ]
    return random.choice(patterns)


def upload_image_to_wp(image_url, keyword=None):
    try:
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        img_data = resp.content
    except Exception as e:
        print("❌ 이미지 다운로드 실패:", e)
        return None

    parsed_url = urlparse(image_url)
    filename = unquote(parsed_url.path.split("/")[-1])
    ext = filename.split(".")[-1].lower().split("?")[0]
    content_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")

    # SEO 최적화된 alt 태그 생성
    alt_text = f"{keyword} 관련 이미지" if keyword else "관련 이미지"

    media_headers = {
        "Content-Disposition": f"attachment; filename=image.{ext}",
        "Content-Type": content_type
    }

    try:
        media_response = requests.post(
            WP_URL.replace("/posts", "/media"),
            headers=media_headers,
            data=img_data,
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
        )
        media_response.raise_for_status()
        media_json = media_response.json()
        
        # 이미지에 alt 태그 추가
        if keyword:
            alt_update = requests.put(
                f"{WP_URL.replace('/posts', '/media')}/{media_json['id']}",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"alt_text": alt_text}),
                auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
            )
        
        print("✅ 이미지 업로드 성공:", media_json.get("source_url"))
        return media_json["id"]
    except Exception as e:
        print("❌ 이미지 업로드 실패:", e)
        return None

def generate_tags_with_gpt(keyword, news_titles):
    prompt = f"블로그 글의 핵심 키워드가 '{keyword}'이고 관련 뉴스는 '{' / '.join(news_titles)}'입니다. 이 글에 적합한 태그를 쉼표로 구분하여 10개 추천해주세요. (예: 태그1, 태그2, ...)"
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    tags_str = res['choices'][0]['message']['content']
    return [tag.strip() for tag in tags_str.split(",") if tag.strip()]


def post_to_wordpress(title, html, category_slug, image_url):
    cat_id = get_or_create_category(category_slug)
    if not cat_id:
        print("❌ 카테고리 ID를 얻지 못해 포스팅을 중단합니다.")
        return

    meta_desc = generate_meta_description(title)
    
    try:
        tag_names = generate_tags_with_gpt(title, [title])
    except Exception as e:
        print("⚠️ GPT 태그 생성 실패, 기본 방식으로 대체:", e)
        tag_names = re.findall(r'[가-힣a-zA-Z]{2,20}', title)[:5]

    tag_ids = get_or_create_tags(tag_names)
    media_id = None
    if image_url:
        media_id = upload_image_to_wp(image_url, title)
        if media_id:
            html = f'<img src="{image_url}" alt="{title}" style="max-width:100%; height:auto; border-radius:10px; margin-bottom: 20px;" />' + html

    # 속도 최적화 메타 태그 추가
    html = add_speed_optimization_meta(html, title)

    # 내부 링크 추가
    html = add_internal_links_to_content(html, title, category_slug)

    # 연관 쿠팡 상품 추가
    product = search_coupang_products(title)
    if product and product.get('url'):
        product_html = f"""
        <div style="text-align: center; margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <a href="{product['url']}" target="_blank" rel="noopener sponsored">
                <img src="{product['image']}" alt="{product['name']}" style="width: 200px; height: 200px; object-fit: cover; border-radius: 8px; margin-bottom: 15px;">
            </a>
            <h4 style="margin: 10px 0; font-size: 1.2em;">{product['name']}</h4>
            <a href="{product['url']}" target="_blank" rel="noopener sponsored" style="display: inline-block; background: #ff6b6b; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold;">
                바로가기
            </a>
        </div>
        """
        html += product_html

    # "더 많은 정보 보기" 버튼 추가
    html += """
    <div style="text-align: center; margin: 40px 0;">
        <a href="https://mgddang.com/" target="_blank" rel="noopener" style="display: inline-block; background-color: #1a73e8; color: white; padding: 14px 28px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
            더 많은 정보 보기
        </a>
    </div>
    """

    post = {
        "title": reword_title(title),
        "content": html,
        "status": "publish",
        "categories": [cat_id],
        "tags": tag_ids,
        "meta": { 
            "rank_math_focus_keyword": title, 
            "rank_math_description": meta_desc,
            "rank_math_title": reword_title(title),
            "rank_math_robots": "index,follow",
            "rank_math_facebook_title": reword_title(title),
            "rank_math_facebook_description": meta_desc,
            "rank_math_twitter_title": reword_title(title),
            "rank_math_twitter_description": meta_desc,
            "rank_math_twitter_card_type": "summary_large_image",
            "rank_math_schema_type": "Article",
            "rank_math_schema_article_type": "BlogPosting"
        },
        **({"featured_media": media_id} if media_id else {})
    }

    r = requests.post(
        WP_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(post),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )

    if r.status_code in [200, 201]:
        post_url = r.json().get('link')
        print("✅ 글 등록 완료:", post_url)
        
        # Rank Math SEO 점수 재계산
        time.sleep(2)
        trigger_seo_recalc(r.json().get('id'))
        
    else:
        print("❌ 등록 실패:", r.text)

def trigger_seo_recalc(post_id):
    try:
        refresh_res = requests.put(
            f"{WP_URL}/{post_id}",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"status": "publish"}),
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
        )
        if refresh_res.status_code == 200:
            print("✅ Rank Math SEO 점수 재계산 트리거 완료")
        else:
            print("⚠️ Rank Math 점수 트리거 실패:", refresh_res.status_code, refresh_res.text)
    except Exception as e:
        print("❌ Rank Math 트리거 중 오류:", e)

def search_coupang_products(keyword, limit=5):
    """키워드로 쿠팡 상품을 검색하고 랜덤으로 하나를 반환합니다."""
    
    # 쿠팡에서 상품을 찾기 어려운 키워드들 (랜덤 상품 추천)
    random_product_keywords = [
        "보험", "신용카드", "대출", "건강검진", "검진", "의료", "보험료", "카드", "대출상품", "금융상품"
    ]
    
    # 키워드가 랜덤 상품 추천 대상인지 확인
    should_use_random = any(random_keyword in keyword for random_keyword in random_product_keywords)
    
    if should_use_random:
        print(f"🔍 쿠팡 검색 키워드: '{keyword}' → 랜덤 상품 추천")
        # 인기 카테고리에서 랜덤 상품 선택
        popular_categories = [1001, 1002, 1010, 1011, 1013, 1014, 1015, 1016, 1017, 1018, 1019, 1020, 1021, 1024, 1025, 1026, 1029, 1030]
        category_id = random.choice(popular_categories)
        
        path = f"/v2/providers/affiliate_open_api/apis/openapi/products/bestcategories/{category_id}?limit=30"
        url = f"https://api-gateway.coupang.com{path}"
        auth_header = generateHmac("GET", path, CP_SECRET_KEY, CP_ACCESS_KEY)
        
        try:
            r = requests.get(url, headers={"Authorization": auth_header}, timeout=10)
            r.raise_for_status()
            data = r.json().get("data")
            if data:
                p = random.choice(data)
                return {
                    "name": p.get("productName"),
                    "image": p.get("productImage"),
                    "url": p.get("productUrl")
                }
        except requests.exceptions.RequestException as e:
            print(f"⚠️ 쿠팡 랜덤 상품 검색 실패: {e}")
        return None
    
    # 일반 상품 검색
    product_keywords = {
        "노트북": ["노트북", "랩탑", "컴퓨터"],
        "스마트폰": ["스마트폰", "휴대폰", "폰"],
        "다이어트": ["다이어트", "건강식품", "영양제"],
        "영양제": ["영양제", "건강식품", "비타민"],
        "게이밍": ["게이밍", "게임", "게이밍기기"],
        "인테리어": ["인테리어", "가구", "홈데코"],
        "이사": ["이사", "이사용품", "박스"],
        "결혼": ["결혼", "웨딩", "결혼용품"]
    }
    
    # 키워드에 맞는 상품 키워드 찾기
    search_keyword = keyword
    for key, products in product_keywords.items():
        if key in keyword:
            search_keyword = random.choice(products)
            break
    
    # 기본 상품 키워드 추가
    if search_keyword == keyword:
        if "노트북" in keyword or "컴퓨터" in keyword:
            search_keyword = "노트북"
        elif "스마트폰" in keyword or "폰" in keyword:
            search_keyword = "스마트폰"
        elif "다이어트" in keyword or "건강" in keyword:
            search_keyword = "건강식품"
        elif "게임" in keyword or "게이밍" in keyword:
            search_keyword = "게이밍"
        elif "인테리어" in keyword or "가구" in keyword:
            search_keyword = "가구"
        elif "이사" in keyword:
            search_keyword = "이사용품"
        elif "결혼" in keyword:
            search_keyword = "결혼용품"
    
    path = f"/v2/providers/affiliate_open_api/apis/openapi/products/search?keyword={quote(search_keyword)}&limit={limit}"
    url = f"https://api-gateway.coupang.com{path}"
    auth_header = generateHmac("GET", path, CP_SECRET_KEY, CP_ACCESS_KEY)
    
    print(f"🔍 쿠팡 검색 키워드: '{keyword}' → '{search_keyword}'")
    
    try:
        r = requests.get(url, headers={"Authorization": auth_header}, timeout=10)
        r.raise_for_status()
        data = r.json().get("data")
        if data and data.get("productData"):
            products = data["productData"]
            if products:
                p = random.choice(products)
                return {
                    "name": p.get("productName"),
                    "image": p.get("productImage"),
                    "url": p.get("productUrl")
                }
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 쿠팡 상품 검색 실패: {e}")
    
    return None

def generate_high_cpc_keywords(category=None, count=5):
    """OpenAI를 사용하여 고단가 CPC 키워드를 동적으로 생성합니다."""
    if category:
        prompt = f"""
다음 카테고리에서 CPC(클릭당 비용)가 높은 키워드 {count}개를 추천해주세요.
카테고리: {category}

조건:
- 검색량이 많으면서도 상업적 의도가 강한 키워드
- "구매", "예약", "방법", "추천", "비교", "가격", "후기", "순위" 등 행동 유도 단어 포함
- 실제 구매나 서비스 이용으로 이어지는 키워드
- 한국어로 작성
- 쉼표로 구분하여 키워드만 나열 (줄바꿈 없이)

예시: 키워드1, 키워드2, 키워드3, 키워드4, 키워드5
"""
    else:
        prompt = f"""
CPC(클릭당 비용)가 높은 키워드 {count}개를 추천해주세요.

조건:
- 금융, 보험, 건강, 기술, 라이프스타일 분야에서 각각 다른 분야의 키워드를 선택
- "구매", "예약", "방법", "추천", "비교", "가격", "후기", "순위" 등 행동 유도 단어 포함
- 실제 구매나 서비스 이용으로 이어지는 키워드
- 한국어로 작성
- 쉼표로 구분하여 키워드만 나열 (줄바꿈 없이)
- 같은 분야의 키워드가 중복되지 않도록 다양한 분야에서 선택

예시: 노트북 구매 가이드, 신용카드 추천, 다이어트 약 구매, 이사 업체 추천, 게이밍 마우스 비교
"""

    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        keywords_str = res['choices'][0]['message']['content'].strip()
        # 줄바꿈 제거하고 쉼표로 분리
        keywords_str = keywords_str.replace('\n', '').replace('-', '')
        keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        return keywords[:count]
    except Exception as e:
        print(f"⚠️ AI 키워드 생성 실패: {e}")
        # 실패 시 기본 키워드 반환
        fallback_keywords = {
            "finance": ["대출 비교", "신용카드 추천", "보험 가입 방법"],
            "health": ["다이어트 약 구매", "영양제 추천", "건강검진 예약"],
            "tech": ["노트북 구매 가이드", "스마트폰 비교", "게이밍 마우스 추천"],
            "life": ["이사 업체 추천", "인테리어 견적", "결혼준비 체크리스트"]
        }
        return fallback_keywords.get(category, ["구매 가이드", "추천 순위", "비교 방법"])[:count]

def get_dynamic_high_cpc_keyword():
    """동적으로 고단가 키워드를 생성하고 선택합니다."""
    global used_keywords
    
    # 카테고리 선택 (기존 + AI 생성)
    categories = list(HIGH_CPC_KEYWORDS.keys()) + ["ai_generated"]
    category = random.choice(categories)
    
    if category == "ai_generated":
        # AI가 카테고리와 키워드를 모두 생성
        keywords = generate_high_cpc_keywords(count=5)
        if keywords:
            # 사용되지 않은 키워드 중에서 선택
            unused_keywords = [kw for kw in keywords if kw not in used_keywords]
            if unused_keywords:
                selected_keyword = random.choice(unused_keywords)
            else:
                # 모든 키워드가 사용되었다면 첫 번째 선택
                selected_keyword = keywords[0]
            
            used_keywords.add(selected_keyword)
            print(f"🎯 AI 생성 키워드 목록: {keywords}")
            print(f"✅ 선택된 키워드: {selected_keyword}")
            return selected_keyword, "ai_generated"
        else:
            # AI 생성 실패 시 기본 카테고리로 폴백
            category = random.choice(list(HIGH_CPC_KEYWORDS.keys()))
            base_keywords = HIGH_CPC_KEYWORDS[category]
            unused_keywords = [kw for kw in base_keywords if kw not in used_keywords]
            if unused_keywords:
                selected_keyword = random.choice(unused_keywords)
            else:
                selected_keyword = random.choice(base_keywords)
            used_keywords.add(selected_keyword)
            return selected_keyword, category
    else:
        # 기존 카테고리에서 선택하되, 다른 카테고리의 AI 키워드 생성
        base_keywords = HIGH_CPC_KEYWORDS[category]
        
        # 다른 카테고리에서 AI 키워드 생성 (중복 방지)
        other_categories = [cat for cat in HIGH_CPC_KEYWORDS.keys() if cat != category]
        if other_categories:
            other_category = random.choice(other_categories)
            ai_keywords = generate_high_cpc_keywords(other_category, count=3)
        else:
            ai_keywords = generate_high_cpc_keywords(count=3)
        
        # 기존 키워드와 AI 키워드를 합쳐서 선택
        all_keywords = base_keywords + ai_keywords
        
        # 중복 제거 (같은 키워드가 여러 번 있으면 하나만 유지)
        unique_keywords = list(dict.fromkeys(all_keywords))
        
        # 사용되지 않은 키워드 중에서 선택
        unused_keywords = [kw for kw in unique_keywords if kw not in used_keywords]
        if unused_keywords:
            selected_keyword = random.choice(unused_keywords)
        else:
            # 모든 키워드가 사용되었다면 랜덤 선택
            selected_keyword = random.choice(unique_keywords)
        
        used_keywords.add(selected_keyword)
        print(f"🎯 선택 가능한 키워드: {unique_keywords}")
        print(f"✅ 최종 선택: {selected_keyword}")
        return selected_keyword, category

def translate_to_english(keyword):
    """한국어 키워드를 영어로 번역합니다."""
    try:
        prompt = f"다음 한국어 키워드를 영어로 번역해주세요. 이미지 검색에 적합한 영어 단어나 구문으로 번역해주세요: {keyword}"
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )
        english_keyword = res['choices'][0]['message']['content'].strip()
        print(f"🌐 번역: '{keyword}' → '{english_keyword}'")
        return english_keyword
    except Exception as e:
        print(f"⚠️ 번역 실패: {e}")
        return keyword

def get_pexels_image_url(keyword):
    """Pexels API를 사용해 키워드에 맞는 이미지를 검색하여 대표 이미지 URL을 반환합니다."""
    # 한국어 키워드를 영어로 번역
    english_keyword = translate_to_english(keyword)
    
    url = f'https://api.pexels.com/v1/search?query={quote(english_keyword)}&per_page=10&page=1'
    headers = {"Authorization": PEXELS_API_KEY}
    
    print(f"🔍 Pexels 검색 URL: {url}")
    print(f"🔑 API 키: {PEXELS_API_KEY[:10]}...")
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"📡 Pexels API 응답 상태: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ Pexels API 오류: {resp.text}")
            return None
            
        data = resp.json()
        photos = data.get('photos', [])
        print(f"📸 찾은 이미지 개수: {len(photos)}")
        
        if photos:
            # 랜덤으로 한 장 선택
            photo = random.choice(photos)
            image_url = photo['src']['large']
            print(f"✅ 선택된 이미지: {image_url}")
            return image_url
        else:
            print("⚠️ 검색 결과가 없습니다.")
            
    except Exception as e:
        print(f"⚠️ Pexels 이미지 검색 실패: {e}")
    return None

def run_high_cpc_strategy():
    print("\n🚀 [시작] 고단가 키워드 기반 자동 포스팅\n")
    
    # 동적으로 고단가 키워드 생성
    keyword, category_key = get_dynamic_high_cpc_keyword()
    print(f"🎯 선택된 키워드: {keyword} (카테고리: {category_key})")

    news_url, _, news_title = get_news_url_and_og_image(keyword)
    if not news_url:
        print(f"⚠️ '{keyword}' 뉴스를 찾지 못해도 포스팅을 진행합니다.")
        news_title = None
    
    # Pexels에서 대표 이미지 가져오기
    image_url = get_pexels_image_url(keyword)
    if not image_url:
        print(f"⚠️ Pexels에서 이미지를 찾지 못했습니다. 이미지 없이 진행합니다.")
    
    category_name = CATEGORY_MAP.get(category_key, "정보")
    html = generate_blog_content(keyword, [news_title] if news_title else [keyword], category_name)
    post_to_wordpress(keyword, html, category_key, image_url)
    print(f"✅ 포스팅 완료: {keyword}")

def add_speed_optimization_meta(html, title):
    """페이지 로딩 속도 최적화를 위한 메타 태그를 추가합니다."""
    speed_meta = f"""
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
    <meta name="googlebot" content="index, follow">
    <meta name="bingbot" content="index, follow">
    <link rel="canonical" href="{WP_URL.replace('/wp-json/wp/v2/posts', '')}/finance/{title.lower().replace(' ', '-')}/">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:url" content="{WP_URL.replace('/wp-json/wp/v2/posts', '')}/finance/{title.lower().replace(' ', '-')}/">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    """
    
    # HTML 시작 부분에 메타 태그 삽입
    if '<head>' in html:
        html = html.replace('<head>', f'<head>{speed_meta}')
    else:
        html = speed_meta + html
    
    return html

def get_existing_posts_for_internal_links(category_slug=None, limit=5):
    """내부 링크용 기존 포스트 목록을 가져옵니다."""
    try:
        url = f"{WP_URL}?per_page={limit}&status=publish"
        if category_slug:
            # 카테고리별 포스트 가져오기
            cat_id = get_or_create_category(category_slug)
            if cat_id:
                url += f"&categories={cat_id}"
        
        r = requests.get(url, auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
        if r.status_code == 200:
            posts = r.json()
            internal_links = []
            for post in posts:
                title = post.get('title', {}).get('rendered', '')
                link = post.get('link', '')
                if title and link:
                    internal_links.append({
                        'title': title,
                        'url': link
                    })
            return internal_links
    except Exception as e:
        print(f"⚠️ 내부 링크용 포스트 가져오기 실패: {e}")
    return []

def add_internal_links_to_content(html, keyword, category_slug):
    """콘텐츠에 내부 링크를 추가합니다."""
    try:
        # 관련 포스트 가져오기
        related_posts = get_existing_posts_for_internal_links(category_slug, limit=3)
        
        if related_posts:
            internal_links_html = """
            <div style="background: #f8f9fa; border-left: 4px solid #007cba; padding: 20px; margin: 30px 0; border-radius: 5px;">
                <h3 style="margin-top: 0; color: #333;">📚 관련 글 더보기</h3>
                <ul style="list-style: none; padding: 0;">
            """
            
            for post in related_posts:
                internal_links_html += f"""
                    <li style="margin-bottom: 10px;">
                        <a href="{post['url']}" target="_blank" style="color: #007cba; text-decoration: none; font-weight: 500;">
                            🔗 {post['title']}
                        </a>
                    </li>
                """
            
            internal_links_html += """
                </ul>
            </div>
            """
            
            # 콘텐츠 중간에 내부 링크 삽입
            if '</h2>' in html:
                # 첫 번째 h2 태그 다음에 삽입
                html = html.replace('</h2>', '</h2>' + internal_links_html, 1)
            else:
                # 콘텐츠 끝에 추가
                html += internal_links_html
                
    except Exception as e:
        print(f"⚠️ 내부 링크 추가 실패: {e}")
    
    return html

if __name__ == "__main__":
    # --- 전략 선택 ---
    # 'trend': 구글 트렌드 키워드 기반 포스팅
    # 'high_cpc': 지정된 고단가 키워드 기반 포스팅
    STRATEGY = "high_cpc"
    # -----------------

    if STRATEGY == "trend":
        run_trend_strategy(count=1)
    elif STRATEGY == "high_cpc":
        run_high_cpc_strategy()
    else:
        print(f"❌ 알 수 없는 전략: {STRATEGY}")
    
    print("\n🎉 모든 작업 완료!")
