"""Compare the released Gemma prompt with source-backed Q&A, locally."""
import argparse
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
GEMMA_PORT = int(os.environ.get("TAGALLM_GEMMA_PORT", "19468"))
APP = HERE.parent
SOURCE_LIBRARY = Path(os.environ.get("TAGALLM_SOURCE_LIBRARY") or HERE / "sources-regional-preview-v104.json")
SOURCES = json.loads(SOURCE_LIBRARY.read_text(encoding="utf-8-sig"))
CASES = [
    ("callao", "Ano ang natuklasan sa Callao Cave at gaano katanda ang buto sa paa?"),
    ("butuan", "Ano ang ipinapakita ng mga bangka sa Butuan? Alam ba ang eksaktong ruta ng bawat isa?"),
    ("colonial", "Pareho ba ang taon ng pagdating ni Magellan at pagtatatag ni Legazpi ng himpilan sa Cebu?"),
    ("leyte", "Kailan at saan bumalik si MacArthur sa Pilipinas?"),
    ("local", "Ano ba ang trabaho ng barangay sa ilalim ng Local Government Code?"),
    ("national", "Anong dalawang kapulungan ang bumubuo sa Kongreso?"),
    ("dated", "Ano ang pagkakaiba ng dalawang briefer sa impeachment ni Sara Duterte noong Enero at Agosto 2026?"),
    ("freshness", "Ano ang pinakabagong status ngayong araw ng impeachment ni Sara Duterte?"),
    ("regional", "Ano ang iniulat ng MindaNews tungkol sa flood control sa Davao? May hatol na ba?"),
    ("unknown", "Ano ang eksaktong kasalukuyang presyo ng mangga sa palengke ng Baguio?"),
]


def lookup_text(text):
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def retrieve(question):
    question = lookup_text(question)

    def matches(keyword):
        return re.search(r"(?<!\w)" + re.escape(lookup_text(keyword)) + r"(?!\w)", question) is not None

    return [
        source for source in SOURCES
        if any(matches(word) for word in source["keywords"])
        or any(all(matches(word) for word in group) for group in source.get("keyword_groups", []))
    ]


def generate(system, question, history=()):
    messages = [{"role": "system", "content": system}, *history,
                {"role": "user", "content": question}]
    body = {"model": "TagaLLM", "messages": messages, "temperature": 0, "max_tokens": 360}
    request = Request(f"http://127.0.0.1:{GEMMA_PORT}/v1/chat/completions", json.dumps(body).encode(),
                      {"Content-Type": "application/json"})
    start = time.monotonic()
    with urlopen(request, timeout=90) as response:
        answer = json.load(response)["choices"][0]["message"]["content"]
    return answer, round(time.monotonic() - start, 2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=[case for case, _ in CASES])
    parser.add_argument("--output", type=Path, default=HERE / "pilot-results.jsonl")
    args = parser.parse_args()
    baseline = (APP / "system-prompt.txt").read_text(encoding="utf-8-sig")
    instructions = (
        "Sumagot sa natural na Tagalog o Taglish. Saklaw ang kasaysayan, pamahalaan at balita sa Pilipinas. "
        "Gamitin lang bilang ebidensiya ang mga tala sa ibaba. Banggitin ang ID gaya ng [H1] "
        "katabi ng pahayag na sinusuportahan nito. Ihiwalay ang ulat, paratang at hatol. "
        "Ibigay ang petsa ng tala kung mahalaga. Kung hinihingi ang kalagayan ngayon at walang "
        "napapanahong tala, sabihin na hindi mo ito makumpirma at ibuod lang ang petsadong tala. "
        "Huwag mag-imbento ng citation, detalye, o resulta. Sagutin agad ang tanong sa hanggang "
        "apat na pangungusap. Sa paghahambing, sabihin ang pangunahing pagkakaiba sa unang pangungusap."
    )
    with args.output.open("w", encoding="utf-8") as output:
        for case, question in CASES:
            if args.case and case != args.case:
                continue
            sources = retrieve(question)
            evidence = "\n".join(f"[{s['id']}] {s['date'] or 'walang petsa'} — {s['note']}" for s in sources)
            for mode, system in (("released_prompt", baseline), ("sourced", instructions + "\n\n" + (evidence or "Walang nakitang tala."))):
                answer, seconds = generate(system, question)
                citations = set(re.findall(r"\[([A-Z]+\d+)\]", answer))
                available = {s["id"] for s in sources}
                citation_ok = mode != "sourced" or (
                    citations <= available and bool(citations) == bool(available)
                )
                row = dict(case=case, mode=mode, question=question, answer=answer, seconds=seconds,
                           citation_ok=citation_ok,
                           retrieved=[{"id": s["id"], "url": s["url"]} for s in sources] if mode == "sourced" else [])
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
                output.flush()
                print(case, mode, seconds, answer, flush=True)


if __name__ == "__main__":
    main()
