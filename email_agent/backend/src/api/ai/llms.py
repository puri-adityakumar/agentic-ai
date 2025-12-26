import os

from langchain_openai import ChatOpenAI

OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL') or None
OPENAI_MODEL_NAME = os.environ.get('OPENAI_MODEL_NAME') or 'gpt-4o-mini'
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise NotImplementedError("`OPENAI_API_KEY` is required")

def get_openai_llm():
    openai_params = {
        "model": OPENAI_MODEL_NAME,
        "api_key": OPENAI_API_KEY
    }
    if OPENAI_BASE_URL:
        openai_params['base_url'] = OPENAI_BASE_URL
    return ChatOpenAI(**openai_params)
