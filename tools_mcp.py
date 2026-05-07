from langchain_core.tools import tool
import requests


@tool
def search_biorxiv_preprints(query: str) -> str:
    """Search bioRxiv and medRxiv for the very latest preprints on a topic.
    Use this when the user wants cutting-edge or bleeding-edge work,
    asks about preprints, or wants results too recent to be in the local collection.
    """
    # Europe PMC has free keyword search across preprint servers (bioRxiv, medRxiv, etc.)
    # SRC:PPR filters to preprints only. No API key needed.
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": f"({query}) AND (SRC:PPR)",
        "resultType": "lite",
        "format": "json",
        "pageSize": 5,
        "sort": "P_PDATE_D desc",  # newest first
    }

    response = requests.get(url, params=params)
    data = response.json()

    papers = []
    for item in data.get("resultList", {}).get("result", []):
        title   = item.get("title", "No title")
        authors = item.get("authorString", "Unknown authors")[:100]
        year    = item.get("pubYear", "Unknown year")
        source  = item.get("source", "preprint server")
        doi     = item.get("doi", "no DOI")

        abstract_raw = item.get("abstractText", "")
        abstract = abstract_raw[:300] if abstract_raw else "No abstract available."

        papers.append(
            f"Title: {title}\n"
            f"Authors: {authors}\n"
            f"Year: {year} | Source: {source} | DOI: {doi}\n"
            f"Abstract: {abstract}..."
        )

    if not papers:
        return f"No preprints found for: {query}"

    return "\n\n---\n\n".join(papers)
