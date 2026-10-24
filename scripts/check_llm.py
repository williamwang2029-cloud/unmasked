"""Diagnose the LLM connection with one live call.

Usage:  python scripts/check_llm.py

Loads .env the same way the app does, prints the resolved (masked) config, makes a single
real call through reid.llm.complete(), and tells you exactly what happened. Never prints your
API key and never sends any dataset content, only a tiny fixed test prompt.
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from reid import llm

load_dotenv()


def mask(value):
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return "****"
    return value[:4] + "…" + value[-4:]


def main():
    provider = os.getenv("LLM_PROVIDER", "none")
    model = os.getenv("LLM_MODEL")
    base_url = os.getenv("OPENAI_BASE_URL")

    print("=== LLM config (from environment / .env) ===")
    print(f"LLM_PROVIDER     : {provider}")
    print(f"LLM_MODEL        : {model or '(not set)'}")
    print(f"OPENAI_BASE_URL  : {base_url or '(not set, uses OpenAI default)'}")
    print(f"OPENAI_API_KEY   : {mask(os.getenv('OPENAI_API_KEY'))}")
    print(f"ANTHROPIC_API_KEY: {mask(os.getenv('ANTHROPIC_API_KEY'))}")
    print(f"llm.llm_enabled(): {llm.llm_enabled()}")
    print()

    if not llm.llm_enabled():
        print("RESULT: LLM is DISABLED. The app will run in rule-based fallback mode.")
        print("Fix: set LLM_PROVIDER to 'openai' or 'anthropic' in your .env, then rerun.")
        return 1

    if provider.lower() == "openai" and not model:
        print("WARNING: provider is 'openai' but LLM_MODEL is empty. OpenAI/Gemini require a model name.")
        print("         For Gemini via AI Studio, set e.g. LLM_MODEL=gemini-2.0-flash")
        print()

    print("=== Making one live test call… ===")
    reply = llm.complete("Reply with exactly the word: pong", max_tokens=20)

    if reply is None:
        print("RESULT: the call returned None. The wrapper caught an error (see the '[llm] error:' line above).")
        print("Common causes:")
        print("  - wrong or unset LLM_MODEL (Gemini: use a model name from AI Studio)")
        print("  - invalid/disabled API key, or key not enabled for this model")
        print("  - wrong OPENAI_BASE_URL for the Gemini OpenAI-compatible endpoint")
        print("  - the 'openai' package is not installed (pip install -r requirements.txt)")
        return 1

    print("RESULT: live call SUCCEEDED. Raw model reply:")
    print(repr(reply))
    print()
    print("The app sidebar should show '🟢 LLM connected'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
