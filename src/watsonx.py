import os
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials

load_dotenv()


WATSONX_APIKEY = os.getenv("WATSONX_APIKEY")
WATSONX_URL = os.getenv("WATSONX_URL")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")

if not WATSONX_APIKEY or not WATSONX_URL or not WATSONX_PROJECT_ID:
    raise ValueError("Missing Watsonx.ai configuration in environment variables.")

credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_APIKEY)
