if __name__ == "__main__":
    from IPython.display import Image
    from llm import get_model
    from rag import RAG
    from db import init_db
    from tools import get_tools
    from agent import ReActAgent
    import dal

    conn, _ = init_db("data/loan_assistant.db")
    rag = RAG("documents", "chroma_db")
    llm, client = get_model()
    tools = get_tools(rag, conn)
    user = dal.get_user_by_id(conn, 1)
    if not user:
        raise ValueError("User with ID 1 not found.")
    agent = ReActAgent(user, llm, client, tools, conn)
    agent.graph.get_graph().draw_mermaid_png(
        background_color="transparent",
        output_file_path="agent_graph.png",
    )
