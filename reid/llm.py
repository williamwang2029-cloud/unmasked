"""Thin, swappable LLM wrapper. Returns None when disabled or on any error,
so every caller MUST have a rule-based fallback."""
import json
import os
import re


def llm_enabled():
    return os.getenv("LLM_PROVIDER", "none").lower() in ("anthropic", "openai")


def complete(prompt, system=None, json_mode=False, max_tokens=800):
    provider = os.getenv("LLM_PROVIDER", "none").lower()
    model = os.getenv("LLM_MODEL")
    if provider not in ("anthropic", "openai"):
        return None
    if json_mode:
        prompt += "\n\nRespond with valid JSON only. No prose, no code fences."
    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
            kwargs = {"model": model or "claude-haiku-5-5", "max_tokens": max_tokens,
                      "messages": [{"role": "user", "content": prompt}]}
            if system:
                kwargs["system"] = system
            msg = client.messages.create(**kwargs)
            return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI()  # reads OPENAI_API_KEY
            messages = ([{"role": "system", "content": system}] if system else []) + \
                       [{"role": "user", "content": prompt}]
            r = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens)
            return r.choices[0].message.content
    except Exception as e:  # never crash the app because of the LLM
        print(f"[llm] error: {e}")
    return None


def parse_json(text):
    if not text:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                return None
    return None
