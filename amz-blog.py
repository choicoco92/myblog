# ✅ Unified Auto Posting Script for Global Audience (High-CPC Strategy)

import requests, json, openai, re, time, random
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from config import * # Make sure to use a config file for your English blog
import requests
import time
from urllib.parse import quote
from urllib.parse import urlparse, unquote
from datetime import datetime
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Load API keys from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WP_URL = os.getenv('WP_URL')
WP_USERNAME = os.getenv('WP_USERNAME')
WP_PASSWORD = os.getenv('WP_PASSWORD')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')

print("🔑 OPENAI_API_KEY:", OPENAI_API_KEY[:10] + "...")
print("🌐 WP_URL:", WP_URL)

openai.api_key = OPENAI_API_KEY

CATEGORY_MAP = {
    "finance": "💰 Finance & Investing",           
    "health": "💪 Health & Wellness",
    "tech": "🔌 Tech & Gadgets",  
    "legal": "⚖️ Legal",
    "marketing": "📈 Marketing & Business",
    "lifestyle": "🏠 Lifestyle & Home",
    "education": "📚 Education & Career",
    "software": "💻 Software & Services",
    "ai_generated": "🎯 AI Recommended"
}

HIGH_CPC_KEYWORDS = {
    "finance": [
        "credit card for bad credit", "online loans", "investment platforms", "stock trading apps", "cryptocurrency exchange",
        "mortgage calculator", "refinance rates", "debt consolidation", "personal finance software", "car insurance quotes",
        "life insurance policy", "financial advisor", "401k plans", "small business loans", "tax relief services",
        "best online brokers", "robo-advisors comparison", "high-yield savings accounts", "student loan refinancing", "credit repair services",
        "free credit score", "best checking accounts", "business credit cards", "no-fee stock trading", "real estate investing",
        "how to invest in stocks", "beginner stock market guide", "best mutual funds", "ETF investing", "options trading for beginners",
        "forex trading platforms", "gold investment", "silver price today", "Bitcoin price analysis", "Ethereum wallet",
        "NFT marketplace", "how to buy cryptocurrency", "blockchain technology explained", "decentralized finance (DeFi)", "best tax software",
        "tax preparation services", "what is an IRA", "Roth IRA vs Traditional IRA", "SEP IRA for self-employed", "how to start a budget",
        "budgeting apps", "financial planning", "retirement calculator", "net worth tracker", "best cash back credit cards",
        "travel rewards credit cards", "balance transfer credit cards", "secured credit cards", "unsecured personal loans", "peer-to-peer lending",
        "bad credit loans guaranteed approval", "payday loans online", "home equity loan (HELOC)", "FHA loan requirements", "VA loan rates",
        "jumbo loan limits", "mortgage pre-approval", "auto loan calculator", "boat financing", "RV loans",
        "small business administration (SBA) loans", "merchant cash advance", "invoice factoring companies", "best business bank accounts", "sole proprietorship vs LLC",
        "how to start an LLC", "passive income ideas", "how to make money online", "financial independence retire early (FIRE)", "investment property calculator",
        "commercial real estate loans", "hard money lenders", "private mortgage insurance (PMI)", "understanding credit reports", "how to improve credit score",
        "identity theft protection", "credit monitoring services", "best insurance companies", "term life vs whole life insurance", "disability insurance",
        "long-term care insurance cost", "health savings account (HSA)", "flexible spending account (FSA)", "529 college savings plan", "annuity rates"
    ],
    "health": [
        "mesothelioma lawyer", "online therapy", "rehab centers", "health insurance plans", "diet programs",
        "weight loss supplements", "medical alert systems", "CBD oil", "dental implants cost", "addiction treatment",
        "back pain relief", "hearing aids", "anti-aging cream", "telehealth services", "lasik eye surgery cost",
        "best online therapy platforms", "couples counseling online", "teen therapy", "PTSD treatment centers", "alcohol rehab near me",
        "drug detox programs", "affordable health insurance", "short term health insurance", "Medicare Advantage plans", "Medicaid eligibility",
        "Noom review", "Weight Watchers (WW) plan", "keto diet plan", "intermittent fasting guide", "best meal replacement shakes",
        "GOLO diet cost", "Optavia diet", "Nutrisystem for men", "best probiotics for women", "collagen peptides benefits",
        "vitamin D supplements", "omega-3 fish oil", "turmeric curcumin benefits", "ashwagandha for anxiety", "elderberry gummies",
        "senior alert systems", "fall detection devices", "Life Alert cost", "Medical Guardian reviews", "Bay Alarm Medical",
        "full spectrum CBD oil", "CBD for pain relief", "CBD gummies for sleep", "best CBD cream", "is CBD legal",
        "all-on-4 dental implants", "cost of dentures", "teeth whitening kits", "Invisalign cost", "veneers cost",
        "outpatient rehab programs", "luxury rehab facilities", "holistic treatment centers", "dual diagnosis treatment", "sober living homes",
        "chiropractor near me", "physical therapy for sciatica", "acupuncture for back pain", "massage therapy", "inversion table benefits",
        "Eargo hearing aids review", "Starkey hearing aids", "Miracle-Ear cost", "cochlear implant surgery", "tinnitus treatment",
        "Botox cost", "Juvederm fillers", "microneedling benefits", "laser hair removal", "CoolSculpting cost",
        "Teladoc reviews", "Amwell vs Teladoc", "MDLive", "PlushCare", "Talkspace vs BetterHelp",
        "cataract surgery", "glaucoma treatment", "dry eye remedies", "best eye drops", "blue light glasses"
    ],
    "tech": [
        "web hosting services", "VPN services", "cloud storage", "antivirus software", "data recovery software",
        "website builder", "e-commerce platform", "gaming laptop", "CRM software", "project management tools",
        "email marketing software", "password manager", "best smartphones 2025", "smart home devices", "online backup services",
        "best web hosting for small business", "shared hosting vs VPS", "dedicated server hosting", "WordPress hosting", "Bluehost review",
        "ExpressVPN vs NordVPN", "best free VPN", "VPN for streaming Netflix", "how to set up a VPN", "ProtonVPN review",
        "Google Drive vs Dropbox", "iCloud storage pricing", "best cloud backup", "pCloud review", "IDrive personal backup",
        "Norton 360 review", "McAfee Total Protection", "Bitdefender antivirus", "best malware removal", "free antivirus for Windows 11",
        "Stellar Data Recovery", "EaseUS Data Recovery Wizard", "Recuva file recovery", "hard drive recovery service", "recover deleted photos",
        "Wix vs Squarespace", "best website builder for artists", "GoDaddy website builder", "Shopify vs BigCommerce", "how to start an online store",
        "best e-commerce hosting", "WooCommerce themes", "Magento development", "Salesforce CRM pricing", "HubSpot CRM review",
        "Zoho CRM", "best CRM for small business", "Asana vs Trello", "Monday.com review", "Basecamp project management",
        "Smartsheet features", "Mailchimp pricing", "Constant Contact review", "best email automation tools", "ConvertKit vs AWeber",
        "1Password vs LastPass", "best password manager free", "Dashlane review", "Keeper password manager", "Bitwarden review",
        "iPhone 17 rumors", "Samsung Galaxy S26 leaks", "Google Pixel 10 review", "best budget smartphone", "5G phone plans",
        "Amazon Echo vs Google Home", "Philips Hue smart lighting", "Ring video doorbell", "Nest thermostat", "smart plugs for Alexa",
        "Backblaze review", "Carbonite backup", "cloud backup for business", "NAS (Network Attached Storage)", "best personal cloud storage"
    ],
    "legal": [
        "personal injury lawyer", "car accident attorney", "divorce lawyer near me", "workers compensation lawyer", "real estate attorney",
        "bankruptcy lawyer", "criminal defense lawyer", "DUI lawyer", "medical malpractice attorney", "immigration lawyer",
        "truck accident lawyer", "motorcycle accident attorney", "slip and fall lawyer", "wrongful death lawsuit", "brain injury attorney",
        "how to find a good lawyer", "free legal consultation", "contingency fee lawyer", "average car accident settlement", "what to do after a car accident",
        "uncontested divorce process", "child custody lawyer", "alimony calculator", "legal separation vs divorce", "prenuptial agreement cost",
        "workplace injury rights", "how to file workers comp claim", "denied workers comp appeal", "social security disability lawyer", "long term disability insurance",
        "real estate closing attorney", "landlord tenant lawyer", "eviction notice process", "property dispute lawyer", "title search company",
        "Chapter 7 vs Chapter 13", "how to file for bankruptcy", "cost to file bankruptcy", "debt relief options", "life after bankruptcy",
        "felony defense lawyer", "misdemeanor charges", "expungement lawyer", "federal criminal defense", "white collar crime attorney",
        "DUI penalties by state", "field sobriety test refusal", "DWI vs DUI", "ignition interlock device", "how to beat a DUI",
        "hospital negligence lawyer", "birth injury lawyer", "surgical error lawsuit", "misdiagnosis lawyer", "nursing home abuse attorney",
        "green card application", "US citizenship test", "H1B visa lawyer", "deportation defense", "asylum seeker process",
        "business lawyer", "contract review attorney", "starting a business lawyer", "intellectual property lawyer", "patent attorney",
        "tax attorney", "IRS audit help", "offer in compromise", "innocent spouse relief", "tax levy release",
        "family law attorney", "adoption lawyer", "guardianship forms", "child support modification", "paternity test"
    ],
    "marketing": [
        "SEO services", "social media marketing agency", "email marketing platform", "PPC management services", "content marketing tools",
        "lead generation software", "digital marketing course", "webinar software", "affiliate marketing programs", "sales funnel builder",
        "local SEO services", "e-commerce SEO", "keyword research tools", "backlink checker", "Ahrefs vs SEMrush",
        "Facebook advertising agency", "Instagram marketing services", "TikTok marketing strategy", "LinkedIn advertising", "social media management tools",
        "Mailchimp alternative", "Constant Contact pricing", "HubSpot marketing hub", "Sendinblue review", "email automation workflows",
        "Google Ads management", "Facebook Ads expert", "Bing Ads agency", "programmatic advertising platforms", "PPC audit",
        "best content marketing examples", "content creation services", "copywriting services", "video marketing strategy", "BuzzSumo review",
        "lead capture forms", "landing page builder", "sales intelligence tools", "B2B lead generation", "OptinMonster review",
        "Google Digital Garage", "Coursera digital marketing", "Udemy SEO course", "digital marketing certificate", "learn digital marketing free",
        "Zoom webinar pricing", "GoToWebinar review", "best webinar platforms", "webinar best practices", "EverWebinar automated webinars",
        "Amazon Associates program", "ShareASale affiliate network", "CJ Affiliate review", "best affiliate products", "high ticket affiliate marketing",
        "ClickFunnels review", "Leadpages vs Instapage", "best landing page builders", "how to build a sales funnel", "funnel mapping tools",
        "marketing automation software", "Marketo pricing", "Pardot vs HubSpot", "ActiveCampaign review", "customer journey mapping",
        "influencer marketing platform", "how to find influencers", "micro-influencer marketing", "brand ambassador programs", "influencer outreach",
        "conversion rate optimization (CRO)", "A/B testing tools", "Google Optimize alternative", "VWO (Visual Website Optimizer)", "customer feedback tools",
        "best analytics tools", "Google Analytics 4 guide", "Hotjar review", "Crazy Egg heatmaps", "data visualization tools",
        "public relations (PR) agency", "press release distribution", "online reputation management", "brand monitoring tools", "HARO (Help a Reporter Out)"
    ],
    "lifestyle": [
        "moving companies", "home security systems", "solar panel cost", "HVAC repair", "pest control services",
        "online mattress", "meal delivery service", "travel deals", "luxury hotels", "car rental deals",
        "long distance moving companies", "local movers near me", "moving company quotes", "PODS cost", "U-Haul truck rental",
        "best home security system", "ADT vs Vivint", "SimpliSafe review", "Ring Alarm Pro", "DIY home security",
        "how much do solar panels save", "Tesla solar roof cost", "best solar companies", "solar panel installation", "community solar programs",
        "air conditioner repair", "furnace replacement cost", "emergency HVAC service", "duct cleaning services", "Nest thermostat installation",
        "Orkin vs Terminix", "bed bug treatment cost", "termite inspection", "rodent control", "mosquito control for yard",
        "best mattress in a box", "Purple mattress review", "Casper vs Purple", "Nectar mattress", "best hybrid mattress",
        "HelloFresh vs Blue Apron", "Factor meals review", "best prepared meal delivery", "Home Chef pricing", "Daily Harvest smoothies",
        "cheap flights", "Google Flights tracker", "all-inclusive resort deals", "last minute vacation deals", "best travel credit cards",
        "5-star hotels", "boutique hotels", "booking.com vs expedia", "best hotel booking sites", "Hyatt all-inclusive",
        "Enterprise vs Hertz", "Turo car rental", "best car rental company", "cheap car rentals", "RV rental USA",
        "home renovation contractors", "kitchen remodel cost", "bathroom renovation ideas", "basement finishing", "home addition cost",
        "landscaping companies near me", "lawn care services", "swimming pool installation", "hot tub cost", "deck builder",
        "interior design services", "online interior design", "best paint colors for living room", "furniture stores near me", "Wayfair vs Overstock",
        "best coffee subscription", "wine delivery clubs", "craft beer subscription", "butcher box review", "best streaming service"
    ],
    "education": [
        "online degree programs", "MBA programs", "coding bootcamp", "student loans", "online courses platform",
        "master's degree online", "GED test online", "financial aid for college", "scholarship search", "language learning apps",
        "accredited online colleges", "bachelor's degree online fast", "online psychology degree", "online nursing programs", "WGU review",
        "top MBA programs in the world", "online MBA no GMAT", "part-time MBA programs", "executive MBA cost", "Harvard MBA",
        "best coding bootcamps for job placement", "free coding bootcamp", "software engineering bootcamp", "data science bootcamp", "cybersecurity bootcamp",
        "student loan forgiveness", "how to apply for student loans", "private student loans", "student loan calculator", "FAFSA deadline",
        "Coursera vs edX", "Udemy vs Skillshare", "best online learning platforms", "LinkedIn Learning review", "MasterClass all access pass",
        "online master's in education", "master's in computer science online", "online master's in public health", "cheapest online master's degree", "one year master's programs",
        "how to get your GED online", "GED practice test", "GED classes near me", "HiSET vs GED", "cost of GED test",
        "how to get financial aid", "CSS profile guide", "Pell Grant eligibility", "work-study programs", "grants for college",
        "fastweb scholarships", "scholarships for high school seniors", "merit-based scholarships", "how to write a scholarship essay", "Cappex scholarships",
        "Duolingo vs Babbel", "best way to learn Spanish", "Rosetta Stone review", "Pimsleur method", "italki review",
        "CPA exam requirements", "PMP certification cost", "Google project management certificate", "AWS certification path", "CompTIA A+ certification",
        "how to study effectively", "best note-taking apps", "exam preparation tips", "improve concentration for studying", "online tutoring services",
        "Chegg study review", "Quizlet flashcards", "Grammarly premium review", "online proctoring services", "best academic planners"
    ],
    "software": [
        "best accounting software", "video editing software", "graphic design software", "collaboration tools", "HR software",
        "payroll software", "customer support software", "inventory management software", "ERP software", "webinar platforms",
        "QuickBooks Online review", "Xero vs QuickBooks", "FreshBooks pricing", "best free accounting software", "accounting software for small business",
        "Adobe Premiere Pro vs Final Cut Pro", "DaVinci Resolve tutorial", "best video editor for YouTube", "free video editing software", "Camtasia screen recorder",
        "Canva Pro review", "Adobe Photoshop free trial", "Figma vs Sketch", "best free graphic design software", "logo design software",
        "Slack vs Microsoft Teams", "Asana vs Monday", "Trello for project management", "Notion templates", "Miro online whiteboard",
        "best HR software for small business", "HRIS systems", "performance management software", "recruiting software", "Gusto HR review",

        "Gusto payroll review", "ADP RUN payroll", "Paychex Flex pricing", "best payroll services", "how to do payroll",
        "Zendesk vs Freshdesk", "HubSpot Service Hub", "best help desk software", "live chat software", "Intercom pricing",
        "best inventory management for small business", "Shopify inventory management", "barcode inventory system", "warehouse management system", "Square for retail",
        "NetSuite ERP review", "SAP S/4HANA", "what is ERP system", "Oracle ERP Cloud", "Microsoft Dynamics 365",
        "Zoom vs GoToWebinar", "best webinar software for marketing", "automated webinar software", "Webex events", "Livestorm review",
        "best CRM for startups", "Salesforce alternatives", "real estate CRM", "free CRM software", "Pipedrive review",
        "DocuSign vs Adobe Sign", "best e-signature software", "PandaDoc pricing", "contract management software", "HelloSign API",
        "best note-taking app", "Evernote vs OneNote", "GoodNotes for Windows", "Notion vs Evernote", "Bear app review",
        "best tax software", "TurboTax vs H&R Block", "FreeTaxUSA review", "tax filing software", "e-file state taxes"
    ]
}

