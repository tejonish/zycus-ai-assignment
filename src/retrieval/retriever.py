from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from chunker import load_kb_documents


BILLING_KEYWORDS = {
    "price",
    "pricing",
    "cost",
    "billing",
    "invoice",
    "invoices",
    "plan",
    "plans",
    "seat",
    "seats",
    "subscription",
    "upgrade",
    "downgrade",
    "cancel",
    "cancellation",
}


TROUBLESHOOTING_KEYWORDS = {
    "error",
    "fail",
    "failed",
    "failing",
    "failure",
    "stuck",
    "unable",
    "cannot",
    "can't",
    "issue",
    "problem",
    "broken",
    "timeout",
    "blocked",
    "not working",
    "not reaching",
    "missing",
}


PRODUCT_ALIASES = {
    "databridge pro": {
        "databridge pro",
        "databridge",
    },
    "cloudsync": {
        "cloudsync",
    },
    "analyticshub": {
        "analyticshub",
        "analytics hub",
    },
    "securevault": {
        "securevault",
        "secure vault",
    },
    "workflowengine": {
        "workflowengine",
        "workflow engine",
    },
}


IMPORTANT_TERMS = {
    "sso",
    "snowflake",
    "webhook",
    "authentication",
    "ingestion",
    "pipeline",
    "schema",
    "connector",
    "integration",
    "approval",
    "workflow",
    "data source",
    "data sources",
    "batch import",
    "bulk",
}


