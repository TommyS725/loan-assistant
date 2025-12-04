# imports
import sqlite3

from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models.moderations import Guardian
from IPython.display import Image, display
from langchain_ibm import ChatWatsonx
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_core.messages import (
    AnyMessage,
    SystemMessage,
    HumanMessage,
    ToolMessage,
    AIMessage,
    filter_messages,
)
from langchain_experimental.tools.python.tool import PythonREPLTool
from sqlalchemy import create_engine
from typing_extensions import TypedDict
from typing import Annotated
import dal
from prompt import generate_base_prompt, generate_eligibility_prompt
from model import (
    User,
    BaseAgentOutputSchema,
    EligibilityAgentOutputSchema,
)
from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from langchain.tools import BaseTool
from langchain_core.messages.utils import trim_messages, count_tokens_approximately


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    moderation_verdict: Annotated[
        str, "Result of content moderation: 'inappropriate' or 'safe'"
    ]
    loan_to_apply: Annotated[
        int | None, "The loan id the user wants to apply for, if any"
    ]


def message_trimmer(
    messages: list[AnyMessage], max_tokens: int = 1024
) -> list[AnyMessage]:
    """
    Trim messages to fit within max_tokens limit.
    """
    return trim_messages(
        messages,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=max_tokens,
        start_on="human",
        end_on=("human", "tool"),
    )


