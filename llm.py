"""
llm.py — LLM provider setup (Groq / Gemini), Kridh Capital wale pattern jaisa.

.env me jo key hai uske hisaab se provider chunta hai:
  - LLM_PROVIDER = groq | gemini   (default: groq)
  - GROQ_API_KEY  + GROQ_MODEL     (default model: llama-3.1-8b-instant)
  - GEMINI_API_KEY + GEMINI_MODEL  (default model: gemini-2.5-flash)

Koi key na ho to generate() saaf-saaf bata deta hai (None, "none").
"""

import os
from dotenv import load_dotenv

# .env ko isi folder se load karo (chahe kahin se bhi run karein)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

_groq = None
_gemini = None


def _get_groq():
    global _groq
    if not GROQ_API_KEY:
        return None
    if _groq is None:
        from groq import Groq
        _groq = Groq(api_key=GROQ_API_KEY)
    return _groq


def _get_gemini():
    global _gemini
    if not GEMINI_API_KEY:
        return None
    if _gemini is None:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini = genai.GenerativeModel(GEMINI_MODEL)
    return _gemini


def active_provider():
    """Konsa provider use hoga, ye decide karo (Kridh jaisa fallback order)."""
    if LLM_PROVIDER == "groq" and GROQ_API_KEY:
        return "groq"
    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        return "gemini"
    if GROQ_API_KEY:
        return "groq"
    if GEMINI_API_KEY:
        return "gemini"
    return "none"


def generate(prompt):
    """Prompt LLM ko bhejo. Return: (text_or_None, provider_name)."""
    provider = active_provider()
    try:
        if provider == "groq":
            client = _get_groq()
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
            )
            return resp.choices[0].message.content, "groq"
        if provider == "gemini":
            model = _get_gemini()
            return model.generate_content(prompt).text, "gemini"
    except Exception as e:
        return f"[{provider} call failed: {e}]", provider
    return None, "none"
