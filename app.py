import sys
from pathlib import Path

import streamlit as st



# PATHS / IMPORTS


PROJECT_ROOT = Path(__file__).resolve().parent

sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "retrieval"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "triage"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "summarizer"))

from retriever import KBRetriever
from triage import triage_ticket
from summarizer import build_account_health
from llm.llm_client import LLMClient

llm_client = LLMClient()



# PAGE CONFIG


st.set_page_config(
    page_title="Zycus AI Support",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)



# CUSTOM CSS


st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 1rem 0 1.5rem 0;
    }

    .hero h1 {
        font-size: 2.7rem;
        margin-bottom: 0.3rem;
    }

    .hero p {
        font-size: 1.05rem;
        opacity: 0.75;
    }

    .section-title {
        font-size: 1.45rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }

    .result-card {
        padding: 1.2rem;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        margin-bottom: 1rem;
    }

    .source-label {
        font-size: 0.85rem;
        opacity: 0.65;
    }

    .source-name {
        font-weight: 600;
        font-size: 1rem;
    }

    .small-muted {
        font-size: 0.85rem;
        opacity: 0.65;
    }

    </style>
    """,
    unsafe_allow_html=True,
)



# LOAD RETRIEVER


@st.cache_resource
def get_retriever():
    return KBRetriever()


retriever = get_retriever()



# SIDEBAR


with st.sidebar:

    st.title("Navigation")

    st.caption("Choose a workflow")

    page = st.radio(
        "Choose a workflow",
        [
            "🎫 Ticket Triage",
            "🏢 Account Health",
            "🔎 Knowledge Base Search",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.subheader("System")

    st.success("Local retrieval")

    st.success("Deterministic classification")

    st.success("KB-grounded responses")

    if llm_client.enabled:
        st.success(f"Local LLM enabled — Ollama ({llm_client.model})")
    else:
        st.warning("Local LLM unavailable — using deterministic fallback")



# HELPER FUNCTIONS


def render_metric_card(label, value):
    st.metric(label, value)


def get_result_text(result):
    """
    Safely extract useful text from different possible
    retriever result structures.
    """

    for key in [
        "text",
        "content",
        "chunk",
        "document",
        "passage",
    ]:
        value = result.get(key)

        if value:
            return str(value)

    return ""



# TICKET TRIAGE


if page == "🎫 Ticket Triage":

    st.markdown(
        """
        <div class="hero">
            <h1>🎫 AI Support Ticket Triage</h1>
            <p>
                Enter a support ticket and the system will classify it,
                assign urgency, retrieve relevant knowledge-base content,
                and generate a grounded draft response.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # --------------------------------------------------------
    # INPUTS
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        ticket_id = st.text_input(
            "Ticket ID",
            placeholder="e.g. TKT-1001",
        )

    with col2:
        product = st.text_input(
            "Product",
            placeholder="Optional",
        )

    col1, col2 = st.columns(2)

    with col1:
        subject = st.text_input(
            "Subject",
            placeholder="e.g. Users are unable to sync files",
        )

    with col2:
        product_area = st.text_input(
            "Product Area",
            placeholder="Optional",
        )

    description = st.text_area(
        "Ticket Description",
        placeholder="Describe the customer's issue here...",
        height=180,
    )

    run_triage = st.button(
        "Run Ticket Triage",
        type="primary",
        use_container_width=True,
    )

    # --------------------------------------------------------
    # RUN TRIAGE
    # --------------------------------------------------------

    if run_triage:

        if not subject.strip() and not description.strip():
            st.warning(
                "Please enter a subject or ticket description."
            )

        else:

            ticket = {
                "ticket_id": ticket_id.strip() or None,
                "product": product.strip(),
                "product_area": product_area.strip(),
                "subject": subject.strip(),
                "body": description.strip(),
            }

            try:

                with st.spinner("Analyzing ticket..."):

                    result = triage_ticket(
                        ticket,
                        retriever,
                    )

                st.success("Ticket triage completed.")

                st.divider()

                # ------------------------------------------------
                # TRIAGE OVERVIEW
                # ------------------------------------------------

                st.markdown(
                    '<div class="section-title">Triage Overview</div>',
                    unsafe_allow_html=True,
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Category",
                        result.get(
                            "category",
                            "Unknown",
                        ),
                    )

                with col2:
                    st.metric(
                        "Urgency",
                        result.get(
                            "urgency",
                            "Unknown",
                        ),
                    )

                with col3:
                    st.metric(
                        "Confidence",
                        f'{result.get("confidence", 0):.0%}',
                    )

                with col4:
                    st.metric(
                        "KB Sources",
                        len(
                            result.get(
                                "kb_sources",
                                [],
                            )
                        ),
                    )

                # ------------------------------------------------
                # SUMMARY
                # ------------------------------------------------

                st.subheader("📝 Summary")

                st.write(
                    result.get(
                        "summary",
                        "No summary available.",
                    )
                )

                # ------------------------------------------------
                # DRAFT REPLY
                # ------------------------------------------------

                st.subheader("💬 Draft Reply")

                st.info(
                    result.get(
                        "draft_reply",
                        "No draft reply available.",
                    )
                )

                # ------------------------------------------------
                # KB SOURCES
                # ------------------------------------------------

                st.subheader("📚 Knowledge Base Sources")

                sources = result.get(
                    "kb_sources",
                    [],
                )

                if sources:

                    for source in sources:
                        st.markdown(
                            f"- `{source}`"
                        )

                else:
                    st.caption(
                        "No knowledge-base sources found."
                    )

            except Exception as exc:

                st.error(
                    "Unable to complete ticket triage."
                )

                st.caption(
                    f"Details: {exc}"
                )