# Global variable to track used keywords
used_keywords = set()

def generate_meta_description(title):
    current_year = datetime.now().year
    return f"Get the latest {current_year} information and expert analysis on {title}. Find detailed comparisons, buying guides, and top recommendations all in one place."

def generate_blog_content(keyword, category):
    current_year = datetime.now().year
    prompt = f"""
📰 Write a detailed, comprehensive guide about '{keyword}'.
Category: {category}

The article must provide specific, actionable information for the reader.

⚠️ **Critical Keyword Usage Rules**:
- Use the exact keyword phrase "{keyword}" only 2-3 times in the entire article.
- Maintain a keyword density of 1-2%.
- Do not repeat the keyword in the same paragraph or sentence.
- Actively use synonyms and related terms instead of the main keyword.
"""
    messages = [
        {
            "role": "system",
            "content": (
                f"You are an expert writer specializing in detailed, comprehensive guides for an English-speaking audience. Adhere strictly to the following instructions to write a blog post in English:\n"
                f"1.  **Length**: Minimum 800 words, aiming for 1200-1500 words with highly detailed, comprehensive content.\n"
                f"2.  **Specificity**: Use concrete numbers, prices, and step-by-step methods instead of abstract descriptions.\n"
                f"3.  **Real Information**: Use actual, well-known brand names, product names, and services available in the US/Globally. Avoid placeholders like 'XX' or 'YY'.\n"
                f"4.  **Tangible Benefits**: Clearly state real benefits and conditions (e.g., '$95 annual fee,' '20% discount,' 'free shipping').\n"
                f"5.  **Up-to-Date Information**: Use {current_year} data for products, services, and pricing. Avoid outdated information from previous years.\n"
                f"    - Smartphones: Mention iPhone 16 Pro, Galaxy S25 Ultra, Pixel 9 Pro, etc. ({current_year} models).\n"
                f"    - Laptops: Mention MacBook Pro M4, Dell XPS 16, etc. ({current_year} models).\n"
                f"    - Financial Products: Reflect {current_year} benefits and terms.\n"
                f"6.  **Keyword-Centric Subheadings**: Use specific subheadings directly related to the keyword. For 'Best Laptops', use subheadings like 'Top Laptops of {current_year}', 'How to Choose a Laptop by Use Case', 'Laptops by Price Range', etc.\n"
                f"7.  **Logical Structure**: Create a well-organized structure with natural, keyword-related subheadings.\n"
                f"8.  **Actionable Advice**: Provide concrete, easy-to-follow steps for the reader.\n"
                f"9.  **Credibility**: Include verifiable information and specific, real-world examples.\n"
                f"10. **Comparative Analysis**: Compare at least 5-7 specific options using real data.\n"
                f"11. **Pricing Details**: Offer specific price ranges whenever possible.\n"
                f"12. **Key Considerations**: Clearly outline important warnings or considerations for the reader.\n"
                f"13. **FAQ Section**: Include a section for Frequently Asked Questions related to the keyword.\n"
                f"14. **Call to Action (CTA)**: End the article with a clear, specific next step for the reader.\n"
                f"15. **Keyword Density & Synonyms**: Strictly use the main keyword 2-3 times. Keep density under 2%. Use synonyms and related terms (e.g., for 'Real Estate', use 'property market', 'housing investment').\n"
                f"16. **Urgency**: Use words like 'now,' 'today,' or 'don't miss out' where appropriate.\n"
                f"17. **HTML Formatting**: Use <h2>, <h3>, <h4>, <p>, <ul>, <li>, <strong>, <em> tags for structure and readability.\n"
                f"18. **Emojis**: Sparingly use relevant emojis to enhance readability.\n"
                f"19. **Authoritative Links**: If possible, include links to official websites or credible sources.\n"
                f"20. **In-Depth Explanations**: Provide thorough details in each section.\n"
                f"21. **High Relevance**: Ensure all content and subheadings are directly relevant to the keyword.\n"
                f"22. **SEO Best Practices**: Use the keyword in the H1 title (once). Include internal and external links.\n"
                f"23. **US/Global Focus**: All recommendations must be for services, brands, and products available in the United States or globally. Do not mention region-specific items from other countries.\n"
                f"24. **Strict Keyword Repetition Limit**: The focus keyword must appear only 2-3 times. If it appears more, it must be replaced with a synonym. Do not repeat the keyword in the same paragraph.\n"
            )
        },
        {"role": "user", "content": prompt}
    ]

    res = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=4000
    )
    return res['choices'][0]['message']['content']

