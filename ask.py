"""Ask the company brain as a given user. Only that user's dataset is searched.

Usage:
    python ask.py --user alice@lumen.test "What caused the Sept 2 billing outage?"
    python ask.py --user bob@lumen.test   "What caused the Sept 2 billing outage?"

If RESPAN_API_KEY is set, runs are traced in Respan (gateway + tracing).
"""
import argparse
import asyncio
import logging
import os
import re

try:  # corporate SSL inspection: use the OS trust store
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

from dotenv import load_dotenv

load_dotenv()

_respan = None


def init_respan():
    """Enable Respan tracing when a key is present. Safe no-op otherwise."""
    global _respan
    if _respan is not None or not os.getenv("RESPAN_API_KEY"):
        return _respan
    try:
        from respan import Respan
        from respan_instrumentation_openai import OpenAIInstrumentor

        _respan = Respan(instrumentations=[OpenAIInstrumentor()])
    except Exception:  # noqa: BLE001 - SDK optional; gateway logs still work
        _respan = False
    return _respan


def flush_respan():
    if _respan:
        _respan.flush()


import cognee  # noqa: E402  (after truststore/dotenv so env + certs apply)


def dataset_for(user: str) -> str:
    # BRAIN_MODE=shared simulates a brain with NO access control: everyone reads
    # the leadership dataset. Used only to produce the "before" eval baseline.
    if os.getenv("BRAIN_MODE") == "shared":
        return os.getenv("SHARED_DATASET", "jian_han3-brain")
    return re.sub(r"[^A-Za-z0-9_-]", "_", user.split("@")[0]) + "-brain"


async def answer(user: str, question: str) -> str:
    """Return the brain's answer for this user (their dataset only)."""
    try:
        results = await cognee.recall(question, datasets=[dataset_for(user)])
    except Exception as e:  # noqa: BLE001
        return f"[no accessible memory: {type(e).__name__}]"
    texts = [getattr(r, "text", None) or str(r) for r in results]
    return "\n".join(texts) if texts else "I could not find that in your accessible knowledge."


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("question")
    args = ap.parse_args()

    logging.disable(logging.CRITICAL)
    init_respan()
    print(f"[{args.user} -> {dataset_for(args.user)}]")
    print(await answer(args.user, args.question))
    flush_respan()


if __name__ == "__main__":
    asyncio.run(main())
