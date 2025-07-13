"""High-stakes production prompts for query optimisation.

These templates are single-completion style (not chat prompts) because the
LLMChain wrapper applies a ChatOpenAI in completion mode.  Each template
returns JSON with field ``result`` for reliable downstream parsing.
"""
from essay_agent.prompts.templates import make_prompt

# ---------------------------------------------------------------------------
# Rewrite vague user query ---------------------------------------------------
# ---------------------------------------------------------------------------

REWRITE_PROMPT = make_prompt(
    """SYSTEM: You are the Query-Optimization Agent for an essay-writing assistant.
Your task is to rewrite a user query so that it is crystal-clear, specific,
and actionable for the assistant. Do NOT add new information. Preserve the
original intent and meaning while eliminating ambiguity.

INSTRUCTIONS:
1. Briefly reason about what the user is truly asking (do NOT output this).
2. Rewrite the query in the second person, filling in implicit details where
   obvious, but never introducing assumptions beyond the user message.
3. Keep it concise (max 1 sentence) and maintain the same voice (question or
   statement).
4. Output a JSON object **only** with the key "result" containing the
   rewritten query.

USER_QUERY: {query}

Respond with JSON only.
"""
)

# ---------------------------------------------------------------------------
# Compress conversation context ---------------------------------------------
# ---------------------------------------------------------------------------

COMPRESS_PROMPT = make_prompt(
    """SYSTEM: You are the Context-Compression Agent for an essay-writing assistant.
Your goal is to compress a conversation transcript while retaining all
critical facts, decisions, and open questions so the LLM can stay within
context window limits.

Guidelines:
- Preserve key user details, essay requirements, tool outputs, and decisions.
- Remove filler, small-talk, and acknowledgements.
- Maintain chronological order.
- Aim for <= {max_tokens} tokens (roughly equal to {max_tokens} / 0.75 words).

INSTRUCTIONS:
1. Analyse the transcript and identify essential information.
2. Produce a concise summary covering only those essentials.
3. Output JSON with a single key "result" containing the compressed text.

TRANSCRIPT_START
{context}
TRANSCRIPT_END
"""
)

# ---------------------------------------------------------------------------
# Clarify user question -------------------------------------------------------
# ---------------------------------------------------------------------------

CLARIFY_PROMPT = make_prompt(
    """SYSTEM: You are the Clarification Agent for an essay-writing assistant.
Your role is to rephrase or augment a vague user question so that the
assistant clearly understands what action or information is requested.

Steps:
1. Reflect silently on ambiguities in the user question (do not output).
2. Produce a clarified question that is explicit and self-contained.
3. Output JSON with key "result" containing the clarified question.

USER_QUESTION: {query}
"""
) 