import streamlit as st
from model import User
import dal
from sqlite3 import Connection as SQLiteConnection
from agent import ReActAgent
from db import init_db
from rag import RAG
from tools import get_tools
from llm import get_model
from state import get_app_state, ChatMessage, get_welcome_message
from datetime import datetime
import utils


def chat_ui():
    """Modern chat UI using Streamlit chat primitives and typed AppState."""
    st.header("Chat with LoanGuide")
    state = get_app_state()

    # Ensure chat_history exists on the state
    if state.chat_history is None:
        state.chat_history = []

    # Render previous messages
    for msg in state.chat_history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        content = utils.normalize_text(content)
        with st.chat_message(role):
            st.write(content)

    # Chat input
    user_input = st.chat_input("Ask about loans, APR, or your loans...")

    if user_input:
        # Append and render user's message immediately
        user_msg = ChatMessage(
            role="user",
            content=user_input,
            time=str(datetime.now()),
        )
        state.chat_history.append(user_msg)
        with st.chat_message("user"):
            st.write(user_input)

        # Call agent with spinner
        ag = state.agent

        with st.chat_message("assistant"):
            with st.spinner("LoanGuide is thinking..."):
                try:
                    if ag is None:
                        assistant_response = "(Agent unavailable)"
                    else:
                        result = ag.invoke(user_input)
                        # result may be a dict with messages or a raw string
                        if (
                            isinstance(result, dict)
                            and "messages" in result
                            and result["messages"]
                        ):
                            last = result["messages"][-1]
                            # prefer attribute .content if present
                            raw = getattr(last, "content", last)
                        else:
                            raw = result

                        assistant_response = utils.normalize_text(raw)
                except Exception as e:
                    print("Agent invocation error:", e)
                    assistant_response = f"(Agent error) {e}"

                st.write(assistant_response)

        # Persist assistant response in UI history
        state.chat_history.append(
            {
                "role": "assistant",
                "content": assistant_response,
                "time": str(datetime.now()),
            }
        )


def applied_loans_page(selected_user: User, db_conn: SQLiteConnection):
    st.header("Applied Loans")

    if selected_user is None:
        st.info("Please select a user from the sidebar to view applied loans.")
        return

    # Fetch applied loans for user
    try:
        loans = dal.get_user_loans(db_conn, selected_user.user_id)
    except Exception:
        loans = []

    if not loans:
        st.info("No applied loans found for this user.")
        return

    # Display in a table
    table = []
    for ln in loans:
        table.append(ln.table_display())

    # Normalize table values for display (fix narrow no-break spaces etc.)
    normalized_table = []
    for row in table:
        norm_row = {}
        for k, v in row.items():
            if isinstance(v, str):
                norm_row[k] = utils.normalize_text(v)
            else:
                norm_row[k] = v
        normalized_table.append(norm_row)
    hide_table_row_index = """
        <style>
        thead tr th:first-child {display:none}
        tbody th {display:none}
        thead th {white-space: nowrap;}
        </style>
    """

    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)
    st.table(
        normalized_table,
    )


def main():
    st.set_page_config(page_title="Loan Assistant", layout="wide")

    st.sidebar.title("Loan Assistant")
    # Use a typed AppState container to hold session resources
    state = get_app_state()

    # Initialize heavy resources once and keep them in the typed AppState
    if not state.resources_initialized:
        llm, client = get_model()
        db_conn, _ = init_db("data/loan_assistant.db")
        rag = RAG("documents", "chroma_db")
        tools = get_tools(rag, db_conn)
        users = dal.get_users(db_conn)

        state.llm = llm
        state.client = client
        state.db_conn = db_conn
        state.rag = rag
        state.tools = tools
        state.users = users

        # Create agent instance once. Agent will be instructed to switch users
        initial_user = users[0] if users else None
        if initial_user is None:
            st.sidebar.error("No users found in the database.")
            return
        try:
            state.agent = ReActAgent(initial_user, llm, client, tools, db_conn)
        except Exception:
            # Fallback: leave agent as None
            state.agent = None

        state.current_user_id = getattr(initial_user, "user_id", None)
        state.applied_loans = (
            dal.get_user_loans(db_conn, state.current_user_id)
            if state.current_user_id
            else []
        )
        state.resources_initialized = True
        # ensure local reference to agent exists in this run (other locals were already assigned above)
        agent = state.agent
    else:
        llm = state.llm
        client = state.client
        db_conn = state.db_conn
        rag = state.rag
        tools = state.tools
        users = state.users
        agent = state.agent
    # just for type checking
    if db_conn is None or agent is None:
        st.sidebar.error("Failed to initialize resources.")
        return
    # Sidebar: user selector + natural navigation
    st.sidebar.header("User")
    user_map = (
        {f"{getattr(usr, 'email', usr.user_id)}": usr for usr in users} if users else {}
    )
    user_options = list(user_map.keys())

    if not user_options:
        st.sidebar.info("No users available in the database.")
        return

    # Build a readable label for each user showing email and credit score when available
    labels: list[str] = []
    for usr in users:
        score = getattr(usr, "credit_score", None)
        income = getattr(usr, "income", None)
        label_parts = [getattr(usr, "email", str(getattr(usr, "user_id", "user")))]
        if score is not None:
            label_parts.append(f"score {score}")
        if income is not None:
            label_parts.append(f"income ${int(income):,}")
        labels.append(" — ".join(label_parts))

    # Keep selection stable using state.current_user_id
    default_index = 0
    if state.current_user_id is not None:
        for i, usr in enumerate(users):
            if getattr(usr, "user_id", None) == state.current_user_id:
                default_index = i
                break

    choice = st.sidebar.selectbox("Switch user", options=labels, index=default_index)
    # map back to selected user object
    selected = users[labels.index(choice)]
    if selected is None:
        st.sidebar.error("Selected user not found.")
        return
    # If user changed, notify the agent and refresh applied loans from DB
    prev_id = state.current_user_id
    if selected and prev_id != selected.user_id:
        # Update agent user context if supported
        ag = state.agent
        if ag is not None:
            try:
                ag.change_user(selected)
            except Exception:
                pass
        # refresh chat history
        state.chat_history = [get_welcome_message()]
        # Refresh applied loans from DB for the new user
        try:
            state.applied_loans = dal.get_user_loans(db_conn, selected.user_id)
        except Exception:
            state.applied_loans = []

        state.current_user_id = selected.user_id

    # Natural navigation with friendly labels
    st.sidebar.markdown("---")
    page_choice = st.sidebar.radio("Go to", ["💬 Chat", "📋 Applied Loans"], index=0)
    page = "Chat" if page_choice.startswith("💬") else "Applied Loans"

    # Sidebar action buttons
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh loans"):
        try:
            state.applied_loans = dal.get_user_loans(db_conn, selected.user_id)
        except Exception:
            state.applied_loans = []
        st.rerun()

    if st.sidebar.button("🧹 Clear chat"):
        state.chat_history = [get_welcome_message()]
        agent.clear_memory()
        st.rerun()
    if page == "Chat":
        # Use the modern chat UI which reads the persistent agent from AppState
        chat_ui()
    elif page == "Applied Loans":
        # Always fetch fresh loans when viewing the page to ensure up-to-date data
        try:
            loans = dal.get_user_loans(db_conn, selected.user_id)
            state.applied_loans = loans
        except Exception:
            state.applied_loans = state.applied_loans or []

        applied_loans_page(selected, db_conn)


if __name__ == "__main__":
    main()
