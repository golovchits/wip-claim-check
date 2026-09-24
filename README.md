# Claim Check

Is this claim actually in the source? Upload a PDF and one claim. Claim Check answers **supported**, **contradicted**, **mixed** or **not found**, shows the exact source passages behind the verdict (with page numbers), and saves the result so a person can approve or reject it.

**Live:** https://wip-claim-check.onrender.com

- **The first load can take about a minute.** The free host sleeps after 15 minutes without visitors. The page appears once it has woken up.
- **Use public test documents only.** The AI runs on a free trial tier, and its data-use controls can't be switched off without a paid plan.

## Try it

Upload WIP's take-home brief (`Studio-WIP-Dev-Take-Home-Test.pdf`) and try these claims:

| Claim | Expected |
|---|---|
| Credentials must never be committed to the repo. | Supported |
| Candidates are expected to spend at least two full days on the task. | Contradicted |
| Studio WIP is headquartered in Berlin. | Not found |
| The brief recommends a 1 to 2 hour time box and says a bigger system that does not start is still acceptable. | Mixed |

The model can still get a claim wrong or return Needs review. That is what the approve / reject step is for.

## How it works

```
Browser -> FastAPI app -> Cohere API (verdict + citations)
                       -> Postgres (saved reviews)
```

1. The app reads the PDF with pypdf and splits each page into numbered passages of whole sentences.
2. It sends the claim and the passages to Cohere as documents, using our own passage IDs. Cohere's citations say which IDs back the answer.
3. An output check flags a missing verdict word, missing citations, unknown passage IDs and quotes that don't appear in the cited passages. An answer that can't be trusted is saved as **Needs review**.
4. The page shows the cited passages from our own text, never from the model's words. A reviewer approves or rejects.

More detail: `docs/ARCHITECTURE.md`, `docs/PRD.md` and `docs/DESIGN_NOTE.md`.

## Run it locally

Needs Docker Desktop and a free Cohere trial key (dashboard.cohere.com, under API Keys).

```bash
git clone https://github.com/golovchits/wip-claim-check.git
cd wip-claim-check
cp .env.example .env        # then put your Cohere key in .env
docker compose up --build
```

Open http://localhost:8000. The database table is created on first start.

**Start command:** `docker compose up --build`

## Environment variables

| Variable | Needed | Local value | Online (Render) |
|---|---|---|---|
| `COHERE_API_KEY` | yes | your trial key | set in Render's environment settings |
| `DATABASE_URL` | yes | `postgresql://postgres:postgres@db:5432/claims` (the local Docker database, already in `.env.example`) | Neon connection string |

`.env` is git-ignored. `.env.example` holds placeholders only.

## Tests

```bash
docker compose exec app python -m pytest
```

The tests cover passage splitting and the output check, using fake model answers. The test that reads WIP's brief is skipped unless you put `Studio-WIP-Dev-Take-Home-Test.pdf` in `tests/` (the PDF is not in the repo).

## Limits

- Digital PDFs only: scanned PDFs are rejected with a message. Maximum 10 MB and 50 pages.
- In a PDF that mixes text and scanned pages, the scanned pages are skipped without a warning, so a claim that only appears on them can come back as Not found.
- One claim and one document per check.
- Cohere trial: 20 calls per minute, 1,000 per month. One check uses one call.
- No login: anyone with the URL can submit and review.
- The verdict can be wrong while looking clean. That is why a person approves every result.
