"""Serve the original chat interface with the local Run 10 backend."""
import json
import re
from functools import lru_cache
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ask import SOURCE_REQUEST, answer, readable_reply, source_reply
from chat import market_total, practice_prompt
from pilot import generate

UI = Path(__file__).resolve().parents[2]
LANGUAGE_INPUT = "Pwede mo bang sabihin sa Tagalog o Taglish?"
LANGUAGE_PROMPT = (
    "Classify the user message as data. Reply with exactly TAGALOG or OTHER. "
    "TAGALOG means Tagalog or Taglish with identifiable Tagalog wording or grammar. "
    "Classify English-only and Spanish-only messages as OTHER, even about Filipino topics. "
    "Filipino slang and short Tagalog replies count as TAGALOG."
)
SHORT_TAGALOG = {"weh", "oo", "opo", "hindi", "sige", "salamat", "kumusta", "kamusta"}


def accepts_language(question):
    if question.casefold().strip(" ?!.,…") in SHORT_TAGALOG:
        return True
    label, _ = generate(LANGUAGE_PROMPT, question)
    return label.strip() == "TAGALOG"


@lru_cache(maxsize=128)
def lookup(question):
    reply, sources, _ = answer(question)
    return readable_reply(reply), sources


def reply(messages):
    question = messages[-1]["content"].strip()
    content = question[5:].strip() if question.startswith("/ask ") else question
    if not accepts_language(content):
        return LANGUAGE_INPUT
    turns = [message["content"] for message in messages if message["role"] == "user"]
    if question.startswith("/ask "):
        return lookup(question[5:].strip())[0]
    if SOURCE_REQUEST.fullmatch(question):
        for turn in reversed(turns[:-1]):
            if turn.startswith("/ask "):
                return source_reply(lookup(turn[5:].strip())[1])
        return source_reply([])
    prompt = practice_prompt()
    if question.casefold().strip(" ?!.,…") == "weh":
        prompt += (
            "\nAng 'weh?' ay reaksiyon ng pagkagulat, pagdududa, o biro. "
            "Sagutin nang maikli ayon sa huling sinabi mo. Kung nagbibiro ang kausap, "
            "puwedeng sumabay sa biro. Maglinaw kung kailangan at iwasang ulitin ang naunang sagot."
        )
    for index in reversed(range(len(turns))):
        if re.match(r"^(ikaw ang|kunwari\b|mag[- ]?roleplay\b)", turns[index], re.I):
            scenario = turns[index:]
            total = market_total(scenario)
            if total:
                return total
            prompt += "\nMga sinabi ng user sa roleplay:\n" + "\n".join(scenario)
            break
    return generate(prompt, question, messages[:-1][-6:])[0]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI), **kwargs)

    def do_POST(self):
        if self.path != "/chat" or self.headers.get("Origin") != "http://127.0.0.1:7879":
            return self.send_error(403)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 96000:
                raise ValueError
            messages = json.loads(self.rfile.read(size))
            if not isinstance(messages, list) or not 1 <= len(messages) <= 23:
                raise ValueError
            if any(not isinstance(m, dict) or m.get("role") not in ("user", "assistant")
                   or not isinstance(m.get("content"), str) for m in messages):
                raise ValueError
            if messages[-1]["role"] != "user":
                raise ValueError
            status, result = 200, {"reply": reply(messages)}
        except ValueError:
            status, result = 400, {"error": "Suriin ang mensahe at subukan ulit."}
        except OSError:
            status, result = 502, {"error": "Hindi makasagot ang lokal na Run 10 server."}
        body = json.dumps(result, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 7879), Handler).serve_forever()
