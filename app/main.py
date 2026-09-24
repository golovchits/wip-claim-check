from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.checker import ModelUnavailable, check_claim
from app.pdf_reader import PDFError, read_passages


@asynccontextmanager
async def lifespan(app):
    # Runs once at startup. If the database is unreachable, the app stops here.
    db.create_table()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["VERDICT_LABELS"] = {
    "supported": "Supported",
    "contradicted": "Contradicted",
    "mixed": "Mixed",
    "not_found": "Not found",
    "needs_review": "Needs review",
}


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


# Plain "def", not "async def": FastAPI runs it in a worker thread,
# so the slow model call doesn't freeze the server for other requests.
@app.post("/check")
def check(request: Request, pdf: UploadFile = File(...), claim: str = Form(...)):
    pdf_bytes = pdf.file.read()
    try:
        passages = read_passages(pdf_bytes)
        result = check_claim(claim, passages)
    except (PDFError, ModelUnavailable) as error:
        # Show the form again with one plain sentence, and keep the claim the user typed.
        return templates.TemplateResponse(
            request, "index.html", {"error": str(error), "claim": claim}, status_code=400
        )
    review_id = db.save_review(pdf.filename, pdf_bytes, claim, passages, **result)
    # 303 turns the POST into a GET, so refreshing the result page doesn't re-run the check.
    return RedirectResponse(f"/reviews/{review_id}", status_code=303)


@app.get("/reviews")
def reviews(request: Request):
    return templates.TemplateResponse(request, "reviews.html", {"reviews": db.list_reviews()})


@app.get("/reviews/{review_id}")
def review(request: Request, review_id: int):
    found = db.get_review(review_id)
    if found is None:
        raise HTTPException(404, "Review not found")
    # Cited passages always come from our own stored list, never from the model's text.
    cited = [p for p in found["passages"] if p["id"] in found["cited_ids"]]
    return templates.TemplateResponse(request, "review.html", {"review": found, "cited": cited})


@app.post("/reviews/{review_id}/decision")
def decide(review_id: int, decision: str = Form(...), note: str = Form("")):
    if decision not in ("approved", "rejected"):
        raise HTTPException(400, "Decision must be approved or rejected")
    db.set_decision(review_id, decision, note)
    return RedirectResponse(f"/reviews/{review_id}", status_code=303)


@app.get("/health")
def health():
    try:
        with db.connect() as conn:
            conn.execute("SELECT 1")
        return {"db": "ok"}
    except psycopg.Error:
        return JSONResponse({"db": "error"}, status_code=503)
