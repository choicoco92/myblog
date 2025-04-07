import requests
import random
import json
import openai
import hashlib
import hmac
import re
from time import gmtime, strftime
from requests.auth import HTTPBasicAuth
from config import *

openai.api_key = OPENAI_API_KEY

CATEGORIES = {
    1016: "가전디지털",
    1015: "홈인테리어",
    1017: "스포츠/레저",
    1018: "자동차용품",
    1025: "국내여행", 1026: "해외여행",
    1029: "반려동물용품", 1030: "유아동패션"
}
EXCLUDE_CATEGORY = [1012]
VALID_CATEGORIES = [k for k in CATEGORIES if k not in EXCLUDE_CATEGORY]

def print_progress(percent, message):
    bar_len = 30
    filled_len = int(bar_len * percent // 100)
    bar = '█' * filled_len + '░' * (bar_len - filled_len)
    print(f"[{bar}] {percent}% - {message}")

def generateHmac(method, full_url_path, secretKey, accessKey):
    if '?' in full_url_path:
        path, query = full_url_path.split('?', 1)
    else:
        path, query = full_url_path, ""

    signed_date = strftime('%y%m%dT%H%M%SZ', gmtime())
    message = signed_date + method + path + query

    signature = hmac.new(secretKey.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={accessKey}, signed-date={signed_date}, signature={signature}"

def get_random_best_product():
    for _ in range(5):
        category_id = random.choice(VALID_CATEGORIES)
        path = f"/v2/providers/affiliate_open_api/apis/openapi/products/bestcategories/{category_id}?limit=1"
        full_url = f"https://api-gateway.coupang.com{path}"

        auth_header = generateHmac("GET", path, CP_SECRET_KEY, CP_ACCESS_KEY)
        response = requests.get(full_url, headers={"Authorization": auth_header, "Content-Type": "application/json"})

        if response.status_code != 200:
            print(f"❌ API 오류: {response.status_code}")
            continue

        data = response.json().get("data", [])
        if not data:
            continue

        product = data[0]
        return {
            "name": product["productName"],
            "image": product["productImage"],
            "price": product["productPrice"],
            "url": product["productUrl"]
        }

    raise Exception("🚨 쿠팡 상품을 가져올 수 없습니다.")

def generate_review(product_name):
    prompt = f"""
'{product_name}' 제품에 대해 SEO 최적화된 블로그 리뷰 글을 3000자 이상, 800단어 이상 분량으로 작성해줘.
구성: 1. 구매 전 고려할 점, 2. 제품의 주요 특징, 3. 장점과 단점, 4. 실사용 팁, 5. 총평과 이런 분께 추천.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "당신은 리뷰 전문 블로거입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response['choices'][0]['message']['content']

def clean_text(text):
    return re.sub(r'\*\*|__', '', text)

def format_html(text):
    html = []
    lines = text.strip().split('\n')
    in_box = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d+\.\s', line):
            html.append(f"<h2>{line}</h2>")
        elif '총평' in line:
            html.append('<div style="background:#f4f4f4; border-left:5px solid #333; padding:10px;"><h2>' + line + '</h2>')
            in_box = True
        elif '추천' in line:
            html.append('<div style="background:#fff9e6; border-left:5px solid #ffa500; padding:10px;"><h2>' + line + '</h2>')
            in_box = True
        elif in_box:
            html.append(f"<p>{line}</p></div>")
            in_box = False
        elif line.startswith("- ") or line.startswith("•"):
            html.append(f"<ul><li>{line[2:]}</li></ul>")
        else:
            html.append(f"<p>{line}</p>")
    return '\n'.join(html)

def apply_seo_fixes(review, html_content, product_name):
    keyword_words = product_name.split()
    keyword = ' '.join(keyword_words[:6]) if len(keyword_words) > 6 else product_name

    def get_meta_description(text, keyword):
        first_line = text.strip().split('\n')[0]
        if keyword not in first_line:
            first_line = f"{keyword}에 대한 솔직 리뷰를 지금 확인해보세요.  {first_line}"
        if len(first_line) < 120:
            first_line += " 이 제품은 어떤 점이 좋은지, 아쉬운 점은 무엇인지 직접 써보고 분석해봤어요."
        return first_line[:155]

    def insert_intro_keyword(content, keyword):
        keyword = keyword.rstrip(',')  # ← 여기 추가
        intro = f"<p><strong>{keyword}</strong>에 대해 궁금하신가요? 리뷰로 자세히 소개해드릴게요!</p>\n"
        return intro + content
    def internal_link_block():
        return """
<div style=\"border:1px dashed #ccc; padding:10px; margin:20px 0;\">
👉 <strong>쿠팡 베스트 상품모아보기:</strong> <a href=\"/wp-content/pages/coupang-products.html\" target=\"_blank\">인기 상품 모아보기</a>
</div>
"""
    meta_desc = get_meta_description(review, keyword)
    html_content = insert_intro_keyword(html_content, keyword)
    html_content += internal_link_block()

    return html_content, meta_desc, keyword

def insert_seo_meta(html, keyword, meta_desc):
    keyword = keyword.rstrip(',')  # ← 여기 추가
    seo_block = f"""<meta name="description" content="{meta_desc}">
<meta name="keywords" content="{keyword}">"""
    return seo_block + "\n\n" + html

def build_html(product, content):
    body = f"""
<h2>{product['name']} 리뷰</h2>
<p><strong>요약:</strong> 이 제품은 현재 쿠팡에서 인기 있는 상품 중 하나로, {product['price']}원에 판매되고 있습니다.</p>

<div style="border:1px solid #ddd; padding:15px; border-radius:10px; background:#f9f9f9; margin-bottom:20px;">
    <img src="{product['image']}" alt="{product['name']}" style="max-width:100%; border-radius:10px;"><br><br>
    <strong style="font-size:18px;">상품명:</strong> {product['name']}<br>
    <strong style="font-size:18px;">가격:</strong> {product['price']}원<br><br>
    <a href="{product['url']}" target="_blank" style="display:inline-block; background:#ff4800; color:#fff; padding:10px 20px; border-radius:5px; text-decoration:none; font-weight:bold;">💰 최저가 보러가기</a>
</div>

<h3>📦 상세 리뷰</h3>
"""
    return body + content + hashtag_block(product['name'])

def generate_hashtags(product_name):
    words = re.findall(r'[가-힣a-zA-Z0-9]+', product_name)
    base_tags = ['리뷰', '쿠팡추천', '인기상품']
    tags = [f"#{word}" for word in words if len(word) > 1]
    return ' '.join(tags + [f"#{tag}" for tag in base_tags])

def hashtag_block(product_name):
    tags = generate_hashtags(product_name)
    return f"""
<div style=\"margin-top:20px; font-size:14px; color:#555;\">
{tags}
</div>
"""

def generate_tags(product_name):
    words = re.findall(r'[가-힣a-zA-Z0-9]+', product_name)
    tags = [word.strip() for word in words if len(word) > 1]
    return tags[:5]

def get_or_create_tags(tag_names):
    tag_ids = []
    for tag in tag_names:
        res = requests.get(
            f"{WP_URL.replace('/posts', '/tags')}?search={tag}",
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
        )
        data = res.json()
        if data:
            tag_ids.append(data[0]['id'])
        else:
            new_tag = {"name": tag}
            res = requests.post(
                WP_URL.replace('/posts', '/tags'),
                headers={"Content-Type": "application/json"},
                data=json.dumps(new_tag),
                auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
            )
            tag_ids.append(res.json()['id'])
    return tag_ids

def post_to_wp(product, html, keyword, meta_desc):
    tag_names = generate_tags(product['name'])
    tag_ids = get_or_create_tags(tag_names)

    post = {
        "title": f"{product['name']} 리뷰",
        "content": html,
        "status": "publish",
        "tags": tag_ids
    }

    res = requests.post(
        WP_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(post),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )

    if res.status_code not in [200, 201]:
        raise Exception(f"🚨 글 등록 실패: {res.status_code}")

    post_id = res.json().get("id")
    print(f"✅ 글 등록 성공 - ID: {post_id}")

    meta = {
        "meta": {
            "_yoast_wpseo_focuskw": keyword.rstrip(','),        # ← 쉼표 제거
            "_yoast_wpseo_metadesc": meta_desc
        }
    }

    seo_res = requests.post(
        f"{WP_URL}/{post_id}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(meta),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )

    if seo_res.status_code not in [200, 201]:
        print("⚠️ Yoast SEO 메타 업데이트 실패:", seo_res.status_code)
    else:
        print("✅ Yoast SEO 메타 적용 완료")

if __name__ == "__main__":
    try:
        print_progress(0, "시작 중...")
        product = get_random_best_product()
        print_progress(25, "쿠팡 상품 가져오는 중...")

        review = generate_review(product['name'])
        print_progress(50, "리뷰 생성 중...")

        review = clean_text(review)
        content = format_html(review)
        content, meta_desc, fixed_keyword = apply_seo_fixes(review, content, product['name'])

        final_html = build_html(product, content)
        final_html = insert_seo_meta(final_html, fixed_keyword, meta_desc)
        print_progress(75, "HTML 변환 중...")

        post_to_wp(product, final_html, fixed_keyword, meta_desc)
        print_progress(100, "업로드 완료!")

    except Exception as e:
        print("❌ 오류 발생:", e)
