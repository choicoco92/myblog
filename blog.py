# ✅ 통합된 자동 포스팅 스크립트: 트렌드 뉴스 + 쿠팡 상품 삽입 (og:image 적용 포함 전체코드)

import requests, json, openai, hashlib, hmac, re, time, feedparser, random
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
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
    url = "https://trends.google.com/trending/rss?geo=KR"
    headers = {"User-Agent": "Mozilla/5.0"}
    raw_feed = requests.get(url, headers=headers).text
    feed = feedparser.parse(raw_feed)

    all_entries = feed.entries
    seen = set()
    unique_entries = []
    for entry in all_entries:
        title = entry.title
        if title not in seen:
            seen.add(title)
            unique_entries.append(entry)

    random.shuffle(unique_entries)
    selected = unique_entries[:count]

    results = []
    for entry in selected:
        keyword = entry.title
        category = map_keyword_to_category(keyword)
        news_titles = []
        image_url = None
        news_url = None

        if 'ht_news_item_title' in entry:
            news_titles.append(entry.ht_news_item_title)
        elif 'ht_news_item' in entry:
            news_titles.append(entry.ht_news_item[0]['ht_news_item_title'])

        if 'ht_news_item_url' in entry:
            news_url = entry.ht_news_item_url
        elif 'ht_news_item' in entry and 'ht_news_item_url' in entry.ht_news_item[0]:
            news_url = entry.ht_news_item[0]['ht_news_item_url']

        if news_url:
            image_url = extract_og_image(news_url)
            print(f"🔗 뉴스 URL: {news_url}")
            print(f"🖼 추출된 og:image: {image_url}")

        results.append((keyword, news_titles, category, image_url))

    return results

# 블로그 글 생성

def generate_blog_content(keyword, news_titles, category):
    joined_titles = "\n".join([f"- {t}" for t in news_titles])
    prompt = f"""
📰 '{keyword}'와 관련된 최근 뉴스 제목은 다음과 같습니다:
{joined_titles}

이 내용을 바탕으로 SEO 최적화된 블로그 글을 작성해주세요.
- 카테고리: {category}
- 자연스러운 문체와 함께, 실제 트랜드리뷰처럼 보이도록 구성
- 3000자 이상, 800단어 이상
- 친근하고 정보성 있는 말투
- 키워드를 적절히 반복 사용
- 이모지를 적절히 활용하여 가독성 높이기
- HTML 태그 포함 (<h2>, <p> 등)
"""
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
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
        f"{title} 지금 핫한 이유, 요약해드립니다.",
        f"{title} 이슈, 핵심만 딱 정리했어요.",
        f"{title} 뉴스 요약, 1분 만에 정리!"
    ]
    return random.choice(patterns)


def upload_image_to_wp(image_url):
    img_data = requests.get(image_url).content
    filename = image_url.split("/")[-1]
    ext = filename.split('.')[-1].lower()
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
    media_response = requests.post(
        WP_URL.replace("/posts", "/media"),
        headers=media_headers,
        data=img_data,
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )
    if media_response.status_code in [200, 201]:
        media_json = media_response.json()
        print("✅ 이미지 업로드 성공:", media_json.get("source_url"))
        return media_json["id"]
    else:
        print("⚠️ 이미지 업로드 실패:", media_response.status_code, media_response.text)
        return None


def post_to_wordpress(title, html, category_slug, image_url):
    cat_id = get_or_create_category(category_slug)
    meta_desc = generate_meta_description(title)
    slug = re.sub(r'\s+', '-', title.lower())
    tag_ids = get_or_create_tags(extract_tags_from_text(title, [title]))

    media_id = None
    if image_url:
        media_id = upload_image_to_wp(image_url)
        html = f'<img src="{image_url}" alt="{title}" style="max-width:100%; border-radius:10px;" />\n<br>{title} <br>' + html

    product = get_random_best_product()
    if product:
        html += f"""
<h3>🛍️ 오늘의 추천 아이템</h3>
<p><strong>{product['name']}</strong> 제품이에요!</p>
<img src="{product['image']}" style="max-width:100%; border-radius:10px;">
<br>
<a href="{product['url']}" target="_blank" style="display:inline-block; margin-top:10px; background:#ff4800; color:white; padding:10px 20px; border-radius:5px;">🛒 상세 보기</a>
"""

    post = {
        "title": reword_title(title),
        "slug": slug,
        "content": html,
        "status": "publish",
        "categories": [cat_id],
        "tags": tag_ids,
        "meta": {
            "_yoast_wpseo_focuskw": title,
            "_yoast_wpseo_title": title,
            "_yoast_wpseo_metadesc": meta_desc
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

    else:
        print("❌ 등록 실패:", r.text)


if __name__ == "__main__":
    items = get_trending_with_news(count=1)
    for idx, (keyword, news, category, image_url) in enumerate(items, 1):
        print(f"\n🌀 [{idx}] {keyword} 처리 중...")
        if not news:
            print("⚠️ 뉴스 없음, 건너뜀")
            continue
        html = generate_blog_content(keyword, news, CATEGORY_MAP[category])
        post_to_wordpress(keyword, html, category, image_url)
        time.sleep(2)
    print("\n🎉 전체 포스팅 완료!")
