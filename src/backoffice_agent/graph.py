"""Top-level intake graph.

    START -> ingest_email -> classify_document --(ambiguous)--> request_clarification -> END
                                    |
                                    v (doc_type known)
                              deep_agent_node -> END

`ingest_email` and `classify_document` are plain, deterministic LangGraph
nodes - the orchestration half of the demo. `deep_agent_node` wraps a
`deepagents.create_deep_agent` compiled graph that delegates to one of four
document-type subagents via its built-in `task` tool - the deep-agent half.
Both show up as distinct, nested spans in the LangSmith trace.

Exported as `graph` for LangSmith / LangGraph CLI deployment.
"""

from __future__ import annotations

from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from deepagents import create_deep_agent
from langgraph.graph import END, START, StateGraph

from backoffice_agent.classify import classify_document as run_classifier
from backoffice_agent.models import make_chat_model
from backoffice_agent.prompts import TOP_LEVEL_SYSTEM_PROMPT
from backoffice_agent.state import BackofficeState
from backoffice_agent.subagents import SUBAGENTS
from backoffice_agent.tools import SHARED_TOOLS, escalate_to_human

load_dotenv(override=True)

CONFIDENCE_THRESHOLD = 0.5

deep_agent = create_deep_agent(
    model=make_chat_model(temperature=0.1),
    tools=SHARED_TOOLS,
    system_prompt=TOP_LEVEL_SYSTEM_PROMPT,
    subagents=SUBAGENTS,
)


def _last_human_text(messages: list) -> str:
    for msg in reversed(messages):
        role = getattr(msg, "type", None) or (msg.get("role") if isinstance(msg, dict) else None)
        if role in ("human", "user"):
            content = getattr(msg, "content", None) if not isinstance(msg, dict) else msg.get("content")
            return content if isinstance(content, str) else str(content)
    return ""


def ingest_email(state: BackofficeState) -> dict:
    """Normalize the inbound email text. A distinct traced span for intake."""
    email_text = _last_human_text(state["messages"]).strip()
    return {"messages": [{"role": "user", "content": email_text}]}


def classify_document(state: BackofficeState) -> dict:
    """Deterministic doc-type routing - not the deep agent."""
    email_text = _last_human_text(state["messages"])
    result = run_classifier(email_text)
    return {"doc_type": result.doc_type, "confidence": result.confidence}


def route_after_classification(state: BackofficeState) -> str:
    doc_type = state.get("doc_type")
    confidence = state.get("confidence") or 0.0
    if doc_type == "out_of_scope" or confidence < CONFIDENCE_THRESHOLD:
        return "request_clarification"
    return "deep_agent"


def deep_agent_node(state: BackofficeState) -> dict:
    email_text = _last_human_text(state["messages"])
    doc_type = state.get("doc_type") or "unknown"
    sub_result = deep_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"Classified document type: {doc_type}\n\n{email_text}",
                }
            ]
        }
    )
    final = sub_result["messages"][-1]
    content = getattr(final, "content", None) or (final.get("content") if isinstance(final, dict) else "")
    return {"messages": [AIMessage(content=content)]}


def request_clarification_node(state: BackofficeState) -> dict:
    """Classifier couldn't confidently place this email in a supported type."""
    email_text = _last_human_text(state["messages"])
    result = escalate_to_human.invoke(
        {
            "reason": "Email did not confidently match a supported document type.",
            "doc_type": state.get("doc_type") or "unknown",
            "extracted_data": {"email_excerpt": email_text[:280]},
        }
    )
    reply = (
        "This email doesn't look like a shipping order, purchase order, invoice, "
        "or remittance advice I can process automatically. I've routed it to a "
        f"human reviewer (ticket {result['ticket_id']})."
    )
    return {"messages": [AIMessage(content=reply)]}


def _build_graph():
    builder = StateGraph(BackofficeState)
    builder.add_node("ingest_email", ingest_email)
    builder.add_node("classify_document", classify_document)
    builder.add_node("deep_agent", deep_agent_node)
    builder.add_node("request_clarification", request_clarification_node)

    builder.add_edge(START, "ingest_email")
    builder.add_edge("ingest_email", "classify_document")
    builder.add_conditional_edges(
        "classify_document",
        route_after_classification,
        {"deep_agent": "deep_agent", "request_clarification": "request_clarification"},
    )
    builder.add_edge("deep_agent", END)
    builder.add_edge("request_clarification", END)
    return builder.compile()


graph = _build_graph()
