"""Ask the local Gemma information pilot a question."""
import argparse
import re

from factual_gate import CURRENT, failure
from pilot import generate, retrieve

CITATION = re.compile(r"\[([A-Z]+\d+)\]")
SOURCE_REQUEST = re.compile(
    r"\s*(?:saan (?:galing|nagmula)(?:\s+(?:ang|ito|iyan|'yan|’yan|yan).*)?|"
    r"(?:ano|alin) ang (?:source|sanggunian).*|"
    r"what(?:'s| is) (?:the|your) source|source(?: please)?|citation(?: please)?)\s*[?.!]*\s*",
    re.I,
)


def source_reply(sources):
    if not sources:
        return "Walang naka-save na sanggunian para sa sagot na iyon."
    return "\n".join(format_source(source) for source in sources)


def cited_sources(reply, sources):
    by_id = {source["id"]: source for source in sources}
    return [by_id[id_] for id_ in dict.fromkeys(CITATION.findall(reply)) if id_ in by_id]


def format_source(source):
    details = [source["publisher"], source.get("title"), source.get("date"), source["url"]]
    return f"[{source['id']}] " + " — ".join(detail for detail in details if detail)


def readable_reply(reply):
    reply = re.sub(r"^\[[A-Z]+\d+\][ \t]*", "", reply, flags=re.MULTILINE)
    group = r"[ \t]*\[[A-Z]+\d+\](?:[ \t]*,?[ \t]*\[[A-Z]+\d+\])*"
    reply = re.sub(r"([.!?])" + group + r"\1", r"\1", reply)
    reply = re.sub(group, "", reply)
    return re.sub(r"([.!?])\s*\[(?:[^\[\]\n]+)\]", r"\1", reply)


def grounded_prompt(sources, evidence):
    survey_guidance = ""
    if any(source.get("kind") == "survey" for source in sources):
        survey_guidance = (
            "Sa tanong tungkol sa survey, tukuyin ang populasyong kinakatawan at "
            "kung kailan isinagawa ang panayam. Iba ang sponsor sa nagsagawa ng survey. "
        )
    return (
        "Diretsong sagutin ang tanong sa natural na Tagalog o Taglish. "
        "Sagutin ang bawat bahagi kung dalawa o higit pa ang tanong. "
        "Kung sapat ang isang pangungusap, iyon lang ang ibigay. "
        "Magdagdag lang ng pangungusap para sa ibang mahalagang detalye o limitasyon. "
        "Huwag ulitin ang sagot, magbuod ulit, o magkomento sa mga detalyeng hindi tinanong. "
        "Kung 'Bakit nangyari ang X?' ang tanong at malinaw sa tala na hindi nangyari ang X, "
        "sabihin agad na hindi nangyari ang X at ipaliwanag kung ano ang nangyari. "
        "Kung kulang ang ebidensiya, sabihin na hindi pa kumpirmado ang ipinapalagay ng tanong. "
        "Gamitin lamang ang mga tala. Sagutin nang walang citation o source tag. "
        "Kung tungkol sa kalagayan ngayon ang tanong at kulang ang tala, sabihin iyon nang malinaw. "
        "Sa balita, pangalanan kung sino ang nagsabi at kung sino ang nag-ulat o nakakita. "
        "Kung pahayag lang ang basehan, gamitin ang 'ayon sa' at panatilihin ang limitasyon ng tala. "
        "Ihiwalay ang pahayag, obserbasyon at desisyon. Kapag naghahambing ng mga pangyayari "
        "sa balita, banggitin ang petsa ng bawat pangyayari at huwag ipagpalit sa petsa ng ulat. "
        + survey_guidance + "\n\n" + evidence
    )

def answer(question, previous_question="", *, diagnostics=None):
    sources = retrieve(question)
    context = ""
    followup = re.fullmatch(
        r"(?:at\s+)?(?:kailan|saan|magkano|bakit|paano)\s+(?:iyon|yun|yon|ito|'yon|’yon)\s*[?.]?",
        question.casefold(),
    )
    if not sources and followup:
        sources = retrieve(previous_question)
        if not sources:
            return "Aling pangyayari o bagay ang tinutukoy mo?", [], "clarification"
        context = (
            f"Paksa mula sa naunang tanong: {previous_question}\n"
            "Sa sumusunod na tanong, ang 'iyon' ay tumutukoy sa pangyayari o bagay sa paksa. "
            "Sagutin lamang ang kasalukuyang tanong nang direkta.\n"
        )
    if not sources:
        return "Walang sapat na tala sa ating library tungkol sa tanong na ito.", [], "no_source"

    evidence = "\n".join(
        f"[{source['id']}] {source['date'] or 'walang petsa'}: {source['note']}"
        for source in sources
    )
    prompt = grounded_prompt(sources, evidence)
    reply, _ = generate(prompt, context + question)
    if diagnostics is not None:
        diagnostics["raw_reply"] = reply
    clean = readable_reply(reply).strip()
    reason = failure(question, clean, sources)
    if reason:
        if diagnostics is not None:
            diagnostics["fallback_reason"] = reason
        intro = (
            "Hindi ko makumpirma ang kalagayan ngayon. Ito ang nakasaad sa tala:"
            if CURRENT.search(question) else "Ito ang nakasaad sa sanggunian:"
        )
        excerpts = "\n\n".join(source["note"] for source in sources)
        return f"{intro}\n\n{excerpts}", sources, "source_notes"
    return clean, sources, "generated"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("--sources", action="store_true", help="Show citations and source links.")
    args = parser.parse_args()
    reply, sources, _ = answer(args.question)
    print(reply if args.sources else readable_reply(reply))
    for source in sources if args.sources else []:
        print(format_source(source))
