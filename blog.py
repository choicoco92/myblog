# ✅ 통합된 자동 포스팅 스크립트: 트렌드 뉴스 + 쿠팡 상품 삽입 (og:image 적용 포함 전체코드)


import requests, json, openai, hashlib, hmac, re, time, feedparser, random
from requests.auth import HTTPBasicAuth
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
from config import *

openai.api_key = OPENAI_API_KEY

CATEGORY_MAP = {
    "today-trend": "🌍 오늘의 트렌드",
    "ai-tech": "🤖 AI & 기술",
    "life-hacks": "🧠 생활정보",
    "today-video": "🎬 오늘의 영상",
    "briefing": "✍️ 짧은 브리핑",
    "archive": "📚 아카이브"
}

COUPANG_CATEGORY_SLUG_MAP = {
    1001: "hot-now", 1002: "hot-now", 1010: "hot-now", 1011: "kids-life",
    1013: "home-living", 1014: "daily-pick", 1015: "home-living", 1016: "tech-gadgets",
    1017: "travel-leisure", 1018: "daily-pick", 1019: "daily-pick", 1020: "daily-pick",
    1021: "daily-pick", 1024: "daily-pick", 1025: "travel-leisure", 1026: "travel-leisure",
    1029: "pet-picks", 1030: "kids-life"
}

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

def generate_blog_content(keyword, news_titles, category):
    joined_titles = "\n".join([f"- {t}" for t in news_titles])
    prompt = f"""
📰 '{keyword}'와 관련된 최근 뉴스 제목은 다음과 같습니다:
{joined_titles}

이 정보를 기반으로 SEO에 최적화된 블로그 글을 작성해주세요.

"""
    messages = [
        {
            "role": "system",
            "content": (
                "너는 SEO 최적화 블로그 글을 잘 쓰는 작가입니다. 요청 조건을 반드시 지켜야 합니다. 반드시 한국어로 작성하세요. "
                "아래 조건을 반드시 준수하세요: "
                "1) 800단어 이상, 4000자 이상 작성, "
                "2) <h2>, <h3>, <h4> 등 부제목에는 포커스 키워드를 넣지 않는다 또한 적절한 이모지를 자연스럽게 활용, "
                "3) <h2>, <p> 태그 포함, "
                f"4) 포커스 키워드 '{keyword}'는 최대 2회 이하만 자연스럽게 사용 (키워드 밀도 1% 이하), 매우중요"
                "5) 분석형 본문 중심, 인물 및 배경 포함, "
                "6) 글은 도입부 / 주요 이슈 요약 / 배경 설명 / 전망 / 결론 구조로 작성."
            )
        },
        {"role": "user", "content": prompt}
    ]

    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=3200
    )
    return res['choices'][0]['message']['content']


def extract_tags_from_text(keyword, news_titles):
    base = " ".join(news_titles) + " " + keyword
    words = re.findall(r'[가-힣a-zA-Z]{2,20}', base)
    return list(set(words))[:5]


