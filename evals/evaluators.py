"""LLM-as-judge evaluators for the offline experiment.

The top-level graph only surfaces the deep agent's final natural-language
summary in state["messages"] (the subagent's own tool calls run in an
isolated `task` context, visible in the LangSmith trace but not replayed
into parent state) - so, unlike a flat ReAct agent, these evaluators judge
the final answer text rather than a raw tool-call trajectory:

- `hallucination_evaluator` - checks whether the final answer states facts
  (e.g. a PO number) not supported by the input email. Per-example score is
  1.0 = hallucination detected, 0.0 = grounded, so the LangSmith aggregate
  reads as the hallucination rate.

- `expected_behavior_evaluator` - checks whether the final answer matches
  the example's `expected_behavior` description (e.g. "should ask for
  clarification, not invent a PO"). Score is True when the judge finds the
  actual behavior consistent with what was expected.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, cast

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

JUDGE_MODEL_NAME = "gpt-4o"


def _make_judge() -> ChatOpenAI:
    base_url = os.getenv("BASE_URL")
    if base_url:
        return ChatOpenAI(
            model=JUDGE_MODEL_NAME,
            temperature=0,
            base_url=base_url,
            api_key=os.environ["LC_GATEWAY_KEY"],
        )
    return ChatOpenAI(model=JUDGE_MODEL_NAME, temperature=0)


_judge = _make_judge()


class _JudgeResult(BaseModel):
    """Structured verdict returned by every LLM-as-judge."""

    reasoning: str = Field(
        description="One or two sentences justifying the verdict, citing the "
        "specific phrase or fact that drove the decision."
    )
    score: bool = Field(
        description="True when the criteria described in the judge prompt are satisfied, False otherwise."
    )


def create_llm_as_judge(*, prompt: str, feedback_key: str, judge: ChatOpenAI) -> Callable[..., dict]:
    """Build a boolean LLM-as-judge scorer from a prompt template."""

    structured_judge = judge.with_structured_output(_JudgeResult)

    def scorer(**prompt_vars: Any) -> dict:
        verdict = cast(_JudgeResult, structured_judge.invoke(prompt.format(**prompt_vars)))
        return {"key": feedback_key, "score": verdict.score, "comment": verdict.reasoning}

    return scorer


HALLUCINATION_JUDGE_PROMPT = """You are an expert evaluator checking a back-office \
document-processing agent's final answer for hallucinations - claims (PO numbers, \
amounts, dates, vendor details) that are not supported by the source email.

<Rubric>
  The answer CONTAINS a hallucination when it:
  - States a PO number, invoice number, amount, or date not present in the source email
  - Asserts an ERP match or validation result that isn't consistent with the email
  - Invents details to fill a gap instead of asking for clarification or escalating
  The answer is FREE of hallucinations when every specific fact it states is either
  present in the source email or is a deterministic tool result (a record id or
  ticket id are fine - those come from the system, not invented).
</Rubric>

<source_email>
{context}
</source_email>

<agent_final_answer>
{outputs}
</agent_final_answer>

If available, the expected behavior for this case may help you judge:

<expected_behavior>
{reference_outputs}
</expected_behavior>

Set score to true if the final answer contains a hallucination, false if it is fully grounded."""

_hallucination_scorer = create_llm_as_judge(
    prompt=HALLUCINATION_JUDGE_PROMPT, feedback_key="hallucination", judge=_judge
)


EXPECTED_BEHAVIOR_JUDGE_PROMPT = """You are grading whether a back-office \
document-processing agent behaved as expected for a given email.

<expected_behavior>
{reference_outputs}
</expected_behavior>

<agent_final_answer>
{outputs}
</agent_final_answer>

Set score to true if the agent's final answer is consistent with the expected \
behavior described above, and false if it is not (e.g. it posted/invented \
something the expected behavior says it should have asked about or escalated \
instead, or it failed to take an action the expected behavior says it should \
have taken)."""

_expected_behavior_scorer = create_llm_as_judge(
    prompt=EXPECTED_BEHAVIOR_JUDGE_PROMPT, feedback_key="expected_behavior", judge=_judge
)


def _final_text(messages: list[Any]) -> str:
    for msg in reversed(messages):
        content = getattr(msg, "content", None)
        if content is None and isinstance(msg, dict):
            content = msg.get("content")
        if content:
            return content if isinstance(content, str) else str(content)
    return ""


def _source_email(inputs: dict) -> str:
    msgs = inputs.get("messages", []) if isinstance(inputs, dict) else []
    for msg in msgs:
        if isinstance(msg, dict) and msg.get("role") == "user":
            return str(msg.get("content", ""))
    return ""


def hallucination_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """LLM-as-judge for facts in the final answer unsupported by the source email."""
    messages = outputs.get("messages", []) if isinstance(outputs, dict) else []
    answer = _final_text(messages)
    verdict = _hallucination_scorer(
        context=_source_email(inputs),
        outputs=answer,
        reference_outputs=str((reference_outputs or {}).get("expected_behavior", "")),
    )
    detected = bool(verdict["score"])
    return {"key": "hallucination", "score": 1.0 if detected else 0.0, "comment": verdict["comment"]}


def expected_behavior_evaluator(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    """LLM-as-judge for whether the final answer matches the example's expected_behavior."""
    del inputs
    messages = outputs.get("messages", []) if isinstance(outputs, dict) else []
    answer = _final_text(messages)
    expected = (reference_outputs or {}).get("expected_behavior") or (reference_outputs or {}).get(
        "reference_answer", ""
    )
    return _expected_behavior_scorer(outputs=answer, reference_outputs=expected)
