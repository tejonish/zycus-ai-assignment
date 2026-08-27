from src.retrieval.retriever import KBRetriever


def test_retriever_returns_results():
    retriever = KBRetriever()

    results = retriever.search("How do I enable SSO?", top_k=3)

    assert len(results) == 3
    assert all("source" in result for result in results)
    assert all("section" in result for result in results)
    assert all("score" in result for result in results)


def test_sso_retrieval():
    retriever = KBRetriever()

    results = retriever.search("How do I enable SSO?", top_k=3)

    assert any(
        "authentication-sso.md" in result["source"]
        for result in results
    )


def test_billing_retrieval():
    retriever = KBRetriever()

    results = retriever.search(
        "How much does the Business plan cost?",
        top_k=3,
    )

    assert any(
        "billing-and-plans.md" in result["source"]
        for result in results
    )