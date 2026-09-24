# Architecture

How the parts fit together. Every part exists because a user need requires it.

## 01 System overview
```
                Browser (plain HTML page)
                         |
                         v
        +----------------------------------+
        |  Web app: FastAPI (Python)       |
        |  - reads PDF (pypdf)             |
        |  - splits into numbered passages |
        |  - checks the model's answer     |
        +----------------------------------+
              |                      |
              v                      v
      Cohere API               Postgres
      (document citations)     (reviews, PDFs, status)
      service 1                service 2
```
Local / fresh machine: `docker compose up` starts the app + a Postgres container.
Online: the same app runs on Render and talks to Neon (hosted Postgres).

## 02 Why each part exists
| Need | Part | Why this one |
|---|---|---|
| Upload a PDF and a claim | FastAPI web app | small, Python, serves the HTML page too |
| Judge the claim with citations | Cohere API, document citations | free trial with fixed limits, the API itself marks which passage IDs back each part of the answer. Mistral was the first choice, its free tier blocked the model (see the design note) |
| Save reviews for a human | Postgres | survives restarts, separate service. SQLite runs inside the app and Render wipes its disk |
| WIP can open it | Render | free, runs Docker, no card |
| Database online | Neon | free Postgres, never deleted (Render's free DB is deleted after 30 days) |
| Hold the PDF | Postgres column | no extra account. Production: move to R2 |

Rejected: n8n (a whole app for one notification), vector DB (one document fits in the prompt), R2 (card needed, not needed at this size), React (a second app to build and explain).

## 03 Tech stack
| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Web | FastAPI + Jinja2 templates + uvicorn + python-multipart (needed for file uploads) |
| PDF | pypdf |
| Database | Postgres 16, `psycopg[binary]` 3 (binary build, so the image needs no system Postgres libraries), plain SQL |
| LLM | Cohere API, `command-a-plus-05-2026`, official `cohere` SDK (v2 client), document citations in FAST mode |
| Tests | pytest (only for passage splitting and the output check) |
| Run | Docker + Docker Compose |
| Host | Render (app), Neon (database) |

## 04 Project structure
```
claim-check/
├── app/
│   ├── main.py          # routes: pages, upload, review decisions, health
│   ├── pdf_reader.py    # PDF -> page texts -> numbered passages
│   ├── checker.py       # calls Cohere, runs the output check
│   ├── db.py            # connect, create table, save and load reviews
│   ├── templates/       # index.html, review.html, reviews.html
│   └── static/style.css
├── tests/               # test_pdf_reader.py, test_checker.py
├── docs/                # PRD, ARCHITECTURE, DESIGN_NOTE
├── schema.sql           # the one table
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example         # placeholders only
├── .gitignore           # includes .env
├── CLAUDE.md
└── README.md
```

## 05 Data flow
1. User uploads a PDF and types a claim.
2. `pdf_reader` extracts text per page. Empty text means scanned PDF: stop with a clear message.
3. `pdf_reader` joins each page's lines, splits them into sentences (at ". ", "? ", "! " and before bullets "•"), and packs whole sentences into passages of up to about 500 characters. Passages never cross a page. Each gets an ID and page number: `[{id: 1, page: 1, text: "..."}]`.
4. `checker` makes one Cohere chat call:
   a. the claim, plus our passages as documents with our own IDs: `[{"id": "1", "data": {"title": "page 1", "snippet": "..."}}, ...]`, and `citation_options={"mode": "FAST"}`
   b. the reply is the answer text plus a list of citations. Each citation names the document IDs (our passage IDs) behind a span of the answer. The prompt tells the model to start with one verdict word: SUPPORTED, CONTRADICTED, MIXED or NOT_FOUND.
5. `checker` runs the output check (section 07).
6. `db` saves everything with status `pending`.
7. The page shows the verdict, the cited passages from our own list, and any flags. `needs_review` shows as "Needs review" with the reason.
8. A reviewer approves or rejects. Status becomes `approved` or `rejected`.

## 06 Data model (one table)
```sql
CREATE TABLE IF NOT EXISTS reviews (
  id            SERIAL PRIMARY KEY,
  created_at    TIMESTAMPTZ DEFAULT now(),
  filename      TEXT,
  pdf           BYTEA,
  claim         TEXT NOT NULL,
  passages      JSONB,        -- our numbered passages
  verdict       TEXT,         -- supported | contradicted | mixed | not_found | needs_review
  explanation   TEXT,
  cited_ids     JSONB,
  flags         JSONB,        -- output-check warnings
  status        TEXT DEFAULT 'pending',   -- pending | approved | rejected
  reviewer_note TEXT
);
```

## 07 The output check
The passages we show always come from our own list, so the model can only point at a source, never invent one. What can still go wrong, and what the code does:
| Problem | Check |
|---|---|
| Answer does not start with a valid verdict word | verdict `needs_review` |
| Answers with no citations | for SUPPORTED, CONTRADICTED or MIXED: verdict `needs_review`, flag "no citations". A NOT_FOUND with no citations is accepted (an honest "not found" has nothing to cite) |
| Cites an ID that does not exist | drop it, flag "unknown passage ID" |
| Writes a quote that is not in the cited passages | a quote (text in quotation marks in the answer) passes if it appears in ANY passage the answer cites, after normalising spaces and case and ignoring trailing punctuation inside the quote. Otherwise flag "unverified quote". Chosen because matching each quote to one exact citation span is stricter than the reviewer needs |
| Cites a real passage that does not support the claim | cannot be caught by code, this is why a human approves |
| Malformed reply, times out (45 s) or errors | save verdict `needs_review`, never crash |
| Rate limit or rejected API key | show a plain message on the form and save nothing: the claim was never checked, and retrying is the fix |

## 08 Environments and secrets
| Variable | Local | Render |
|---|---|---|
| `COHERE_API_KEY` | in `.env` | Render environment settings |
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/claims` | Neon connection string (`sslmode=require`) |

Only `.env.example` is committed. Nothing logs keys, request bodies or PDF text.

## 09 Limits and failure messages
| Case | Behaviour |
|---|---|
| Not a PDF / over 10 MB / over 50 pages | reject with a plain message |
| Scanned PDF (no text) | "Looks like a scanned PDF, not supported yet" |
| Cohere rate limit (trial: 20 calls/min, 1,000/month) | "Too many requests, try again in a minute" |
| Database down | `/health` reports it, upload shows an error |
| Render asleep | first load takes about a minute (README says so) |
