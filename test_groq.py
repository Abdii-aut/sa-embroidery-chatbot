"""Run from project root: python test_groq.py. Does not print your API key."""
import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parent / '.env', override=True)
key = os.getenv('GROQ_API_KEY', '').strip()
model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
print('Key configured:', bool(key), '| Model:', model)
if not key:
    raise SystemExit('Missing GROQ_API_KEY in project-root .env')
try:
    client = Groq(api_key=key, timeout=35, max_retries=0)
    reply = client.chat.completions.create(
        model=model,
        messages=[{'role':'user','content':'Reply with exactly: Connection OK'}],
        max_completion_tokens=1600,
    )
    print('AI reply:', repr(reply.choices[0].message.content))
    print('Finish reason:', reply.choices[0].finish_reason)
except Exception as exc:
    print('Request failed:', type(exc).__name__)
    print('HTTP status:', getattr(exc, 'status_code', 'n/a'))
    err = str(exc).replace(key, '[REDACTED]')
    print('Error:', err[:1000])
