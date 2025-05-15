"""
Light wrapper around the OpenAI chat API with automatic retries.
Usage:
    from app.core.llm import chat
    txt = chat([{"role":"user","content":"Hello"}], model="gpt-4o")
"""
import os, backoff
from openai import OpenAI
from dotenv import load_dotenv
from app.core import FALLBACK_MODEL

load_dotenv()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@backoff.on_exception(backoff.expo, Exception, max_tries=5, max_time=60)
def chat(messages, model, *, json_mode=False, **kw):
    try:
        resp = _client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type":"json_object"} if json_mode else None,
            **kw
        )
        return resp.choices[0].message.content
    except Exception as e:
        if model != FALLBACK_MODEL:          # one-step fallback
            return chat(messages, model=FALLBACK_MODEL,
                        json_mode=json_mode, **kw)
        raise 