def get_or_create_category(slug):
    name = CATEGORY_MAP.get(slug, slug.replace('-', ' ').title())
    url = f"{WP_URL.replace('/posts', '/categories')}"
    r = requests.get(f"{url}?slug={slug}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    if r.status_code == 200 and r.json():
        return r.json()[0]['id']
    
    res = requests.post(url, json={"name": name, "slug": slug}, auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
    if res.status_code == 201:
        return res.json().get('id')
    print(f"⚠️ Failed to create/get category: {res.text}")
    return None

def get_or_create_tags(tag_names):
    tag_ids = []
    url = f"{WP_URL.replace('/posts', '/tags')}"
    for tag in tag_names:
        r = requests.get(f"{url}?search={tag}", auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
        if r.status_code == 200 and r.json():
            tag_ids.append(r.json()[0]['id'])
        else:
            res = requests.post(url, json={"name": tag}, auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
            if res.status_code == 201:
                tag_ids.append(res.json().get("id"))
    return tag_ids

def reword_title(keyword):
    current_year = datetime.now().year
    patterns = [
        f"{current_year} {keyword.title()} Complete Guide",
        f"{keyword.title()}: Top 5 Picks for {current_year}",
        f"The Ultimate Guide to {keyword.title()}",
        f"{keyword.title()}: 7 Things You Must Know in {current_year}",
        f"Expert Review of {keyword.title()}",
        f"{keyword.title()}: Is It Worth It in {current_year}?",
    ]
    return random.choice(patterns)

def upload_image_to_wp(image_url, keyword=None):
    try:
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()
        img_data = resp.content
    except Exception as e:
        print("❌ Image download failed:", e)
        return None

    parsed_url = urlparse(image_url)
    filename = unquote(parsed_url.path.split("/")[-1])
    ext = filename.split(".")[-1].lower().split("?")[0] or "jpg"
    content_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")

    alt_text = f"{keyword} guide" if keyword else "guide image"

    media_headers = {
        "Content-Disposition": f"attachment; filename=image.{ext}",
        "Content-Type": content_type
    }

    try:
        media_response = requests.post(f"{WP_URL.replace('/posts', '/media')}", headers=media_headers, data=img_data, auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
        media_response.raise_for_status()
        media_json = media_response.json()
        
        # Add alt text to the image
        if keyword:
            requests.put(f"{WP_URL.replace('/posts', '/media')}/{media_json['id']}", json={"alt_text": alt_text}, auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))
        
        print("✅ Image uploaded successfully:", media_json.get("source_url"))
        return media_json["id"]
    except Exception as e:
        print("❌ Image upload failed:", e)
        return None

def generate_tags_with_gpt(keyword):
    prompt = f"The main keyword for the blog post is '{keyword}'. Recommend 10 suitable tags for this post, separated by commas. (e.g., tag1, tag2, ...)"
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
        print("❌ Could not get category ID, aborting post.")
        return

    meta_desc = generate_meta_description(title)
    
    try:
        tag_names = generate_tags_with_gpt(title)
    except Exception as e:
        print("⚠️ GPT tag generation failed, using basic method:", e)
        tag_names = re.findall(r'[a-zA-Z]{2,20}', title)[:5]

    tag_ids = get_or_create_tags(tag_names)
    media_id = None
    if image_url:
        media_id = upload_image_to_wp(image_url, title)
        if media_id:
            html = f'<img src="{image_url}" alt="{title}" style="max-width:100%; height:auto; border-radius:10px; margin-bottom: 20px;" />' + html

    post = {
        "title": reword_title(title),
        "content": html,
        "status": "publish",
        "categories": [cat_id],
        "tags": tag_ids,
        "meta": { 
            "rank_math_focus_keyword": title, 
            "rank_math_description": meta_desc,
        },
        **({"featured_media": media_id} if media_id else {})
    }

    r = requests.post(WP_URL, json=post, auth=HTTPBasicAuth(WP_USERNAME, WP_PASSWORD))

    if r.status_code in [200, 201]:
        print("✅ Post published successfully:", r.json().get('link'))
    else:
        print("❌ Posting failed:", r.text)

def generate_high_cpc_keywords_ai(category=None, count=5):
    """Dynamically generates high-CPC keywords using OpenAI."""
    if category:
        prompt = f"""
Recommend {count} high-CPC keywords for the following category.
Category: {category}

Requirements:
- Keywords with high commercial intent and search volume.
- Include action-oriented words like "buy," "book," "guide," "review," "comparison," "price," "best."
- Keywords that lead to actual purchases or service sign-ups.
- Write in English.
- List only the keywords, separated by commas (no newlines).

Example: keyword1, keyword2, keyword3, keyword4, keyword5
"""
    else:
        prompt = f"""
Recommend {count} high-CPC keywords.

Requirements:
- Choose keywords from different high-value niches like finance, health, tech, and legal.
- Include action-oriented words like "buy," "book," "guide," "review," "comparison," "price."
- Keywords that lead to actual purchases or service sign-ups.
- Write in English.
- List only the keywords, separated by commas (no newlines).
- Ensure variety across different niches.

Example: best business loans, cheap car insurance, online therapy sessions, data recovery software, personal injury lawyer
"""
    try:
        res = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=200)
        keywords_str = res['choices'][0]['message']['content'].strip().replace('\n', '')
        keywords = [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
        return keywords[:count]
    except Exception as e:
        print(f"⚠️ AI keyword generation failed: {e}")
        fallback = { "finance": ["loan comparison", "credit card review"], "health": ["diet plan", "online therapy"], "tech": ["best laptop", "vpn review"] }
        return fallback.get(category, ["buying guide", "top reviews"])[:count]

def get_dynamic_high_cpc_keyword():
    """Dynamically generates and selects a high-CPC keyword."""
    global used_keywords
    
    categories = list(HIGH_CPC_KEYWORDS.keys()) + ["ai_generated"]
    category = random.choice(categories)
    
    if category == "ai_generated":
        keywords = generate_high_cpc_keywords_ai(count=5)
        if keywords:
            unused = [kw for kw in keywords if kw not in used_keywords]
            selected_keyword = random.choice(unused) if unused else keywords[0]
            used_keywords.add(selected_keyword)
            print(f"🎯 AI Generated Keywords: {keywords}")
            print(f"✅ Selected Keyword: {selected_keyword}")
            return selected_keyword, "ai_generated"
        else:
            category = random.choice(list(HIGH_CPC_KEYWORDS.keys())) # Fallback
            base_keywords = HIGH_CPC_KEYWORDS[category]
    else:
        base_keywords = HIGH_CPC_KEYWORDS[category]

    other_category = random.choice([c for c in HIGH_CPC_KEYWORDS.keys() if c != category] or [category])
    ai_keywords = generate_high_cpc_keywords_ai(other_category, count=3)
    
    all_keywords = list(dict.fromkeys(base_keywords + ai_keywords))
    unused = [kw for kw in all_keywords if kw not in used_keywords]
    
    selected_keyword = random.choice(unused) if unused else random.choice(all_keywords)
    
    used_keywords.add(selected_keyword)
    print(f"🎯 Available keywords: {all_keywords}")
    print(f"✅ Final choice: {selected_keyword}")
    return selected_keyword, category

def get_pexels_image_url(keyword):
    """Gets an image URL from Pexels for a given keyword."""
    url = f'https://api.pexels.com/v1/search?query={quote(keyword)}&per_page=10&page=1&orientation=landscape'
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        photos = data.get('photos', [])
        if photos:
            photo = random.choice(photos)
            image_url = photo['src']['large2x']
            print(f"✅ Selected Pexels image: {image_url}")
            return image_url
    except Exception as e:
        print(f"⚠️ Pexels search failed: {e}")
    return None

def run_high_cpc_strategy():
    print("\n🚀 [START] High-CPC Keyword Auto-Posting for Global Audience\n")
    
    keyword, category_key = get_dynamic_high_cpc_keyword()
    print(f"🎯 Selected Keyword: {keyword} (Category: {category_key})")

    image_url = get_pexels_image_url(keyword)
    if not image_url:
        print("⚠️ Could not find an image on Pexels. Proceeding without a featured image.")
    
    category_name = CATEGORY_MAP.get(category_key, "General Info")
    html = generate_blog_content(keyword, category_name)
    post_to_wordpress(keyword, html, category_key, image_url)
    print(f"✅ Post finished for: {keyword}")

if __name__ == "__main__":
    run_high_cpc_strategy()
    print("\n🎉 All tasks completed!")
