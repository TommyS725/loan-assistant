from dataclasses import dataclass, field
from typing import Any, List, Optional, cast, Literal, TypedDict
import streamlit as st

from model import User, UserLoanWithDetails
from agent import ReActAgent
from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from sqlite3 import Connection as SQLiteConnection
from rag import RAG
from langchain.tools import BaseTool


class ChatMessage(TypedDict):
    role: Literal["user", "assistant"]
    content: str
    time: str


# A friendly, actionable welcome message used by the Streamlit UI.
# Mention the app capabilities and the specific tools/endpoints available
# (knowledge lookup, DB queries, application routing, APR calculation, document analysis).
WELCOME_MESSAGE = """🏦 **Welcome to Your Professional Loan Assistant**

I'm here to help with accurate, context-aware information about loans using our available tools and data sources.

**What I can do (functions I use):**
- **Knowledge lookup:** Answer current loan product details from the knowledge base and market data.
- **Loan:** Read your existing applications and loans offered in the market.
- **Personal Suggestion and Apply:** Suggest loan base on your profile, and apply for you if you want.
- **APR & calculations:** Calculate APR and monthly payments using precise formulas.

**💼 My Expertise Areas:**
- **Loan Types:** Personal, auto, business, student, mortgage, home equity
- **Eligibility & Records:** Credit score thresholds, income requirements, and application history from your DB
- **Financial Calculations:** APR, monthly payment breakdowns (via tools), fees and amortization details
- **Process Guidance:** Application steps, required documents, and next actions (I do not provide financial advice)


**🚀 How to get the most from me:**
1. **Ask about loans:** Inquire loan knowledge, your applications, or market offerings.
2. **Ask specific questions** (e.g., "What is the APR on my Student Loan #5?" or "Which loans are still active?").
3. **To apply:** say "I want to apply for [loan name]" or confirm the `LOAN_ID` I extracted and I will include the `LOAN_ID` for routing.

**💡 Example prompts:**
- "What is a personal loan?"
- "What's the APR for my loans?"
- "Show my active loans and the monthly payments."
- "Suggest loans I might qualify for."
- "I want to apply for the the loan you suggested."

I base answers only on the data and tools available. I do not give financial advice — for decisions, consult a licensed professional."""


def get_welcome_message() -> ChatMessage:
    return ChatMessage(
        role="assistant",
        content=WELCOME_MESSAGE,
        time="",
    )


# - **Document analysis:** Uploads are prioritized and processed by the vision/OCR pipeline and used for RAG context when relevant.

# **📄 Document Features:**
# - **Upload & Process:** PDF, images, and text files — I extract text and summarize content
# - **Vision + RAG:** I use vision OCR for scanned pages and retrieval-augmented generation to provide contextual answers


@dataclass
class AppState:
    resources_initialized: bool = False
    llm: Optional[ChatWatsonx] = None
    client: Optional[APIClient] = None
    db_conn: Optional[SQLiteConnection] = None
    rag: Optional[RAG] = None
    tools: List[BaseTool] = field(default_factory=list)
    users: List[User] = field(default_factory=list)
    agent: Optional[ReActAgent] = None
    current_user_id: Optional[int] = None
    applied_loans: List[UserLoanWithDetails] = field(default_factory=list)
    chat_history: List[ChatMessage] = field(
        default_factory=lambda: [get_welcome_message()]
    )


def get_app_state() -> AppState:
    """Return a typed AppState instance stored in `st.session_state['app_state']`.

    Ensures a single container object is used for the session which improves DX
    (attribute access, autocompletion, and stronger typing).
    """
    if "app_state" not in st.session_state:
        st.session_state["app_state"] = AppState()
    return cast(AppState, st.session_state["app_state"])
