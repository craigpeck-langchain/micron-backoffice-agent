"""Graph state schema for the top-level intake graph."""

from __future__ import annotations

from typing import Optional

from langgraph.graph import MessagesState


class BackofficeState(MessagesState):
    """Messages plus the classifier's routing decision.

    `doc_type` and `confidence` are set by classify_document and drive the
    conditional edge to either the deep agent or request_clarification.
    """

    doc_type: Optional[str]
    confidence: Optional[float]
    email_text: Optional[str]
