"""Local interactive entry point for Philippine reference Q&A and Tagalog practice."""
import argparse
import json
import re
from pathlib import Path

from ask import SOURCE_REQUEST, answer, format_source, readable_reply, source_reply
from pilot import APP, GEMMA_PORT, SOURCES, generate, lookup_text, retrieve


def market_total(turns):
    """Calculate totals for explicit whole-peso, per-kilo shopping scenarios."""
    if not re.search(r"\bmagkano\b.*\b(?:lahat|kabuuan)\b", turns[-1], re.I):
        return ""
    quantities, prices = {}, {}
    numbers = {"isang": 1, "dalawang": 2, "tatlong": 3, "apat na": 4, "limang": 5}
    for turn in turns:
        for amount, item in re.findall(
            r"\b(isang|dalawang|tatlong|apat na|limang|[0-9]+) kilo ng (\w+)", turn.lower()
        ):
            quantities[item] = int(amount) if amount.isascii() and amount.isdigit() else numbers[amount]
        for amount, item in re.findall(
            r"\b([0-9]+) pesos kada kilo ang (\w+)", turn.lower()
        ):
            prices[item] = int(amount)
        for amount, item in re.findall(r"\bat ([0-9]+) ang (\w+)", turn.lower()):
            if "pesos kada kilo" in turn.lower():
                prices[item] = int(amount)
    if not quantities or quantities.keys() != prices.keys():
        return ""
    subtotals = [f"{qty} kilo ng {item}, {qty * prices[item]:,} pesos"
                 for item, qty in quantities.items()]
    total = sum(qty * prices[item] for item, qty in quantities.items())
    return f"{'; '.join(subtotals)}. {total:,} pesos lahat."


def practice_prompt():
    baseline = (APP / "system-prompt.txt").read_text(encoding="utf-8-sig")
    return baseline + (
        "\nSa language practice at roleplay, sundan ang papel na ibinigay ng user. "
        "Manatili sa natural na Tagalog o Taglish. Sa roleplay, kapag may binago ang user, "
        "iyon lang ang palitan. Sa pagkumpirma ng plano, isama ang araw, oras, lugar at "
        "dadalhin kung nabanggit. Ituring na bayad na ang sinabing bayad na. "
        "Kung hinihingi ang kabuuang presyo, imultiply ang dami sa presyo kada yunit "
        "para sa bawat item, saka pagsamahin ang mga subtotal. Banggitin ang mga item "
        "at subtotal para madaling masuri ang kuwenta."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, help="Save information questions, answers and their sources to a new JSONL file.")
    args = parser.parse_args()
    if args.log:
        try:
            with args.log.open("x", encoding="utf-8"):
                pass
        except OSError as error:
            parser.error(str(error))
    conversation_prompt = practice_prompt()
    culture = json.loads((APP / "tagallm-culture-references.json").read_text(encoding="utf-8-sig"))
    mode = "ask"
    history = []
    roleplay_turns = []
    lookups = []
    previous_question = ""
    print("TagaLLM · /ask para sa impormasyon · /chat para sa practice · /topics · /sources · /quit")
    while True:
        try:
            question = input(f"{mode}> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question == "/quit":
            break
        if question == "/topics" or question.startswith("/topics "):
            topic = question[len("/topics"):].strip().casefold()
            if not topic:
                for name in sorted({source["topic"] for source in SOURCES}):
                    print(f"{name}: {sum(source['topic'] == name for source in SOURCES)}")
                print("Gamitin ang /topics culture o ibang paksa para makita ang mga sanggunian.")
            else:
                matches = [source for source in SOURCES if source["topic"] == topic]
                if not matches:
                    print("Tingnan ang mga paksa sa /topics.")
                for source in matches:
                    print(format_source(source))
            continue
        if question == "/lookups":
            for number, (prompt, _, _) in enumerate(lookups, start=1):
                print(f"{number}. {prompt}")
            continue
        if question == "/sources" or question.startswith("/sources "):
            selection = question[len("/sources"):].strip()
            number = len(lookups)
            if selection:
                try:
                    number = int(selection)
                except ValueError:
                    number = 0
            if not 1 <= number <= len(lookups):
                print("Pumili ng numero mula sa /lookups.")
                continue
            _, _, sources = lookups[number - 1]
            print(source_reply(sources))
            continue
        if question in ("/ask", "/chat"):
            mode = question[1:]
            continue
        if not question:
            continue
        if len(question) > 1000:
            print("Hanggang 1,000 character lang bawat mensahe.")
            continue
        try:
            if mode == "ask":
                if SOURCE_REQUEST.fullmatch(question):
                    print(source_reply(lookups[-1][2] if lookups else []))
                    continue
                reply, sources, status = answer(question, previous_question)
                if args.log:
                    row = dict(question=question, answer=reply, status=status, sources=sources,
                               previous_question=previous_question)
                    try:
                        with args.log.open("a", encoding="utf-8") as log:
                            log.write(json.dumps(row, ensure_ascii=False) + "\n")
                    except OSError as error:
                        print(f"Hindi na-save ang sagot sa log ({error}).")
                if not sources or retrieve(question):
                    previous_question = question if sources else ""
                lookups.append((question, reply, sources))
                print(readable_reply(reply))
            else:
                normalized = lookup_text(question)
                references = [
                    entry["text"] for entry in culture
                    if any(re.search(r"(?<!\w)" + re.escape(lookup_text(alias)) + r"(?!\w)", normalized)
                           for alias in entry["aliases"])
                ]
                prompt = conversation_prompt
                if references:
                    prompt += "\nGamitin ang nauugnay na sanggunian sa tanong tungkol sa kultura:\n" + "\n".join(references)
                if re.search(r"^(?:ikaw ang|kunwari\b|mag[- ]?roleplay\b)", question, re.I):
                    roleplay_turns = [question]
                elif roleplay_turns:
                    roleplay_turns = (roleplay_turns + [question])[-12:]
                if roleplay_turns:
                    prompt += (
                        "\nMga sinabi mismo ng user sa roleplay, mula una hanggang pinakahuli. "
                        "Sundin ang pinakabagong pagbabago at panatilihin ang ibang detalye:\n"
                        + "\n".join(roleplay_turns)
                        + "\nKapag tinanong kung ano na ang buong plano, sabihin pati ang araw "
                        "kahit oras o lugar lang ang binago. Kung inutusan kang magdala ng "
                        "gamit, ikaw ang magdadala: 'Dadalhin ko ang payong mo.' "
                        "Kapag may listahan ng ipapakomperma, sagutin ang bawat detalye sa listahan."
                    )
                reply = market_total(roleplay_turns) if roleplay_turns else ""
                if not reply:
                    reply, _ = generate(prompt, question, history)
                history.extend([{"role": "user", "content": question},
                                {"role": "assistant", "content": reply}])
                history = history[-6:]
                print(reply)
        except OSError as error:
            print(f"Hindi makasagot ang lokal na Gemma server. Suriin ang port {GEMMA_PORT} ({error}).")


if __name__ == "__main__":
    main()
