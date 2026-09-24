import os
import re

import cohere

MODEL = "command-a-plus-05-2026"
TIMEOUT_SECONDS = 45
VERDICTS = {"SUPPORTED", "CONTRADICTED", "MIXED", "NOT_FOUND"}


class ModelUnavailable(Exception):
    """The claim was never checked, so nothing is saved. The message is shown to the user as is."""


SYSTEM_PROMPT = (
    "You check whether a claim is backed by the provided documents. Use only the documents. "
    "Start your answer with exactly one word: SUPPORTED, CONTRADICTED, MIXED or NOT_FOUND. "
    "MIXED means part of the claim is right and part is wrong. Then explain in two or three sentences. "
    "If you quote a document, copy the words exactly and put them in double quotes."
)


def check_claim(claim, passages):
    try:
        client = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"], timeout=TIMEOUT_SECONDS)
        # Our passages go in as documents with our own IDs, so Cohere's citations point back at them.
        documents = [
            {"id": str(p["id"]), "data": {"title": f"page {p['page']}", "snippet": p["text"]}}
            for p in passages
        ]
        response = client.chat(
            model=MODEL,
            documents=documents,
            # FAST cited reliably in testing, the default sometimes returned no citations. ACCURATE is not offered for this model.
            citation_options={"mode": "FAST"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Claim: {claim}"},
            ],
        )
        text = "".join(item.text for item in response.message.content if item.type == "text")
        cited = [source.id for citation in (response.message.citations or []) for source in citation.sources]
    except cohere.TooManyRequestsError:
        raise ModelUnavailable("Too many requests, try again in a minute.")
    except cohere.UnauthorizedError:
        raise ModelUnavailable("The AI service refused the API key. Check the server configuration.")
    except Exception as error:
        # Timeouts, other API errors and malformed replies are saved as needs_review, so the app never crashes.
        return {
            "verdict": "needs_review",
            "explanation": "",
            "cited_ids": [],
            "flags": [f"model error: {type(error).__name__}"],
        }
    return run_output_check(text, cited, passages)


def normalise(text):
    return " ".join(text.split()).lower()


def parse_verdict(text):
    # Strip Markdown bold and a leading "Verdict:" before reading the first word.
    cleaned = text.replace("**", "").strip()
    cleaned = re.sub(r"^verdict\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    parts = cleaned.split(maxsplit=1)
    if not parts:
        return None, ""
    # strip("_*.:,") removes _italic_ marks and trailing punctuation, but keeps NOT_FOUND's inner "_".
    word = parts[0].strip("_*.:,").upper()
    explanation = parts[1].strip() if len(parts) > 1 else ""
    if word not in VERDICTS:
        return None, cleaned
    return word.lower(), explanation


def run_output_check(text, reference_ids, passages):
    flags = []
    verdict, explanation = parse_verdict(text)
    if verdict is None:
        verdict = "needs_review"
        flags.append("missing verdict word")

    known = {str(p["id"]): p for p in passages}
    cited_ids = []
    for ref in map(str, reference_ids):
        if ref not in known:
            flags.append(f"unknown passage ID: {ref}")
        elif int(ref) not in cited_ids:
            cited_ids.append(int(ref))

    # An honest NOT_FOUND has nothing to cite, so only the other verdicts need citations.
    if not cited_ids and verdict in ("supported", "contradicted", "mixed"):
        verdict = "needs_review"
        flags.append("no citations")

    # A quote passes if it appears in ANY cited passage (straight or curly quotes).
    # Trailing punctuation is ignored: models often end a quote with "," or "." the source doesn't have there.
    cited_texts = [normalise(known[str(i)]["text"]) for i in cited_ids]
    for quote in re.findall(r'["“]([^"“”]+)["”]', explanation):
        if not any(normalise(quote).rstrip(".,;:") in passage for passage in cited_texts):
            flags.append(f"unverified quote: {quote}")

    return {"verdict": verdict, "explanation": explanation, "cited_ids": cited_ids, "flags": flags}
