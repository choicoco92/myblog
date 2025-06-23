# config.py
import os
import openai

# OpenAI API Key
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# WordPress API settings
WP_URL = os.environ['WP_URL']
WP_USERNAME = os.environ['WP_USERNAME']
WP_PASSWORD = os.environ['WP_PASSWORD']

# WordPress API settings
WP_URL2 = os.environ['WP_URL2']
WP_USERNAME2 = os.environ['WP_USERNAME2']
WP_PASSWORD2 = os.environ['WP_PASSWORD2']

# 쿠팡 세팅
CP_ACCESS_KEY = os.environ['CP_ACCESS_KEY']
CP_SECRET_KEY = os.environ['CP_SECRET_KEY']
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
