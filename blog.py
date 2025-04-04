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
    1001: "여성패션", 1002: "남성패션", 1010: "뷰티", 1011: "출산/유아동",
    1013: "주방용품", 1014: "생활용품", 1015: "홈인테리어", 1016: "가전디지털",
    1017: "스포츠/레저", 1018: "자동차용품", 1019: "도서/음반/DVD", 1020: "완구/취미",
    1021: "문구/오피스", 1024: "헬스/건강식품", 1025: "국내여행", 1026: "해외여행",
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
구성: 1. 구매 전 고려할 점, 2. 제품의 주요 특징, 3. 장점과 단점, 4. 실사용 팁, 5. 총평과 이런 분께 추천
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "당신은 리뷰 전문 블로거입니다."}, {"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response['choices'][0]['message']['content']


def clean_text(text):
    return re.sub(r'\*\*|__', '', text)


def get_meta_description(text):
    return text.strip().split('\n')[0][:140]


def spread_keyword(html, keyword):
    lines = html.split('</p>')
    for i in range(1, len(lines), max(1, len(lines)//3)):
        lines[i] += f" <strong>{keyword}</strong>"
    return '</p>'.join(lines)


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


def internal_link_block():
    return """
<div style="border:1px dashed #ccc; padding:10px; margin-top:20px;">
📌 오늘의 특가상품!: <a href="https://link.coupang.com/a/cmOStk" target="_blank">보러가기</a>
</div>
"""


def insert_seo_meta(html, keyword, meta_desc):
    seo_block = f"""<meta name=\"description\" content=\"{meta_desc}\">
<meta name=\"keywords\" content=\"{keyword}\">"""
    return seo_block + "\n\n" + html


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


def build_html(product, review_text):
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
    content = format_html(review_text)
    content = spread_keyword(content, product['name'])
    final = body + content + internal_link_block() + hashtag_block(product['name'])
    meta_desc = get_meta_description(review_text)
    return insert_seo_meta(final, product['name'], meta_desc)


def post_to_wp(product, html):
    post = {
        "title": f"{product['name']} 리뷰",
        "content": html,
        "status": "publish"
    }

    res = requests.post(
        WP_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(post),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )

    print(f"✅ 워드프레스 업로드 완료: {res.status_code}")
    print(res.json())


if __name__ == "__main__":
    try:
        print_progress(0, "시작 중...")
        product = get_random_best_product()
        print_progress(25, "쿠팡 상품 가져오는 중...")

        review = generate_review(product['name'])
        print_progress(50, "리뷰 생성 중...")

        review = clean_text(review)
        html = build_html(product, review)
        print_progress(75, "HTML 변환 중...")

        post_to_wp(product, html)
        print_progress(100, "업로드 완료!")

    except Exception as e:
        print("❌ 오류 발생:", e)
