# backend/rag/qa.py
from __future__ import annotations
import re
import os
from typing import Tuple, List, Dict, Optional
from sqlalchemy import select

from backend.rag.retrieve import retrieve
from backend.rag.llm import (
    generate_answer, summarize_history, Provider,
    is_greeting_or_casual, handle_greeting_or_casual
)
from backend.db import db_session
from backend.models import ChatSession, Message


# -----------------------------
# Configuration & Constants
# -----------------------------
MAX_MESSAGES_PER_SESSION = int(os.getenv("MAX_MESSAGES_PER_SESSION", "12"))
MAX_QA_PAIRS_IN_PROMPT = 6

WARNING_KEYWORDS = [
    r"not recommended", r"contraindicated", r"avoid alcohol", r"do not use",
    r"caution", r"warning", r"side effects?", r"adverse reactions?",
    r"allergic reaction", r"overdose", r"toxic", r"dangerous", r"fatal",
    r"emergency", r"immediately consult", r"stop taking", r"discontinue"
]

PROMPT_TEMPLATE = """You are a medical information assistant. Answer the user's question using the provided medical documents.

INSTRUCTIONS:
- Use the DOCUMENT CONTEXT below to answer questions accurately
- For simple questions, provide concise answers (1-2 sentences)
- For complex medical topics, provide detailed explanations with bullet points
- Always prioritize patient safety and mention any warnings or contraindications clearly
- Do NOT include source citations in the main response - they will be shown separately
- If the context doesn't contain relevant information, say "I don't have specific information about this in the current knowledge base"

ROLLING SUMMARY (earlier conversation):
{rolling_summary}

RECENT CONVERSATION:
{recent_history}

DOCUMENT CONTEXT (medical sources selected for relevance):
{context}

USER QUESTION: {question}

MEDICAL RESPONSE:"""


# -----------------------------
# Simple utility functions
# -----------------------------
def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text).strip()


def highlight_medical_warnings(text: str) -> Dict[str, any]:
    """Find and mark medical warning terms in the answer."""
    warnings_found = []
    clean_text = text
    for warning_pattern in WARNING_KEYWORDS:
        pattern = re.compile(rf"({warning_pattern})", re.IGNORECASE)
        matches = pattern.finditer(text)
        for match in matches:
            warnings_found.append({
                "text": match.group(1),
                "start": match.start(),
                "end": match.end(),
                "type": "warning"
            })
    return {"text": clean_text, "warnings": warnings_found}


# -----------------------------
# Formatting helpers
# -----------------------------
def _format_context(chunks: List[Dict]) -> str:
    if not chunks:
        return "No relevant documents found."
    parts = []
    for i, c in enumerate(chunks, 1):
        content_type = c.get('type', 'text')
        score_info = f"Score: {c.get('final_score', c.get('score', 0)):.2f}"
        if 'frequency' in c:
            score_info += f" | Retrieved by {c['frequency']} query variants"
        if content_type.startswith('table'):
            header = f"--- TABLE SOURCE {i}: {c['source']} (Page {c['page']}) | {score_info} ---"
        else:
            header = f"--- SOURCE {i}: {c['source']} (Page {c['page']}) | {score_info} ---"
        content = c["text"].strip()
        parts.append(f"{header}\n{content}")
    return "\n\n".join(parts)


def _format_history(pairs: List[Dict]) -> str:
    if not pairs:
        return "No previous conversation."
    formatted = []
    for i, p in enumerate(pairs, 1):
        clean_q = re.sub(r'<[^>]+>', '', p['q'])
        clean_a = re.sub(r'<[^>]+>', '', p['a'])
        formatted.append(f"Q{i}: {clean_q}\nA{i}: {clean_a}")
    return "\n\n".join(formatted)


# -----------------------------
# Database helpers
# -----------------------------
def _get_last_n_qa_pairs(db, session_id: int, n_pairs: int) -> List[Dict]:
    stmt = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.asc())
    messages = list(db.execute(stmt).scalars())
    pairs: List[Dict] = []
    cur_q = None
    for m in messages:
        if m.role == "user":
            cur_q = m.content
        elif m.role == "assistant" and cur_q is not None:
            pairs.append({"q": cur_q, "a": m.content})
            cur_q = None
    return pairs[-n_pairs:]


def _count_messages_in_session(db, session_id: int) -> int:
    stmt = select(Message).where(Message.session_id == session_id)
    return len(list(db.execute(stmt).scalars()))


def _maybe_update_summary(db, sess: ChatSession, provider: Provider):
    pairs_all = _get_last_n_qa_pairs(db, sess.id, 10_000)
    if len(pairs_all) <= MAX_QA_PAIRS_IN_PROMPT:
        return
    older = pairs_all[:-MAX_QA_PAIRS_IN_PROMPT]
    if not older:
        return
    older_text = _format_history(older)
    rolled = summarize_history(older_text, provider=provider)
    if sess.summary:
        sess.summary = (sess.summary + "\n\n" + rolled).strip()
    else:
        sess.summary = rolled