def get_or_create_category(slug):
    r = requests.get(f"{WP_URL.replace('/posts', '/categories')}?slug={slug}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    if r.status_code == 200 and r.json():
        return r.json()[0]['id']
    name = CATEGORY_MAP.get(slug, slug)
    res = requests.post(
        f"{WP_URL.replace('/posts', '/categories')}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"name": name, "slug": slug}),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )
    return res.json().get('id')


def get_or_create_tags(tag_names):
    tag_ids = []
    for tag in tag_names:
        r = requests.get(f"{WP_URL.replace('/posts', '/tags')}?search={tag}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
        if r.status_code == 200 and r.json():
            tag_ids.append(r.json()[0]['id'])
        else:
            res = requests.post(
                f"{WP_URL.replace('/posts', '/tags')}",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"name": tag}),
                auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
            )
            res_json = res.json()
            tag_ids.append(res_json.get("id", res_json.get("data", {}).get("term_id")))
    return tag_ids


def reword_title(keyword):
    patterns = [
        f"{keyword} 요즘 왜 난리일까?",
        f"{keyword} 이슈, 알고 보면 충격적입니다",
        f"{keyword} 지금 안 보면 후회합니다 🔥",
        f"{keyword} 왜 갑자기 떴을까?",
        f"{keyword} 숨겨진 뒷이야기 공개!",
        f"{keyword} 진짜 이유는 따로 있다",
        f"{keyword} 뉴스 보다가 소름 돋은 이유"
    ]
    return random.choice(patterns)


def generate_meta_description(title):
    patterns = [
        f"{title} 에 대해 지금 가장 궁금한 핵심 내용을 1분 만에 요약해드립니다. 최신 트렌드, 이슈, 그리고 알아두면 돈 되는 정보까지 총정리!",
        f"{title} 관련 뉴스와 이슈들을 한눈에 보기 쉽게 정리했어요. 지금 알아두면 분명히 유용할 정보만 콕 집어서 전해드립니다!",
        f"{title} 이슈가 왜 떠오르고 있는지, 지금 무엇을 준비해야 하는지까지 알 수 있는 핵심 요약 가이드입니다. 절대 놓치지 마세요!",
        f"{title} 에 대해 지금 꼭 알아야 할 배경과 이슈를 쉽게 풀어 정리했습니다. 핵심 포인트를 3분 안에 확인하세요! 최근 많은 사람들이 관심을 갖고 있는중 " ,
        f"{title} 에 대한 최신 정보와 트렌드를 빠르게 요약한 콘텐츠입니다. 실생활에 도움이 되는 핵심 정보만 엄선해서 담았어요!"
    ]
    return random.choice(patterns)


def upload_image_to_wp(image_url):
    try:
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        img_data = resp.content
    except Exception as e:
        print("❌ 이미지 다운로드 실패:", e)
        return None

    # 🔧 쿼리 스트링 제거 + 안전한 확장자 추출
    parsed_url = urlparse(image_url)
    clean_path = parsed_url.path  # /image/abc.jpg
    filename = clean_path.split("/")[-1]
    filename = unquote(filename)
    ext = filename.split(".")[-1].lower().split("?")[0]

    content_type = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp"
    }.get(ext, "image/jpeg")

    media_headers = {
        "Content-Disposition": f"attachment; filename={filename}",
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
        print("✅ 이미지 업로드 성공:", media_json.get("source_url"))
        return media_json["id"]
    except Exception as e:
        print("❌ 이미지 업로드 실패:", e)
        return None

def generate_tags_with_gpt(keyword, news_titles):
    prompt = f"""
다음 키워드를 중심으로 블로그용 태그 후보를 10개 추천해주세요. 

중심 키워드: {keyword}
관련 뉴스 제목: {" / ".join(news_titles)}

조건:
- 각 태그는 1~4단어 사이
- 중복 없이 10개
- 관련 인물, 기업, 지역, 상황 포함 가능
- 쉼표로 구분된 단어 리스트만 출력

예시 출력: 키워드1, 키워드2, 키워드3 ...
"""
    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    tags_str = res['choices'][0]['message']['content']
    return [tag.strip() for tag in tags_str.split(",") if tag.strip()]

def post_to_wordpress(title, html, category_slug, image_url):
    cat_id = get_or_create_category(category_slug)
    meta_desc = generate_meta_description(title)
    slug = re.sub(r'\s+', '-', title.lower())
    try:
        tag_names = generate_tags_with_gpt(title, [title])
    except Exception as e:
        print("⚠️ GPT 태그 생성 실패, 기본 방식으로 대체:", e)
        tag_names = extract_tags_from_text(title, [title])

    tag_ids = get_or_create_tags(tag_names)

    media_id = None
    if image_url:
        media_id = upload_image_to_wp(image_url)
        html = f'<img src="{image_url}" alt="{title}" style="max-width:100%; border-radius:10px;" />\n<br> <br>' + html

    product = get_random_best_product()
    if product:
        html += f"""
    <h3>🛍️ 오늘의 추천 아이템</h3>
    <p><strong>이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</strong></p>
    <p><strong>{product['name']}</strong> 제품이에요!</p>
    <img src="{product['image']}" style="max-width:100%; border-radius:10px;">
    <br>
    <a href="{product['url']}" target="_blank" style="display:inline-block; margin-top:10px; background:#ff4800; color:white; padding:10px 20px; border-radius:5px;">🛒 상세 보기</a>
    """

    # ✅ 내부 링크 자동 삽입
    html += f'''
    <h3>📌 관련 콘텐츠 더 보기</h3>
    <ul>
      <li><a href="/category/{category_slug}">🌍 오늘의 뉴스 모아보기</a></li>
    </ul>
    '''

    post = {
        "title": reword_title(title),
        "slug": slug,
        "content": html,
        "status": "publish",
        "categories": [cat_id],
        "tags": tag_ids,
        "meta": {
            "rank_math_focus_keyword": title,
            "rank_math_title": title,
            "rank_math_description": meta_desc
        }
    }

    r = requests.post(
        WP_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(post),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )

    if r.status_code in [200, 201]:
        post_id = r.json().get("id")
        print("✅ 글 등록 완료:", r.json().get('link'))

        if media_id:
            patch_res = requests.put(
                f"{WP_URL}/{post_id}",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"featured_media": media_id}),
                auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
            )
            print("🖼 대표 이미지 저장 응답:", patch_res.status_code)

            refresh_res = requests.put(
                f"{WP_URL}/{post_id}",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"status": "publish"}),
                auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
            )
            print("🔄 재저장 완료:", refresh_res.status_code)

        trigger_seo_recalc(post_id)

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

if __name__ == "__main__":
    print("\n🚀 [시작] 트렌드 키워드 기반 자동 포스팅 실행\n")
    items = get_trending_with_news(count=1)  # 예: 키워드 5개 가져옴

    for idx, (keyword, news, category, image_url) in enumerate(items, 1):
        print(f"\n🌀 [{idx}] 키워드 처리 시작: {keyword}")

        if not news:
            print("⚠️ 뉴스 없음, 건너뜀")
            continue
        print(f"📝 GPT 본문 생성 중... ({keyword})")
        html = generate_blog_content(keyword, news, CATEGORY_MAP[category])
        print(f"📤 워드프레스 포스팅 시작... ({keyword})")
        post_to_wordpress(keyword, html, category, image_url)
        print(f"✅ [{idx}] 키워드 완료: {keyword} → 다음으로 이동\n")
        time.sleep(2)  # ← 여기서 1개 발행 끝나고 다음 키워드 진행
    print("\n🎉 전체 포스팅 완료!")
