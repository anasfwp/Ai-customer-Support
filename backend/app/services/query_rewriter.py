"""Turn a follow-up question into a standalone search query using the conversation so far."""
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

MAX_TURNS = 3           # most recent question/answer pairs given to the rewriter
MAX_ANSWER_CHARS = 400  # long answers are cut; the gist is enough to resolve "it" or "that"
MAX_QUERY_CHARS = 300
TIMEOUT_SECONDS = 10    # past this the user is left waiting; the fallback is nearly as good (see eval/results.md)

SYSTEM = "You rewrite questions for a document search engine. Reply with the rewritten question only."

PROMPT = """Rewrite the FOLLOW-UP as one standalone question that can be understood without the conversation.
Replace words like "it", "that" or "there" with what they refer to. Keep the user's meaning and language; do not answer it.
If the follow-up is already standalone, return it unchanged.

CONVERSATION:
{conversation}

FOLLOW-UP: {question}

STANDALONE QUESTION:"""


def fallback_query(question: str, history: List[Dict[str, str]]) -> str:
    """No-LLM stand-in for a rewrite: the previous question followed by the follow-up"""
    return f"{history[-1]['question']} {question}" if history else question


def rewrite_query(llm, question: str, history: List[Dict[str, str]], timeout: Optional[float] = TIMEOUT_SECONDS) -> str:
    """Return a standalone version of `question`; uses `fallback_query` if the LLM fails, is too slow, or misbehaves"""
    turns = history[-MAX_TURNS:]
    conversation = "\n".join(
        f"User: {turn['question']}\nAssistant: {turn['answer'][:MAX_ANSWER_CHARS]}" for turn in turns
    ) or "(none)"
    try:
        text = "".join(llm.stream(PROMPT.format(conversation=conversation, question=question), system=SYSTEM, timeout=timeout))
    except Exception as e:
        logger.warning("Query rewrite failed (%s), using the previous question + follow-up", e)
        return fallback_query(question, history)
    # Models sometimes add a label or quotes, or keep talking; keep just the first line of the question
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    rewritten = lines[0].removeprefix("STANDALONE QUESTION:").strip().strip('"\'') if lines else ""
    if not rewritten or len(rewritten) > MAX_QUERY_CHARS:
        return fallback_query(question, history)
    return rewritten
