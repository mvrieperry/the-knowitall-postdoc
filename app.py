import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os

from assignment_chat.main import get_graph

# Load API keys — run this from the 05_src/ directory
load_dotenv(".secrets")

# Build the LangGraph graph (Postdoc persona, no tools yet)
postdoc = get_graph()

# Blocked topics — simple keyword check that fires before calling the LLM at all.
# Maps a keyword (checked as substring of lowercased message) to an in-character refusal.
# Note: this is intentionally simple. The system prompt is the main guardrail;
# this just saves an API call for obvious cases.
blocked_keywords = {
    "cat":        "I'm a computational biologist, not a vet. Try somewhere else.",
    "dog":        "I'm a computational biologist, not a vet. Try somewhere else.",
    "horoscope":  "I deal in p-values, not planets. Hard pass.",
    "zodiac":     "I deal in p-values, not planets. Hard pass.",
    "taylor swift": "Not in my PubMed search history. Moving on.",
}


def chat(message: str, history: list[dict]) -> str:
    # Check for blocked topics before hitting the LLM
    msg_lower = message.lower()
    for keyword, refusal in blocked_keywords.items():
        if keyword in msg_lower:
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

    # The last message in the response is the model's reply
    return response["messages"][-1].content


# Launch the Gradio chat interface
gr.ChatInterface(
    fn=chat,
    type="messages",
    title="The Postdoc",
    description="A senior postdoc who has read everything in the AI/drug discovery literature. Ask about papers, methods, or what the field knows on a topic.",
).launch()