# -----------------------------
# Main complex function
# -----------------------------
def answer_question(
    question: str,
    session_id: Optional[int],
    top_k: int,
    index_dir: str,
    provider: Provider = "auto",
    model_override: Optional[str] = None,
    use_enhanced_retrieval: bool = True,
) -> Tuple[str, List[Dict], Optional[int], bool]:
    """
    Answer a question using enhanced RAG.
    Supports evaluation mode (session_id=None).
    """
    with db_session() as db:
        sess = None
        if session_id is not None:
            sess = db.get(ChatSession, session_id)
            if not sess:
                raise ValueError("Session not found")

        # === Evaluation Mode (no DB session) ===
        if sess is None:
            try:
                hits = retrieve(
                    query=question,
                    index_dir=index_dir,
                    top_k=top_k,
                    use_mmr=use_enhanced_retrieval,
                    use_multi_query=use_enhanced_retrieval
                )
                context = _format_context(hits)
                prompt = PROMPT_TEMPLATE.format(
                    rolling_summary="Evaluation mode (no chat history).",
                    recent_history="",
                    question=question,
                    context=context,
                )
                raw_answer = generate_answer(prompt, provider=provider, model_override=model_override)
                clean_answer = clean_html_tags(raw_answer)
                warning_analysis = highlight_medical_warnings(clean_answer)
                citations = [
                    {
                        "source": h["source"],
                        "page": h["page"],
                        "score": h.get("final_score", h.get("score", 0)),
                        "rank": h.get("rank", i + 1),
                        "type": h.get("type", "text"),
                    }
                    for i, h in enumerate(hits)
                ]
                response_data = {"text": warning_analysis["text"], "warnings": warning_analysis["warnings"]}
                return response_data["text"], citations, None, False
            except Exception as e:
                return f"[Evaluation error: {e}]", [], None, False

        # === Normal Chat Mode (with DB session) ===
        message_count = _count_messages_in_session(db, sess.id)
        session_limit_reached = message_count >= MAX_MESSAGES_PER_SESSION
        if session_limit_reached:
            limit_message = (
                f"This session has reached the maximum limit of {MAX_MESSAGES_PER_SESSION} messages. "
                "Please start a new session to continue."
            )
            return limit_message, [], sess.id, True

        if is_greeting_or_casual(question):
            answer = handle_greeting_or_casual(question)
            user_msg = Message(session_id=sess.id, role="user", content=question)
            db.add(user_msg)
            db.flush()
            asst_msg = Message(session_id=sess.id, role="assistant", content=answer, citations=[])
            db.add(asst_msg)
            from datetime import datetime
            sess.updated_at = datetime.utcnow()
            return answer, [], sess.id, False

        user_msg = Message(session_id=sess.id, role="user", content=question)
        db.add(user_msg)
        db.flush()

        try:
            hits = retrieve(
                query=question,
                index_dir=index_dir,
                top_k=top_k,
                use_mmr=use_enhanced_retrieval,
                use_multi_query=use_enhanced_retrieval
            )
            pairs_recent = _get_last_n_qa_pairs(db, sess.id, MAX_QA_PAIRS_IN_PROMPT)
            recent_history = _format_history(pairs_recent)
            context = _format_context(hits)
            prompt = PROMPT_TEMPLATE.format(
                rolling_summary=sess.summary or "No previous summary.",
                recent_history=recent_history,
                question=question,
                context=context,
            )
            raw_answer = generate_answer(prompt, provider=provider, model_override=model_override)
            clean_answer = clean_html_tags(raw_answer)
            warning_analysis = highlight_medical_warnings(clean_answer)
            citations = []
            for h in hits:
                citation = {
                    "source": h["source"],
                    "page": h["page"],
                    "score": h.get('final_score', h.get('score', 0)),
                    "rank": h.get("rank", len(citations) + 1),
                    "type": h.get("type", "text")
                }
                if 'frequency' in h:
                    citation['frequency'] = h['frequency']
                if 'avg_score' in h:
                    citation['avg_score'] = h['avg_score']
                citations.append(citation)
            response_data = {"text": warning_analysis["text"], "warnings": warning_analysis["warnings"]}
        except Exception as e:
            clean_answer = f"I apologize, but I encountered an error while processing your question: {str(e)}"
            citations = []
            response_data = {"text": clean_answer, "warnings": []}

        asst_msg = Message(
            session_id=sess.id,
            role="assistant",
            content=response_data["text"],
            citations=citations if citations else None
        )
        db.add(asst_msg)
        _maybe_update_summary(db, sess, provider=provider)
        from datetime import datetime
        sess.updated_at = datetime.utcnow()
        new_message_count = _count_messages_in_session(db, sess.id)
        approaching_limit = new_message_count >= MAX_MESSAGES_PER_SESSION

        return response_data["text"], citations, sess.id, approaching_limit
