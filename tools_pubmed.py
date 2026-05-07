from langchain_core.tools import tool
from Bio import Entrez
import time

# NCBI requires an email for Entrez API requests
Entrez.email = "marieechristine@gmail.com"


@tool
def search_pubmed_live(query: str) -> str:
    """Search PubMed right now for recent papers on a topic.
    Use this when the user wants to find papers, asks what's new about something,
    or says 'find me papers on X'.
    """
    # Step 1: search PubMed for matching PMIDs
    search_handle = Entrez.esearch(
        db="pubmed",
        term=query,
        retmax=5,
        sort="relevance",
    )
    search_results = Entrez.read(search_handle)
    search_handle.close()

    pmid_list = search_results["IdList"]

    # If nothing came back, say so
    if not pmid_list:
        return f"PubMed returned no results for: {query}"

    # Be polite to the API
    time.sleep(0.5)

    # Step 2: fetch the full records for those PMIDs
    fetch_handle = Entrez.efetch(
        db="pubmed",
        id=",".join(pmid_list),
        rettype="medline",
        retmode="xml",
    )
    records = Entrez.read(fetch_handle)
    fetch_handle.close()

    # Step 3: pull out the fields we care about and format them
    papers = []
    for record in records["PubmedArticle"]:
        article = record["MedlineCitation"]["Article"]

        title = str(article.get("ArticleTitle", "No title"))

        abstract_parts = article.get("Abstract", {}).get("AbstractText", [])
        abstract = " ".join(str(p) for p in abstract_parts)
        abstract_snippet = abstract[:300] if abstract else "No abstract available."

        pmid = str(record["MedlineCitation"]["PMID"])

        journal = str(article.get("Journal", {}).get("Title", "Unknown journal"))

        pub_date = article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
        year = str(pub_date.get("Year", "Unknown year"))

        author_list = article.get("AuthorList", [])
        authors = []
        for a in author_list[:3]:
            if "LastName" in a and "ForeName" in a:
                authors.append(f"{a['ForeName']} {a['LastName']}")
        authors_str = ", ".join(authors)
        if len(author_list) > 3:
            authors_str += " et al."

        papers.append(
            f"Title: {title}\n"
            f"Authors: {authors_str} | {journal}, {year} | PMID: {pmid}\n"
            f"Abstract: {abstract_snippet}..."
        )

    return "\n\n---\n\n".join(papers)