class ReActAgent:
    def __init__(
        self,
        user: User,
        llm: ChatWatsonx,
        client: APIClient,
        tools: list[BaseTool],
        conn: sqlite3.Connection,
    ):
        memory = MemorySaver()
        graph = StateGraph(AgentState)
        graph.add_node("guardian", self.guardian_moderation)
        graph.add_node("base_advisor", self.call_base_advisor)
        graph.add_node("eligibility_agent", self.call_eligibility_agent)
        # share same tools, but separate nodes for clarity
        graph.add_node("base_agent_tools", self.call_tools)
        graph.add_node("eligibility_agent_tools", self.call_tools)
        graph.add_node("block_message", self.block_message)
        graph.add_edge("base_advisor", END)
        graph.add_edge("eligibility_agent", END)
        graph.add_edge("block_message", END)
        graph.add_conditional_edges(
            "guardian",
            lambda state: state["moderation_verdict"],
            {"inappropriate": "block_message", "safe": "base_advisor"},
        )
        graph.add_conditional_edges(
            "base_advisor",
            self.should_call_base_advisor_tools,
            ["base_agent_tools", END],
        )
        graph.add_edge("base_agent_tools", "base_advisor")
        graph.add_conditional_edges(
            "eligibility_agent",
            self.should_call_eligibility_agent_tools,
            ["eligibility_agent_tools", END],
        )
        graph.add_edge("eligibility_agent_tools", "eligibility_agent")

        graph.add_conditional_edges(
            "base_advisor", self.should_apply_loan, ["eligibility_agent", END]
        )
        graph.add_edge(START, "guardian")
        self.memory = memory
        self.user = user
        self.graph = graph.compile(checkpointer=memory)
        self.tools = {t.name: t for t in tools}
        self.llm = llm.bind_tools(tools)
        self.client = client
        self.db_conn = conn

    def thread_id(self):
        return str(self.user.user_id)

    def invoke(self, user_input: str):
        """
        Wrap a user input and call the compiled graph while supplying the thread_id
        so MemorySaver stores/retrieves the conversation.
        """
        messages = [HumanMessage(content=user_input)]
        # LangGraph expects state dict and a config; put thread id under configurable
        config = {"configurable": {"thread_id": self.thread_id()}}
        result = self.graph.invoke({"messages": messages}, config)  # type: ignore
        return result

    def clear_memory(self):
        self.memory.delete_thread(self.thread_id())

    def change_user(self, user: User):
        self.user = user
        self.clear_memory()

    def call_base_advisor(self, state: AgentState):
        print("===== Calling Base Advisor Agent =====")
        messages = state["messages"]
        prompt = generate_base_prompt(self.user, messages)
        est = count_tokens_approximately(prompt)
        print(f"Base Advisor prompt tokens: {est}")

        output = self.llm.invoke(prompt)
        # Check for tool calls
        if hasattr(output, "tool_calls") and output.tool_calls:
            # The agent wants to use tools - return the AI message with tool calls
            return {"messages": [output], "loan_to_apply": None}
        try:
            parsed = BaseAgentOutputSchema.model_validate_json(output.content)  # type: ignore
            if parsed.loan_id_to_apply is not None:
                return {"loan_to_apply": parsed.loan_id_to_apply}
            return {
                "loan_to_apply": None,
                "messages": [AIMessage(content=parsed.response)],
            }
        except Exception as e:
            print(
                "Error parsing LLM output:",
                output.content if output.content else output,
            )
            return {
                "loan_to_apply": None,
                "messages": [AIMessage(content=output.content)],
            }

    def call_eligibility_agent(self, state: AgentState):
        print("===== Calling Eligibility Agent =====")
        loan_id = state["loan_to_apply"]
        if loan_id is None:
            return {"messages": [AIMessage(content="No loan application detected.")]}
        # query loan details from database later, now just create a dummy loan
        loan = dal.get_specific_loan(self.db_conn, loan_id)
        if loan is None:
            return {"messages": [AIMessage(content="Loan not found.")]}
        user_loans = dal.get_user_loans(self.db_conn, self.user.user_id)
        prompt = generate_eligibility_prompt(self.user, loan, user_loans)
        output = self.llm.invoke(prompt)
        if hasattr(output, "tool_calls") and output.tool_calls:
            # The agent wants to use tools - return the AI message with tool calls
            return {"messages": [output], "loan_to_apply": loan_id}
        try:
            parsed = EligibilityAgentOutputSchema.model_validate_json(output.content)  # type: ignore
            if parsed.application_eligible:
                application_record = parsed.assessment_record
                dal.add_user_loan_record(
                    self.db_conn,
                    self.user.user_id,
                    loan.loan_id,
                    application_record,
                )
                print("Added loan application record to database.")
            else:
                print("Application not eligible; no record added.")
            return {
                "loan_to_apply": None,
                "messages": [AIMessage(content=parsed.user_message)],
            }
        except Exception as e:
            print(
                "Error parsing LLM output:",
                output.content if output.content else output,
            )
            return {
                "loan_to_apply": None,
                "messages": [AIMessage(content=output.content)],
            }

    def call_tools(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls  # type: ignore
        print("Tool calls:", len(tool_calls))
        results = []
        for t in tool_calls:
            print("Invoking tool:", t["name"], "with args:", t["args"])
            try:
                result = self.tools[t["name"]].invoke(t["args"])
                results.append(
                    ToolMessage(
                        tool_call_id=t["id"], name=t["name"], content=str(result)
                    )
                )
            except Exception as e:
                print(f"Error invoking tool {t['name']}: {e}")
                results.append(
                    ToolMessage(
                        tool_call_id=t["id"],
                        name=t["name"],
                        content=f"Error invoking tool: {e}",
                    )
                )
        return {
            "messages": results,
            "loan_to_apply": state["loan_to_apply"],
        }  # preserve loan_to_apply

    def should_call_base_advisor_tools(self, state: AgentState):
        result = state["messages"][-1]
        return "base_agent_tools" if hasattr(result, "tool_calls") and len(result.tool_calls) > 0 else END  # type: ignore

    def should_call_eligibility_agent_tools(self, state: AgentState):
        result = state["messages"][-1]
        return "eligibility_agent_tools" if hasattr(result, "tool_calls") and len(result.tool_calls) > 0 else END  # type: ignore

    def should_apply_loan(self, state: AgentState):
        loan_id = state["loan_to_apply"]
        return "eligibility_agent" if loan_id is not None else END

    def guardian_moderation(self, state: AgentState):
        message = state["messages"][-1]
        detectors = {
            "hap": {},
            "granite_guardian": {"risk_name": "harm", "threshold": 0.6},
            "topic_relevance": {"threshold": 0.5},
            "pii": {},
        }
        guardian = Guardian(api_client=self.client, detectors=detectors)
        response = guardian.detect(text=message.content, detectors=detectors)  # type: ignore
        if (
            len(response["detections"]) != 0
            and response["detections"][0]["detection"] == "Yes"
        ):
            return {"moderation_verdict": "inappropriate"}
        else:
            return {"moderation_verdict": "safe"}

    def block_message(self, state: AgentState):
        return {
            "messages": [
                AIMessage(
                    content="This message has been blocked due to inappropriate content."
                )
            ]
        }
