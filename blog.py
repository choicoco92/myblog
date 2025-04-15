# auto_post.py (Yoast 제거 버전)

import requests, random, json, openai, hashlib, hmac, re, time
from time import gmtime, strftime
from requests.auth import HTTPBasicAuth
from config import *

openai.api_key = OPENAI_API_KEY

# ✅ 쿠팡 카테고리 매핑
COUPANG_CATEGORY_SLUG_MAP = {
    1001: "hot-now", 1002: "hot-now", 1010: "hot-now", 1011: "kids-life",
    1013: "home-living", 1014: "daily-pick", 1015: "home-living", 1016: "tech-gadgets",
    1017: "travel-leisure", 1018: "daily-pick", 1019: "daily-pick", 1020: "daily-pick",
    1021: "daily-pick", 1024: "daily-pick", 1025: "travel-leisure", 1026: "travel-leisure",
    1029: "pet-picks", 1030: "kids-life"
}
EXCLUDE_CATEGORY = [1012]
VALID_CATEGORIES = [k for k in COUPANG_CATEGORY_SLUG_MAP if COUPANG_CATEGORY_SLUG_MAP[k] is not None and k not in EXCLUDE_CATEGORY]

def print_progress(percent, message):
    bar = '█' * int(percent/3.3) + '░' * (30 - int(percent/3.3))
    print(f"[{bar}] {percent}% - {message}")

def generateHmac(method, full_url_path, secretKey, accessKey):
    signed_date = strftime('%y%m%dT%H%M%SZ', gmtime())
    path, query = full_url_path.split('?', 1) if '?' in full_url_path else (full_url_path, "")
    message = signed_date + method + path + query
    signature = hmac.new(secretKey.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={accessKey}, signed-date={signed_date}, signature={signature}"

def get_random_best_product():
    for _ in range(5):
        category_id = random.choice(VALID_CATEGORIES)
        path = f"/v2/providers/affiliate_open_api/apis/openapi/products/bestcategories/{category_id}?limit=30"
        url = f"https://api-gateway.coupang.com{path}"
        auth_header = generateHmac("GET", path, CP_SECRET_KEY, CP_ACCESS_KEY)
        r = requests.get(url, headers={"Authorization": auth_header})
        if r.status_code == 200 and r.json().get("data"):
            p = random.choice(r.json()["data"])
            return {
                "name": p["productName"],
                "image": p["productImage"],
                "price": p["productPrice"],
                "url": p["productUrl"],
                "cat_id": category_id
            }
    raise Exception("🚨 쿠팡 상품 불러오기 실패")

def generate_review(product_name, product_info=""):
    prompt = f"""
'{product_name}'에 대해 실제 사용자 후기와 상품 정보를 바탕으로, 다음 HTML 형식으로 정보성 블로그 글을 작성해주세요:
조건:
- 직접 사용한 내용은 포함하지 말고, 사용자들의 리뷰와 온라인 정보 기반으로 작성
- 자연스러운 문체와 함께, 실사용 리뷰처럼 보이도록 구성
- 3000자 이상, 800단어 이상

<h2>제목 (제품의 특징을 살짝 강조한 한 문장)</h2>
<p>제품을 소개하는 자연스러운 시작 문단</p>

<h2>🔍 주요 특징</h2>
<ul><li>제품 스펙, 기능 요약</li></ul>
<p>실제 활용성 중심으로 설명</p>

<h2>💬 사용자 후기 요약</h2>
<ul><li>실제 사용자들이 자주 언급한 리뷰 요약</li></ul>

<h2>👍 장점 & 👎 단점</h2>
<p><strong>장점:</strong></p>
<ul><li>실제 장점</li></ul>
<p><strong>단점:</strong></p>
<ul><li>실제 단점</li></ul>

<h2>⚠️ 구매 전 체크포인트</h2>
<p>주의사항이나 부가사항</p>

<h2>🎯 이런 분께 추천해요</h2>
<ul><li>추천 대상</li></ul>

<h2>📝 총평</h2>
<p>전체 요약과 감성 마무리 멘트</p>

<hr>

<h3>🔗 제품 정보 바로가기</h3>
<p><a href="{product_info}" target="_blank" rel="noopener noreferrer" style="color:#2b7ec7; font-weight:bold;">
👉 쿠팡 상세 페이지에서 더 많은 정보 보기
</a></p>
"""
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "당신은 실사용 리뷰를 분석하고 요약하는 블로거입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return res['choices'][0]['message']['content']

def clean_text(text):
    return re.sub(r'\*\*|__', '', text)

def shorten_description(text):
    if ',' in text:
        return text.split(',')[0].strip()
    return text.strip()

def apply_seo_fixes(review, html, product_name):
    keyword = product_name if len(product_name) <= 20 else ' '.join(product_name.split()[:6])
    meta = review.strip().split('\n')[0]
    if keyword not in meta:
        meta = f"{keyword}에 대한 실사용 후기와 요약 정보입니다. " + meta
        meta = (meta + " 다양한 사용자 의견을 바탕으로 정리했습니다.")[:155]
        html = f"<p><strong>{keyword}</strong>에 대해 궁금하신가요? 아래에서 자세히 알려드릴게요!</p>\n" + html
    return html, meta, keyword

def insert_seo_meta(html, keyword, meta_desc):
    return html

def get_or_create_category(slug):
    r = requests.get(f"{WP_URL.replace('/posts', '/categories')}?slug={slug}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    if r.status_code == 200 and r.json():
        return r.json()[0]['id']
    name_map = {
        "tech-gadgets": "🎧 테크・가전",
        "home-living": "🏠 홈리빙",
        "travel-leisure": "🎒 여행・레저",
        "daily-pick": "🧼 생활꿀템",
        "pet-picks": "🐾 반려동물",
        "kids-life": "👶 유아동",
        "hot-now": "📰 오늘의 추천",
    }
    name = name_map.get(slug, slug)
    res = requests.post(
        f"{WP_URL.replace('/posts', '/categories')}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "name": name,
            "slug": slug,
            "description": f"{name} 관련 콘텐츠 모음입니다."
        }),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )
    return res.json()['id']

