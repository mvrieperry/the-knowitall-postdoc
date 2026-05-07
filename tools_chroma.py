from langchain_core.tools import tool
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(".secrets")

# Connect to the existing persistent ChromaDB collection.
# Run from the 05_src/ directory — that's where the relative path resolves from.
chroma_client = chromadb.PersistentClient(path="assignment_chat/data/chroma_db")

# Load the collection with no embedding function — the embeddings are already stored.
# We'll embed queries manually and pass them in directly.
collection = chroma_client.get_collection(name="pubmed_ai_drug_discovery")

# OpenAI client via the course gateway — used to embed the user's query
openai_client = OpenAI(
    api_key="any_value",
    base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
    default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY")},
)


@tool
def search_chroma_db(query: str) -> str:
    """Search the local collection of ~1000 AI/drug discovery abstracts using semantic similarity.
    Use this when the user asks what the literature says about a topic, or wants background on something.
    """
    # Embed the query manually using the same model the collection was built with
    query_embedding = openai_client.embeddings.create(
        input=[query],
        model="text-embedding-3-small",
    ).data[0].embedding

    # Fetch the 3 most similar abstracts by passing the embedding directly
    results = collection.query(query_embeddings=[query_embedding], n_results=3)

    # Pull out the parallel lists of metadata and documents
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    # Format each result — the model will turn this into natural prose
    formatted = []
    for meta, doc in zip(metadatas, documents):
        title   = meta.get("title", "Unknown title")
        authors = meta.get("authors", "Unknown authors")
        year    = meta.get("year", "Unknown year")
        journal = meta.get("journal", "Unknown journal")
        pmid    = meta.get("pmid", "")

        # Trim the document text (title + abstract) to just the abstract portion
        # Documents were stored as "Title. Abstract" so we skip past the first sentence
        abstract_snippet = doc[len(title):].strip(". ").strip()[:400]

        formatted.append(
            f"Title: {title}\n"
            f"Authors: {authors} | {journal}, {year} | PMID: {pmid}\n"
            f"Abstract: {abstract_snippet}..."
        )

    return "\n\n---\n\n".join(formatted)
