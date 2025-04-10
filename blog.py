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
import time

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

CATEGORY_NAME = "쿠팡리뷰 | 오늘의 추천 상품과 실사용 후기 정리"


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
        path = f"/v2/providers/affiliate_open_api/apis/openapi/products/bestcategories/{category_id}?limit=30"
        full_url = f"https://api-gateway.coupang.com{path}"

        auth_header = generateHmac("GET", path, CP_SECRET_KEY, CP_ACCESS_KEY)
        response = requests.get(full_url, headers={"Authorization": auth_header, "Content-Type": "application/json"})

        if response.status_code != 200:
            print(f"❌ API 오류: {response.status_code}")
            continue

        data = response.json().get("data", [])
        if not data:
            continue

        product = random.choice(data)
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
        keyword = keyword.rstrip(',')
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
    html_content = limit_keyword_usage(html_content, keyword, limit=3)

    return html_content, meta_desc, keyword


def insert_seo_meta(html, keyword, meta_desc):
    keyword = keyword.rstrip(',')
    seo_block = f"""<meta name=\"description\" content=\"{meta_desc}\">
<meta name=\"keywords\" content=\"{keyword}\">"""
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


def get_or_create_category(category_name):
    res = requests.get(
        f"{WP_URL.replace('/posts', '/categories')}?search={category_name}",
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )
    if res.status_code != 200:
        raise Exception(f"🚨 카테고리 조회 실패: {res.status_code}")

    data = res.json()
    if data:
        return data[0]['id']
    else:
        new_cat = {"name": category_name, "description": f"{category_name} 관련 리뷰 모음입니다."}
        res = requests.post(
            WP_URL.replace('/posts', '/categories'),
            headers={"Content-Type": "application/json"},
            data=json.dumps(new_cat),
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
        )
        if res.status_code not in [200, 201]:
            raise Exception(f"🚨 카테고리 생성 실패: {res.status_code} - {res.text}")
        return res.json()['id']


def post_to_wp(product, html, keyword, meta_desc):
    tag_names = generate_tags(product['name'])
    tag_ids = get_or_create_tags(tag_names)
    category_id = get_or_create_category(CATEGORY_NAME)

    prefix = get_category_prefix(CATEGORY_NAME)
    slug_index = get_next_slug_index(prefix)
    slug = f"{prefix}-{slug_index}"

    post = {
        "title": f"{product['name']} 리뷰",
        "slug": slug,
        "content": html,
        "status": "publish",
        "tags": tag_ids,
        "categories": [category_id],
        "meta": {
            "_yoast_wpseo_focuskw": keyword.rstrip(','),
            "_yoast_wpseo_metadesc": meta_desc
        }
    }

    # 1차 등록
    res = requests.post(
        WP_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(post),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )

    if res.status_code not in [200, 201]:
        raise Exception(f"🚨 글 등록 실패: {res.status_code} - {res.text}")

    post_id = res.json().get("id")
    print(f"✅ 글 등록 성공 - ID: {post_id}")

    # ✅ 2차 저장 (Yoast 점수 계산 트리거용)
    patched_html = html + "\n<!-- YOAST REFRESH -->"
    patch_post = {
        "content": patched_html
    }

    time.sleep(5)
    patch_res = requests.put(
        f"{WP_URL}/{post_id}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(patch_post),
        auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
    )

    if patch_res.status_code in [200, 201]:
        print("✅ Yoast 점수 반영용 재저장 완료")
    else:
        print("⚠️ 재저장 실패:", patch_res.status_code, patch_res.text)

    # ✅ Yoast 점수 재계산 강제 호출
    refresh_url = f"https://mgddang.com/wp-json/custom/v1/yoast-refresh/{post_id}"  # 🔁 도메인 수정 필요
    refresh_res = requests.post(refresh_url)

    if refresh_res.status_code == 200:
        print("✅ Yoast 점수 강제 트리거 완료")
    else:
        print("⚠️ Yoast 트리거 실패:", refresh_res.status_code, refresh_res.text)



def get_category_prefix(category_name):
    if "쿠팡리뷰" in category_name:
        return "cp"
    elif "실시간정보" in category_name:
        return "jb"
    else:
        return "post"

def get_next_slug_index(prefix):
    page = 1
    all_slugs = []

    while True:
        res = requests.get(
            f"{WP_URL}?per_page=100&page={page}",
            auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD)
        )
        if res.status_code != 200:
            break

        data = res.json()
        if not data:
            break

        # prefix로 시작하는 slug만 추출
        matching = [
            post.get("slug", "") for post in data
            if post.get("slug", "").startswith(prefix + "-")
        ]
        all_slugs.extend(matching)
        page += 1

    # 숫자 인덱스 추출
    max_index = 0
    for slug in all_slugs:
        match = re.match(rf"{prefix}-(\d+)$", slug)  # 정확히 cp-숫자
        if match:
            idx = int(match.group(1))
            max_index = max(max_index, idx)

    return max_index + 1


def limit_keyword_usage(text, keyword, limit=3):
    """
    본문에서 키워드가 너무 자주 나오는 걸 방지 (최대 limit회만 유지)
    """
    keyword_pattern = re.escape(keyword)
    matches = list(re.finditer(keyword_pattern, text, flags=re.IGNORECASE))

    if len(matches) <= limit:
        return text  # 제한 안 넘으면 그대로 반환

    # 초과된 키워드 위치 제거
    new_text = text
    count = 0
    offset = 0
    for match in matches:
        if count < limit:
            count += 1
            continue
        start, end = match.start() + offset, match.end() + offset
        # 키워드 제거 (또는 다른 유사어로 바꾸려면 여기 수정)
        new_text = new_text[:start] + new_text[end:]
        offset -= (end - start)

    return new_text

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