class KBRetriever:

    def __init__(self):
        self.documents = load_kb_documents()

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )

        self.document_vectors = self.vectorizer.fit_transform(
            [
                f"{doc['source']} "
                f"{doc['section']} "
                f"{doc['text']}"
                for doc in self.documents
            ]
        )

    @staticmethod
    def normalise(text):
        return text.lower().strip()

    @staticmethod
    def get_source_product(source):
        """
        Convert:

            products\\databridge-pro.md

        into:

            databridge pro
        """

        source = source.lower()

        if not source.startswith("products\\"):
            return ""

        filename = source.split("\\")[-1]

        filename = filename.replace(
            ".md",
            "",
        )

        filename = filename.replace(
            "-",
            " ",
        )

        return filename

    @staticmethod
    def detect_product(text):
        """
        Detect a known product name from text.
        """

        text = text.lower()

        for product, aliases in PRODUCT_ALIASES.items():

            for alias in aliases:

                if alias in text:
                    return product

        return None

    @staticmethod
    def build_ticket_query(ticket):
        """
        Build a retrieval query using the important
        ticket fields.
        """

        return (
            f"Product: {ticket.get('product', '')}. "
            f"Product area: {ticket.get('product_area', '')}. "
            f"Category: {ticket.get('category', '')}. "
            f"Urgency: {ticket.get('urgency', '')}. "
            f"Subject: {ticket.get('subject', '')}. "
            f"Body: {ticket.get('body', '')}"
        )

    def product_matches(
        self,
        document,
        product,
    ):
        """
        Check whether a KB document belongs to
        the requested product.
        """

        if not product:
            return False

        source_product = self.get_source_product(
            document["source"]
        )

        aliases = PRODUCT_ALIASES.get(
            product.lower(),
            {product.lower()},
        )

        for alias in aliases:

            alias = alias.replace(
                "-",
                " ",
            )

            if alias == source_product:
                return True

        return False

    def search(
        self,
        query,
        top_k=3,
        product=None,
        product_area=None,
    ):

        query = query.strip()

        query_vector = self.vectorizer.transform(
            [query]
        )

        base_scores = cosine_similarity(
            query_vector,
            self.document_vectors,
        )[0]

        adjusted_scores = base_scores.copy()

        query_lower = query.lower()

        # Detect product automatically if caller didn't provide it.
        detected_product = product

        if not detected_product:
            detected_product = self.detect_product(
                query_lower
            )

        # Detect whether this looks like a support /
        # troubleshooting question.
        is_troubleshooting = any(
            keyword in query_lower
            for keyword in TROUBLESHOOTING_KEYWORDS
        )

        # Detect billing intent.
        query_words = set(
            query_lower.split()
        )

        is_billing = bool(
            query_words & BILLING_KEYWORDS
        )

        for index, document in enumerate(
            self.documents
        ):

            source = document["source"].lower()
            section = document["section"].lower()
            text = document["text"].lower()

            # ==================================================
            # 1. PRODUCT BOOST
            # ==================================================

            if detected_product:

                if self.product_matches(
                    document,
                    detected_product,
                ):

                    adjusted_scores[index] += 0.12

                elif source.startswith(
                    "products\\"
                ):

                    # Penalize a different product.
                    adjusted_scores[index] -= 0.15

            # ==================================================
            # 2. PRODUCT AREA BOOST
            # ==================================================

            if product_area:

                area_words = [
                    word.lower()
                    for word in product_area.split()
                    if len(word) > 2
                ]

                area_matches = 0

                for word in area_words:

                    if (
                        word in section
                        or word in text
                    ):
                        area_matches += 1

                if area_matches:

                    adjusted_scores[index] += min(
                        0.12,
                        area_matches * 0.04,
                    )

            # ==================================================
            # 3. TROUBLESHOOTING BOOST
            # ==================================================

            if is_troubleshooting:

                troubleshooting_sections = {
                    "troubleshooting",
                    "error reference",
                    "common support scenarios",
                    "common issues",
                }

                if any(
                    term in section
                    for term in troubleshooting_sections
                ):

                    adjusted_scores[index] += 0.10

                # Product-specific support documentation
                # is especially useful.
                if (
                    "common support scenarios"
                    in text
                ):

                    adjusted_scores[index] += 0.08

            # ==================================================
            # 4. IMPORTANT TERM BOOST
            # ==================================================

            for term in IMPORTANT_TERMS:

                if term not in query_lower:
                    continue

                # Exact section match is strong evidence.
                if term in section:

                    adjusted_scores[index] += 0.10

                # Match in document body.
                elif term in text:

                    adjusted_scores[index] += 0.04

            # ==================================================
            # 5. BILLING BOOST
            # ==================================================

            if is_billing:

                if source.startswith(
                    "billing\\"
                ):

                    adjusted_scores[index] += 0.10

                if "pricing" in section:

                    adjusted_scores[index] += 0.05

            # ==================================================
            # 6. DON'T RETURN PRICING FOR BUGS / ISSUES
            # ==================================================

            if is_troubleshooting:

                if (
                    "pricing & limits"
                    in section
                ):

                    adjusted_scores[index] -= 0.10

            # ==================================================
            # 7. STRONG SIGNAL FOR ERROR-SPECIFIC SECTIONS
            # ==================================================

            error_terms = [
                "err_",
                "invalid_",
                "checksum",
                "schema_mismatch",
                "connection",
                "authentication",
                "webhook",
            ]

            for term in error_terms:

                if term in query_lower:

                    if term in section:

                        adjusted_scores[index] += 0.08

                    elif term in text:

                        adjusted_scores[index] += 0.04

        # ======================================================
        # SORT RESULTS
        # ======================================================

        ranked_indices = adjusted_scores.argsort()[::-1]

        results = []

        for index in ranked_indices:

            results.append(
                {
                    "source": self.documents[index][
                        "source"
                    ],
                    "section": self.documents[index][
                        "section"
                    ],
                    "text": self.documents[index][
                        "text"
                    ],
                    "score": float(
                        adjusted_scores[index]
                    ),
                }
            )

            if len(results) >= top_k:
                break

        return results


if __name__ == "__main__":

    retriever = KBRetriever()

    queries = [
        "How do I enable SSO?",
        "Users are unable to sync files",
        "How much does the Business plan cost?",
        "WorkflowEngine approval is stuck",
        "DataBridge Pro ingestion is failing",
        "CloudSync webhook is not reaching Snowflake",
    ]

    for query in queries:

        print("=" * 70)
        print("QUERY:", query)
        print("=" * 70)

        results = retriever.search(
            query,
            top_k=3,
        )

        for i, result in enumerate(
            results,
            start=1,
        ):

            print(
                f"{i}. "
                f"{result['source']} | "
                f"{result['section']} | "
                f"score={result['score']:.4f}"
            )

        print()