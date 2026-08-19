"""FastAPI custom routes for the LangGraph agent server.

Mounted at the deployment root via `langgraph.json`'s `http.app` key, so
this app extends the agent server (which already exposes `/threads`,
`/runs`, `/assistants`, etc.) with our own routes:

- `GET  /health`            - simple liveness probe
- `GET  /`                  - redirect to `/inbox/`
- `GET  /inbox/`            - the built React inbox UI (Vite dist/)
- `POST /inbox-api/feedback` - record thumbs up/down on a run in LangSmith

If the frontend bundle hasn't been built yet, `/inbox/*` returns a 503 with
a hint to run `npm install && npm run build` in `frontend/`.

The feedback route keeps `LANGSMITH_API_KEY` server-side: the browser posts
only `{run_id, score, comment}` and this app calls the LangSmith SDK on its
behalf, so the key is never shipped to the client.

NOTE: do NOT add `from __future__ import annotations` here. The custom app's
request models (e.g. FeedbackRequest) must resolve eagerly so the LangGraph
server can build the OpenAPI spec at startup; lazy string annotations raise
PydanticUserError("...is not fully defined").
"""

import pathlib
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from langsmith import Client, get_current_run_tree
from pydantic import BaseModel, Field

app = FastAPI()

_langsmith_client = Client()


def record_posting_review(score: float, run_id: uuid.UUID | None = None) -> None:
    """Record human review feedback for the current or supplied root run."""
    resolved_run_id = run_id
    if resolved_run_id is None:
        run_tree = get_current_run_tree()
        resolved_run_id = run_tree.id if run_tree is not None else None
    if resolved_run_id is None:
        raise ValueError("A root run_id is required to record posting review feedback")
    _langsmith_client.create_feedback(
        run_id=resolved_run_id,
        key="posting_reviewed",
        score=score,
        trace_id=resolved_run_id,
    )


class FeedbackRequest(BaseModel):
    run_id: uuid.UUID
    score: float = Field(ge=0, le=1)
    comment: str | None = None


@app.post("/inbox-api/feedback")
def submit_feedback(body: FeedbackRequest) -> dict[str, str]:
    """Attach user thumbs up/down to the LangSmith run that produced a reply."""
    try:
        _langsmith_client.create_feedback(
            body.run_id,
            key="user_feedback",
            score=body.score,
            trace_id=body.run_id,
            comment=body.comment,
        )
    except Exception as exc:  # noqa: BLE001 - surface a clean 502 to the client
        raise HTTPException(status_code=502, detail=f"Failed to record feedback: {exc}") from exc
    return {"status": "ok"}


FRONTEND_BUILD_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/inbox/")


@app.get("/inbox")
def inbox_redirect() -> RedirectResponse:
    return RedirectResponse(url="/inbox/")


if FRONTEND_BUILD_DIR.is_dir() and (FRONTEND_BUILD_DIR / "index.html").is_file():
    app.mount("/inbox", StaticFiles(directory=str(FRONTEND_BUILD_DIR), html=True), name="frontend")
else:

    @app.get("/inbox/{path:path}")
    def frontend_not_built(path: str = "") -> PlainTextResponse:
        del path
        return PlainTextResponse(
            "Frontend not built. From the project root, run:\n\n"
            "  npm --prefix frontend install\n"
            "  npm --prefix frontend run build\n",
            status_code=503,
        )
