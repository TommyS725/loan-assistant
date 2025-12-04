import os

from dotenv import load_dotenv

from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from watsonx import credentials, WATSONX_PROJECT_ID

load_dotenv()

model_id = os.getenv("WATSONX_MODEL_ID", "mistralai/mistral-medium-2505")


def get_model():
    print(f"Using model ID: {model_id}")
    client = APIClient(credentials=credentials, project_id=WATSONX_PROJECT_ID)
    llm = ChatWatsonx(
        model_id=model_id,
        watsonx_client=client,
        params={"temperature": 0.1, "max_new_tokens": 4096},
    )
    return llm, client
