"""Deterministic checks for factual drafts backed by the local library."""
import re

CURRENT = re.compile(
    r"\b(?:ngayon\w*|pinakabago\w*|latest|kasalukuyan\w*|today|currently|"
    r"right now|as of now|this week|ngayong linggo|still open|"
    r"(?:bukas|open|tapos|kumpleto|operational)\s+(?:na|pa(?:\s+rin)?)\s+ba)\b", re.I
)
STATUS = re.compile(
    r"\b(?:(?:bukas|open|tapos|completed?|operational|gumagana|sarado|closed)"
    r"\s+(?:na|pa(?:\s+rin)?|ngayon|today|currently)|"
    r"(?:kasalukuyang|currently|still|already)\s+(?:bukas|open|tapos|completed?|operational|closed)|"
    r"(?:bukas|sarado|tapos)\s+(?:ito|ang)|(?:is|are)\s+(?:open|closed|complete|operational))\b",
    re.I,
)
QUALIFIED = re.compile(
    r"\b(?:hindi\s+(?:ko\s+)?(?:makumpirma|matitiyak|malinaw|sinasabi|nabanggit)|"
    r"walang\s+(?:tala|impormasyon|kumpirmasyon|datos)|hindi\s+nakasaad|"
    r"cannot confirm|can.t confirm|unclear whether|no confirmation|no information)\b", re.I
)
HISTORICAL = re.compile(r"\b(?:noong|as of|in)\s+(?:[\w,]+\s+){0,3}(?:19|20)\d{2}\b", re.I)
PRESENT = re.compile(r"\b(?:ngayon\w*|today|kasalukuyan\w*|currently|still|pa rin|already)\b", re.I)
NUMBER = re.compile(r"(?<!\w)\d+(?:,\d{3})*(?:\.\d+)?(?!\w)")
DISASTER_ALLOCATION = re.compile(r"quick response fund|(?:disaster fund|ldrrmf).*porsiyento", re.I)
DISASTER_PERCENTAGES = {
    "5": re.compile(r"(?<![\w.,])5(?:\.0+)?\s*(?:%|porsiyento\b|percent\b)", re.I),
    "30": re.compile(r"(?<![\w.,])30(?:\.0+)?\s*(?:%|porsiyento\b|percent\b)", re.I),
}
# Each rule binds a question cue to a source and the facts that cue requests.
ANCHORS = (
    ({"H14", "P153"}, r"edad|katanda|ilang taon|gaano na katagal|709[ ,]?000", ("709000",)),
    ({"N8"}, r"ilang kama|ilang bed|kapasidad|500\s*(?:kama|bed)", ("250",)),
    ({"N8"}, r"iminungkahi|panukala|propos", ("500",)),
    ({"G6"}, r"anong batas|aling batas|what law|statute", ("12000",)),
    ({"P125"}, r"anong batas|aling batas|what law|statute", ("9237",)),
    ({"P151"}, r"kailan|anong taon|petsa", ("2025",)),
    ({"G2", "G9", "C4"}, r"kailan.*(?:ratipika|pinagtibay)|(?:ratipika|pinagtibay).*kailan", ("1987",)),
)


def numbers(text):
    return {match.replace(",", "") for match in NUMBER.findall(text)}


def failure(question, reply, sources):
    question_numbers = numbers(question)
    reply_numbers = numbers(reply)
    notes = " ".join(source["note"] for source in sources)
    source_numbers = numbers(notes)
    ids = {source["id"] for source in sources}
    required = set()
    allocation = "P145" in ids and DISASTER_ALLOCATION.search(question)
    if re.search(r"\b(?:edad|katanda|ilang|kailan|magkano|petsa|batas|statute)\b", question, re.I):
        required.update(question_numbers & source_numbers)
    if allocation:
        # The question identifies the law. The answer needs the allocation figures.
        required.discard("10121")
        asks_quick_response = re.search(r"quick response fund", question, re.I)
        asks_minimum = re.search(r"regular na kita|minimum|pareho|both", question, re.I)
        percentages = ("5", "30") if asks_quick_response and asks_minimum else (
            ("30",) if asks_quick_response else ("5",)
        )
        if any(not DISASTER_PERCENTAGES[value].search(reply) for value in percentages):
            return "missing_required_fact"
    for source_ids, cue, values in ANCHORS:
        if ids & source_ids and re.search(cue, question, re.I):
            required.update(set(values) & source_numbers)

    current = CURRENT.search(question)
    if current and not any(source.get("current_status_verified") is True for source in sources):
        for clause in re.split(r"[.!?\n;]+|\b(?:pero|ngunit|but)\b", reply, flags=re.I):
            status = STATUS.search(clause)
            if not status:
                continue
            before = clause[:status.start()]
            qualifier = QUALIFIED.search(before)
            scoped_uncertainty = qualifier and re.search(
                r"\b(?:kung|whether|if)\b", before[qualifier.end():], re.I
            )
            dated = HISTORICAL.search(clause) and not PRESENT.search(clause)
            if not (scoped_uncertainty or dated):
                return "unsupported_current_status"
        if not QUALIFIED.search(reply):
            return "missing_current_status_limit"
    if required - reply_numbers:
        return "missing_required_fact"
    return None