def generate_tags(product_name):
    return [w for w in re.findall(r'[가-힣a-zA-Z0-9]+', product_name) if len(w) > 1][:5]

def get_or_create_tags(tag_names):
    tag_ids = []
    for tag in tag_names:
        r = requests.get(f"{WP_URL.replace('/posts', '/tags')}?search={tag}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
        if r.json():
            tag_ids.append(r.json()[0]['id'])
        else:
            res = requests.post(
                f"{WP_URL.replace('/posts', '/tags')}",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"name": tag}),
                auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
            )
            tag_ids.append(res.json()['id'])
    return tag_ids

def build_html(product, content):
    return f"""
<p>💰 <strong>가격:</strong> {product['price']}원 &nbsp;|&nbsp; ⭐ <strong>평점:</strong> ⭐⭐⭐⭐점</p>
<h5>※쿠팡 파트너스 활동의 일환으로, 일정액의 수수료를 제공받습니다.※</h5>
<div style="border:1px solid #ddd; padding:15px; background:#f9f9f9; border-radius:10px;">
    <img src="{product['image']}" style="max-width:100%; border-radius:10px;">
    <br><a href="{product['url']}" target="_blank" style="display:inline-block; margin-top:10px; background:#ff4800; color:white; padding:10px 20px; border-radius:5px;">🛒 최저가 보러가기</a>
</div>
<h3>📦 제품 리뷰</h3>
{content}
"""

def upload_image_to_wp(img_url):
    img_data = requests.get(img_url).content
    filename = img_url.split("/")[-1]
    media_headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": "image/jpeg"
    }
    media_response = requests.post(
        WP_URL.replace("/posts", "/media"),
        headers=media_headers,
        data=img_data,
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )
    if media_response.status_code in [200, 201]:
        return media_response.json()["id"]
    else:
        print("⚠️ 이미지 업로드 실패:", media_response.status_code, media_response.text)
        return None

def post_to_wp(product, html, keyword, meta_desc, category_slug):
    tag_ids = get_or_create_tags(generate_tags(product['name']))
    cat_id = get_or_create_category(category_slug)
    slug = product['name'].strip().replace(" ", "-")
    featured_image_id = upload_image_to_wp(product['image'])

    post = {
        "title": f"{product['name']} 리뷰",
        "slug": slug,
        "content": html,
        "status": "publish",
        "tags": tag_ids,
        "categories": [cat_id],
        "meta": {
            "_custom_meta_description": meta_desc,
            "_custom_meta_keywords": keyword
        }
    }

    if featured_image_id:
        post["featured_media"] = featured_image_id

    r = requests.post(
        WP_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(post),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )

    if r.status_code not in [200, 201]:
        raise Exception(f"등록 실패: {r.status_code}, {r.text}")

    pid = r.json()["id"]
    print(f"✅ 글 등록 성공 - ID {pid}")

    time.sleep(3)
    patch = {
        "content": html + "\n<!-- REFRESH -->"
    }

    patch_res = requests.put(
        f"{WP_URL}/{pid}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(patch),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )
    print("📦 PATCH 응답 코드:", patch_res.status_code)

# ✅ 메인 실행
if __name__ == "__main__":
    try:
        print_progress(0, "시작 중...")
        product = get_random_best_product()
        print_progress(25, "상품 로딩 중...")
        review = generate_review(product['name'], product['url'])
        print_progress(50, "리뷰 생성 중...")
        content = clean_text(review)
        content, meta_desc, keyword = apply_seo_fixes(review, content, product['name'])
        html = insert_seo_meta(build_html(product, content), keyword, meta_desc)
        print_progress(75, "SEO 최적화 HTML 생성 중...")
        category_slug = COUPANG_CATEGORY_SLUG_MAP.get(product['cat_id'], "hot-now")
        post_to_wp(product, html, keyword, meta_desc, category_slug)
        print_progress(100, "업로드 완료 ✅")
    except Exception as e:
        print("❌ 오류 발생:", e)
