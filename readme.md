# The Postdoc — Assignment 2

## What this is

This is a conversational AI chatbot that plays the role of a slightly burnt-out, wry senior postdoc who has read everything in the AI and drug discovery literature. You ask it research questions, it digs through the literature and tells you what it found — with dry humor and minimal enthusiasm. It's helpful. It just doesn't perform excitement about it.

The chatbot has three services it can call depending on your question, and it decides which one to use on its own.

---

## The three services

### Service 1 — Live PubMed Search (`tools_pubmed.py`)

Uses the NCBI Entrez API via Biopython to search PubMed in real time based on your question. Returns the top 5 results, summarized in natural prose. Good for "find me papers on X" or "what's been published recently on Y."

I used the same Biopython Entrez pattern from the abstract-fetching script I wrote earlier during my time working as a technical lead at my job and could adapt it to this course (`fetch_abstracts_script.ipynb`). The API is free and doesn't require a key — just an email address registered with NCBI.

### Service 2 — Semantic Search (`tools_chroma.py`)

Loads a persistent ChromaDB collection of ~1000 PubMed abstracts on AI/ML in drug discovery that I pre-embedded earlier. When you ask a conceptual question ("what does the literature say about X"), it embeds your question using `text-embedding-3-small` via the course API gateway and returns the 3 most semantically similar abstracts from the collection.

The collection was built separately using `fetch_abstracts_script.ipynb` (which fetched the abstracts) and a separate embedding script (which embedded them with `text-embedding-3-small` and stored them in `data/chroma_db/`). The app just loads the existing collection — it doesn't re-embed anything at runtime.

I embed the query manually and pass it directly to `collection.query(query_embeddings=[...])` because the collection was built with pre-computed embeddings, not an attached embedding function.

### Service 3 — Preprint Search (`tools_mcp.py`)

Uses the Europe PMC REST API to search bioRxiv and medRxiv for the most recent preprints on a topic. Good for "what's the bleeding-edge work on X" or anything too new to be indexed in the local collection.

I used Europe PMC instead of the bioRxiv REST API directly because the bioRxiv public API only supports date-range browsing — it has no keyword search. Europe PMC indexes bioRxiv, medRxiv, and other preprint servers, and has a proper free search endpoint with no authentication required. This service uses function calling (the LLM decides to invoke it as a tool) which satisfies the assignment's Service 3 requirement.

---

## Guardrails

Two layers:

1. **Keyword check in `app.py`** — fires before the LLM is called at all. If the message contains a blocked keyword (`cat`, `dog`, `horoscope`, `zodiac`, `taylor swift`), it returns an in-character refusal immediately without making an API call.

2. **System prompt in `prompts.py`** — instructs the model to refuse restricted topics and never reveal or modify the system prompt. Refusals are written in the Postdoc's voice.

---

## Architecture

Built on LangGraph (`StateGraph` + `ToolNode`), matching the `course_chat` reference implementation. The flow is:

```
Gradio ChatInterface
    → converts history to LangChain messages
    → LangGraph graph
        → call_model node (LLM with 3 bound tools)
        → tools_condition (routes to ToolNode or END)
        → ToolNode (executes whichever tool the LLM chose)
        → back to call_model for final response
    → returns last message content to Gradio
```

The LLM decides which service to call based on the user's message. It can also combine services if appropriate.

---

## Embedding process

1. Fetched 1000 PubMed abstracts using `Bio.Entrez.esearch` + `Entrez.efetch` (see `fetch_abstracts_script.ipynb`).
2. Stored as JSON in `data/pubmed_ai_drug_discovery.json` with fields: `pmid`, `title`, `abstract`, `authors`, `journal`, `year`.
3. Embedded each abstract using `text-embedding-3-small` via the course API gateway.
4. Stored in a persistent ChromaDB collection at `data/chroma_db/`, collection name `pubmed_ai_drug_discovery`.

The app loads the existing collection at startup — no re-embedding happens at runtime.

---

## How to run

From `05_src/`:

```bash
uv run python -m assignment_chat.app
```

Requires `05_src/.secrets` with `API_GATEWAY_KEY` set.
