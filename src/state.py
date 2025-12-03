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
    chat_history: List[ChatMessage] = field(default_factory=list)


def get_app_state() -> AppState:
    """Return a typed AppState instance stored in `st.session_state['app_state']`.

    Ensures a single container object is used for the session which improves DX
    (attribute access, autocompletion, and stronger typing).
    """
    if "app_state" not in st.session_state:
        st.session_state["app_state"] = AppState()
    return cast(AppState, st.session_state["app_state"])
