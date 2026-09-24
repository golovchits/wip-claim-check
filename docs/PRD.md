# PRD: Claim Check

A clear plan for what we build, why it matters, and how we know it works.

## 01 Product overview
| | |
|---|---|
| **Name** | Claim Check |
| **Tagline** | Is this claim actually in the source? |
| **Description** | Upload a PDF and a claim. Get a verdict with the exact passages behind it. A person approves or rejects the result. |

## 02 Problem
Studio WIP writes reports from founder conversations, transcripts and documents. A claim in a report can drift from what the source actually says. Checking by hand means rereading the whole source.

## 03 Goal
In under a minute, show a reviewer whether a claim is supported, contradicted, mixed or not found, and point to the passages that decide it. The human keeps the final say.

## 04 Target users
- WIP sprint team members writing strategic outputs
- The person reviewing those outputs before they go to a founder

> **User need:** "Before this goes out, show me where in the source this claim comes from, so I don't have to reread 40 pages."

## 05 Core features (must have)
| # | Feature | What it does |
|---|---|---|
| 1 | Upload | PDF (digital, text layer) plus one claim |
| 2 | Verdict | supported, contradicted, mixed or not found, with a short explanation. If the model's answer can't be trusted (no verdict word, no citations, error) it shows "Needs review" with the reason |
| 3 | Cited passages | the numbered source passages the verdict relies on, shown from our own text with page numbers |
| 4 | Output check | flags missing citations, cited IDs that don't exist, quotes not in the cited passage, and a missing verdict word |
| 5 | Human review | list of saved reviews, approve or reject with a note |
| 6 | Clear failures | scanned PDF, too large, model error or rate limit each give a plain message |

## 06 Later (only if time is left)
- OCR for scanned PDFs (OCRmyPDF / Tesseract)

## 07 Out of scope
- Accounts and login
- Several claims or documents at once
- Very long documents (chunked processing)

## 08 Success criteria
- A fresh machine runs it with one command: `docker compose up`
- The live URL on Render works end to end
- A known true, false, absent and half-true claim each get the right verdict on WIP's take-home brief:
  - "Credentials must never be committed to the repo." -> supported
  - "Candidates are expected to spend at least two full days on the task." -> contradicted
  - "Studio WIP is headquartered in Berlin." -> not found
  - "The brief recommends a 1 to 2 hour time box and says a bigger system that does not start is still acceptable." -> mixed
- No secret anywhere in the repo, image or logs
