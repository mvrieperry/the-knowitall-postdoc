import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from dotenv import load_dotenv
import re

from main import get_graph

# Load API keys — run this from the 05_src/ directory
load_dotenv(".secrets")

# Build the LangGraph graph (Postdoc persona, no tools yet)
postdoc = get_graph()

# Blocked topics — keyword check that fires before calling the LLM at all.
# Matched as whole words (so "cat" won't trip on "publiCATions"). The system
# prompt is the main guardrail; this just saves an API call for obvious cases.
blocked_keywords = {
    "cat":        "I'm a computational biologist, not a vet. Try somewhere else.",
    "dog":        "I'm a computational biologist, not a vet. Try somewhere else.",
    "horoscope":  "I deal in p-values, not planets. Hard pass.",
    "zodiac":     "I deal in p-values, not planets. Hard pass.",
    "taylor swift": "Not in my PubMed search history. Moving on.",
}

# Friendly labels for the tool note shown above each answer in the browser.
tool_labels = {
    "search_pubmed_live":       "Live PubMed search",
    "search_chroma_db":         "Semantic search (local embeddings)",
    "search_biorxiv_preprints": "Preprint search (bioRxiv/medRxiv)",
}


def chat(message: str, history: list[dict]) -> str:
    # Check for blocked topics before hitting the LLM (whole-word match)
    msg_lower = message.lower()
    for keyword, refusal in blocked_keywords.items():
        if re.search(rf"\b{re.escape(keyword)}\b", msg_lower):
            return refusal

    # Convert Gradio's history format (list of dicts) into LangChain messages
    langchain_messages = []
    for msg in history:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))

    # Add the new user message
    langchain_messages.append(HumanMessage(content=message))

    # Run the graph — the LLM (and eventually tools) will handle the rest
    state = {"messages": langchain_messages}
    response = postdoc.invoke(state)

    answer = response["messages"][-1].content

    # Note which tool(s) the model called, in order, above the answer.
    tools_used = [m.name for m in response["messages"] if isinstance(m, ToolMessage)]
    if tools_used:
        labels = [tool_labels.get(name, name) for name in tools_used]
        answer = f"*Tool used: {', '.join(labels)}*\n\n{answer}"

    return answer


# Launch the Gradio chat interface
gr.ChatInterface(
    fn=chat,
    title="The Postdoc",
    description="A senior postdoc who has read everything in the AI/drug discovery literature. Ask about papers, methods, or what the field knows on a topic.",
).launch()
