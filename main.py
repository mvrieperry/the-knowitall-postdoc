from langgraph.graph import StateGraph, MessagesState, START
from langchain_openai import ChatOpenAI
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

from prompts import return_instructions
from tools_chroma import search_chroma_db
from tools_pubmed import search_pubmed_live
from tools_mcp import search_biorxiv_preprints
from llm_config import openai_kwargs

# Load API keys — run this app from the repo root
load_dotenv(".secrets")

# Set up the language model. Uses real OpenAI if OPENAI_API_KEY is set,
# otherwise the course API gateway via API_GATEWAY_KEY (see llm_config.py).
chat_agent = ChatOpenAI(model="gpt-4o-mini", **openai_kwargs())

# Load the Postdoc persona system prompt
instructions = return_instructions()

# Tools list — add services here as we build them
tools = [search_chroma_db, search_pubmed_live, search_biorxiv_preprints]


# This node sends the conversation to the LLM.
# The system prompt goes in front so the Postdoc persona is always active.
def call_model(state: MessagesState):
    response = chat_agent.bind_tools(tools).invoke(
        [SystemMessage(content=instructions)] + state["messages"]
    )
    return {"messages": [response]}


# Build and return the LangGraph graph.
# Right now: START → call_model → END (no tools yet).
# When we add tools, tools_condition will route between call_model and ToolNode.
def get_graph():
    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    graph = builder.compile()
    return graph