# ACCOUNT HEALTH


elif page == "🏢 Account Health":

    st.markdown(
        """
        <div class="hero">
            <h1>🏢 Account Health</h1>
            <p>
                Look up an account and generate an executive health
                summary using account information and recent support history.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    account_id = st.text_input(
        "Account ID",
        placeholder="e.g. ACC-3336",
    )

    analyze_account = st.button(
        "Analyze Account Health",
        type="primary",
        use_container_width=True,
    )

    if analyze_account:

        if not account_id.strip():

            st.warning(
                "Please enter an account ID."
            )

        else:

            try:

                with st.spinner(
                    "Analyzing account health..."
                ):

                    result = build_account_health(
                        account_id.strip()
                    )

                st.success(
                    "Account health analysis completed."
                )

                st.divider()

                summary = result.get(
                    "account_summary",
                    {},
                )

                # ------------------------------------------------
                # ACCOUNT OVERVIEW
                # ------------------------------------------------

                st.markdown(
                    '<div class="section-title">Account Overview</div>',
                    unsafe_allow_html=True,
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Company",
                        summary.get(
                            "company",
                            "Unknown",
                        ),
                    )

                with col2:
                    st.metric(
                        "Health Status",
                        summary.get(
                            "health_status",
                            "Unknown",
                        ),
                    )

                with col3:
                    st.metric(
                        "Usage Trend",
                        summary.get(
                            "usage_trend",
                            "Unknown",
                        ),
                    )

                st.metric(
                    "Recent Tickets",
                    result.get(
                        "recent_ticket_count",
                        0,
                    ),
                )

                # ------------------------------------------------
                # EXECUTIVE SUMMARY
                # ------------------------------------------------

                st.subheader(
                    "📊 Executive Summary"
                )

                st.write(
                    result.get(
                        "executive_summary",
                        "No executive summary available.",
                    )
                )

                # ------------------------------------------------
                # OPEN RISKS
                # ------------------------------------------------

                st.subheader(
                    "⚠️ Open Risks"
                )

                risks = result.get(
                    "open_risks",
                    {},
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Open Tickets",
                        risks.get(
                            "open_ticket_count",
                            0,
                        ),
                    )

                with col2:
                    st.metric(
                        "High Priority",
                        risks.get(
                            "high_priority_ticket_count",
                            0,
                        ),
                    )

                with col3:
                    st.metric(
                        "Recent Open",
                        risks.get(
                            "recent_open_ticket_count",
                            0,
                        ),
                    )

                # ------------------------------------------------
                # CHURN FLAGS
                # ------------------------------------------------

                churn_flags = risks.get(
                    "churn_flags",
                    [],
                )

                if churn_flags:

                    st.markdown(
                        f"### 🔴 Churn Flags ({len(churn_flags)})"
                    )

                    for flag in churn_flags:
                        st.warning(flag)

                else:

                    st.success(
                        "No churn flags detected."
                    )

                # ------------------------------------------------
                # ESCALATION FLAGS
                # ------------------------------------------------

                escalation_flags = risks.get(
                    "escalation_flags",
                    [],
                )

                if escalation_flags:

                    st.markdown(
                        f"### 🟠 Escalation Flags "
                        f"({len(escalation_flags)})"
                    )

                    for flag in escalation_flags:
                        st.warning(flag)

                else:

                    st.success(
                        "No escalation flags detected."
                    )

                # ------------------------------------------------
                # TAM TALKING POINTS
                # ------------------------------------------------

                st.subheader(
                    "🗣️ TAM Talking Points"
                )

                talking_points = result.get(
                    "tam_talking_points",
                    [],
                )

                if talking_points:

                    for point in talking_points:
                        st.markdown(
                            f"- {point}"
                        )

                else:

                    st.caption(
                        "No talking points available."
                    )

                # ------------------------------------------------
                # RECENT TICKETS
                # ------------------------------------------------

                recent_tickets = result.get(
                    "recent_tickets",
                    [],
                )

                st.subheader(
                    f"🎫 Recent Tickets "
                    f"({len(recent_tickets)})"
                )

                if recent_tickets:

                    for ticket in recent_tickets:

                        subject_text = ticket.get(
                            "subject",
                            "Support Ticket",
                        )

                        with st.expander(
                            subject_text
                        ):

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.caption("Ticket ID")
                                st.write(
                                    ticket.get(
                                        "ticket_id",
                                        "Unknown",
                                    )
                                )

                            with col2:
                                st.caption("Status")
                                st.write(
                                    ticket.get(
                                        "status",
                                        "Unknown",
                                    )
                                )

                            with col3:
                                st.caption("Urgency")
                                st.write(
                                    ticket.get(
                                        "urgency",
                                        "Unknown",
                                    )
                                )

                            st.write(
                                ticket.get(
                                    "body",
                                    "No description available.",
                                )
                            )

                else:

                    st.info(
                        "No recent tickets found."
                    )

            except ValueError:

                # IMPORTANT:
                # Do not expose the raw Python exception.
                st.error(
                    "⚠️ Account not found"
                )

                st.write(
                    f"We couldn't find "
                    f"`{account_id.strip()}`. "
                    "Please check the account ID and try again."
                )

            except Exception as exc:

                st.error(
                    "Unable to complete account health analysis."
                )

                st.caption(
                    f"Details: {exc}"
                )



# KNOWLEDGE BASE SEARCH


elif page == "🔎 Knowledge Base Search":

    st.markdown(
        """
        <div class="hero">
            <h1>🔎 Knowledge Base Search</h1>
            <p>
                Search the local knowledge base and inspect the most
                relevant documentation retrieved for your question.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    query = st.text_input(
        "Search the knowledge base",
        placeholder="e.g. How do I enable SSO?",
    )

    top_k = st.slider(
        "Number of results",
        min_value=1,
        max_value=5,
        value=3,
    )

    search_kb = st.button(
        "Search Knowledge Base",
        type="primary",
        use_container_width=True,
    )

    if search_kb:

        if not query.strip():

            st.warning(
                "Please enter a search query."
            )

        else:

            try:

                with st.spinner(
                    "Searching knowledge base..."
                ):

                    results = retriever.search(
                        query.strip(),
                        top_k=top_k,
                    )

                st.success(
                    f"Found {len(results)} relevant result(s)."
                )

                st.divider()

                if not results:

                    st.info(
                        "No relevant knowledge-base content found."
                    )

                else:

                    for index, result in enumerate(
                        results,
                        start=1,
                    ):

                        source = result.get(
                            "source",
                            "Unknown source",
                        )

                        section = result.get(
                            "section",
                            "Knowledge Base",
                        )

                        score = result.get(
                            "score",
                            0,
                        )

                        content = get_result_text(
                            result
                        )

                        st.markdown(
                            f"### {index}. {section}"
                        )

                        st.caption(
                            f"Source: `{source}`"
                        )

                        if score is not None:

                            try:

                                st.caption(
                                    f"Relevance score: "
                                    f"{float(score):.2f}"
                                )

                            except (
                                TypeError,
                                ValueError,
                            ):
                                pass

                        if content:

                            st.write(content)

                        else:

                            # Fallback so the UI still exposes
                            # the retrieved result even if the
                            # retriever uses a different field.
                            st.json(result)

                        if index < len(results):
                            st.divider()

            except Exception as exc:

                st.error(
                    "Unable to search the knowledge base."
                )

                st.caption(
                    f"Details: {exc}"
                )



# FOOTER

st.divider()

st.caption(
    "Zycus AI Support Ticket Triage • "
     "Local retrieval + Ollama LLM"
)