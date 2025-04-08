import requests
import json
import re
import urllib.parse
from time import gmtime, strftime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import openai
from requests.auth import HTTPBasicAuth
from config import *

openai.api_key = OPENAI_API_KEY
CATEGORY_NAME = "실시간정보 | 지금 확인해야 할 최신 뉴스와 핫이슈"

# 구글 트렌드 키워드 1개 가져오기 (Selenium)
def get_google_trends_keywords():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.get("https://trends.google.co.kr/trending?geo=KR&hours=4")
    driver.implicitly_wait(5)

    try:
        keyword_element = driver.find_element(By.CSS_SELECTOR, 'div.mZ3RIc')
        keyword = keyword_element.text.strip()
    except Exception as e:
        keyword = None
        print("❌ 키워드 추출 실패:", e)

    driver.quit()
    return [keyword]

# 구글 뉴스 검색 결과 수집
def search_news_snippets(keyword, max_results=3):
    url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}&hl=ko"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    results = []
    for elem in soup.select('div.BNeawe.s3v9rd.AP7Wnd'):
        text = elem.get_text(strip=True)
        if text and len(text) > 40:
            results.append(f"- {text}")
        if len(results) >= max_results:
            break
    return "\n".join(results)

# GPT에게 글 생성 요청
def generate_blog_post(keyword):
    info_snippets = search_news_snippets(keyword)

    prompt = f"""
키워드: "{keyword}"

아래는 이 키워드에 대한 검색 정보 요약입니다:
\"\"\"
{info_snippets}
\"\"\"

위 정보를 참고하여 블로그 글을 작성해주세요.

요구사항:
- 해당 키워드에 대해 사람들이 궁금해할 내용을 중심으로 정리
- 배경 설명, 관련 이슈, 대중의 반응, 주목할 점 등을 포함해도 좋음
- SEO 최적화
- 3000자 이상
- 키워드를 제목과 서론에 자연스럽게 포함
- 너무 딱딱한 설명 말고, 블로그 글처럼 친근하고 읽기 쉬운 문체로 작성
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "당신은 다양한 주제를 다루는 블로그 작가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    print("✅ GPT 글 생성 완료")
    return response['choices'][0]['message']['content']



# HTML 포맷 (본문에 이미지 삽입)
def format_html_with_images(text, image_urls):
    html = []
    lines = text.strip().split('\n')
    img_index = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d+\.\s', line):
            html.append(f"<h2>{line}</h2>")
        else:
            html.append(f"<p>{line}</p>")
            if img_index < len(image_urls):
                html.append(f'<img src="{image_urls[img_index]}" style="width:100%; margin:20px 0; border-radius:10px;">')
                img_index += 1
    return '\n'.join(html)

# 구글 이미지 검색
def search_google_images(keyword, max_results=4):
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}&tbm=isch"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    image_urls = []
    for img_tag in soup.select('img'):
        src = img_tag.get('src')
        if src and src.startswith('http'):
            image_urls.append(src)
        if len(image_urls) >= max_results:
            break
    return image_urls

# 유튜브 영상 검색 후 iframe 삽입 (맨 하단에만 삽입)
def get_youtube_embed_html(keyword):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    import time
    import urllib.parse

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')

    driver = webdriver.Chrome(options=options)
    search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(keyword)}"
    driver.get(search_url)
    time.sleep(3)

    video_id = ""
    try:
        video_links = driver.find_elements(By.CSS_SELECTOR, 'a#video-title')

        for video in video_links:
            href = video.get_attribute("href")
            if href and "watch?v=" in href:
                video_id = href.split("watch?v=")[-1].split("&")[0]  # 영상 ID만 추출
                print("🎥 유튜브 영상 ID:", video_id)
                break

    except Exception as e:
        print("❌ 유튜브 영상 추출 실패:", e)

    driver.quit()

    if video_id:
        return f"""
<div style="margin:20px 0;">
<iframe width="100%" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>
</div>
"""
    else:
        print("⚠️ 유튜브 영상 ID를 찾지 못했어요.")
        return ""


# Yoast용 SEO 메타 및 내용 최종 조립
def insert_seo_meta(html, keyword, meta_desc):
    return f"""<meta name=\"description\" content=\"{meta_desc}\">
<meta name=\"keywords\" content=\"{keyword}\">\n\n{html}"""

# 포스트 본문 마무리
def build_html(keyword, content, youtube_html):
    return f"""
<h2>{keyword} - 실시간 이슈 분석</h2>
<p><strong>이슈 요약:</strong> 지금 한국에서 가장 주목받고 있는 키워드 <strong>{keyword}</strong>에 대해 깊이 있게 다뤄봅니다.</p>
<h3>📌 상세 분석</h3>
{content}
{youtube_html}
"""

# 슬러그 순차 증가용 인덱스 확인
def get_next_slug_index():
    prefix = "jb"
    page = 1
    all_slugs = []
    while True:
        res = requests.get(f"{WP_URL}?per_page=100&page={page}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
        if res.status_code != 200:
            break
        data = res.json()
        if not data:
            break
        matching = [post.get("slug", "") for post in data if post.get("slug", "").startswith(prefix + "-")]
        all_slugs.extend(matching)
        page += 1
    max_index = 0
    for slug in all_slugs:
        match = re.match(r"jb-(\d+)$", slug)
        if match:
            idx = int(match.group(1))
            max_index = max(max_index, idx)
    return max_index + 1

# 카테고리 및 태그 처리
def get_or_create_category(name):
    url = WP_URL.replace("/posts", "/categories")
    res = requests.get(f"{url}?search={name}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    if res.json(): return res.json()[0]['id']
    res = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps({"name": name}), auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    return res.json()['id']

def get_or_create_tag(name):
    url = WP_URL.replace("/posts", "/tags")
    res = requests.get(f"{url}?search={name}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    if res.json(): return res.json()[0]['id']
    res = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps({"name": name}), auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    return res.json()['id']

# 워드프레스 업로드
def post_to_wp(title, content, keyword, meta_desc):
    slug = f"jb-{get_next_slug_index()}"
    category_id = get_or_create_category(CATEGORY_NAME)
    tag_id = get_or_create_tag(keyword.split()[0])

    post = {
        "title": f"{title}",
        "slug": slug,
        "content": content,
        "status": "publish",
        "tags": [tag_id],
        "categories": [category_id],
        "meta": {
            "_yoast_wpseo_focuskw": keyword,
            "_yoast_wpseo_metadesc": meta_desc
        }
    }

    res = requests.post(WP_URL, headers={"Content-Type": "application/json"}, data=json.dumps(post), auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    if res.status_code in [200, 201]:
        print(f"✅ 업로드 성공 - {title}")
    else:
        print(f"❌ 업로드 실패: {res.status_code}", res.text)

# 실행
if __name__ == "__main__":
    try:
        keywords = get_google_trends_keywords()
        for keyword in keywords:
            print(f"🚀 키워드: {keyword}")
            text = generate_blog_post(keyword)
            image_urls = search_google_images(keyword)
            html_content = format_html_with_images(text, image_urls)
            youtube = get_youtube_embed_html(keyword)
            full_body = build_html(keyword, html_content, youtube)
            meta_desc = text.strip().split('\n')[0][:155]
            full_with_meta = insert_seo_meta(full_body, keyword, meta_desc)
            post_to_wp(keyword, full_with_meta, keyword, meta_desc)
    except Exception as e:
        import traceback
        print("❌ 오류 발생:", e)
        traceback.print_exc()
    input("\n완료되었습니다. Enter 키를 누르면 창이 닫힙니다.")