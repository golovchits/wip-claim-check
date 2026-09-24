# Claim Check design note

## What I built, and why this problem
Models sound as sure when they are wrong as when they are right, and a confident wrong claim in a founder report costs more than a slow check. Claim Check takes a PDF and a claim, answers supported, contradicted, mixed or not found, and shows the passages behind the answer. The model can cite passages but never write them. My code splits the PDF into numbered passages and shows only those, then checks that cited passages exist, that quotes appear in them and that the answer starts with a verdict. A missing verdict or missing citations sends the answer to Needs review, an unknown ID or unverified quote shows a warning next to the verdict, and a person approves every result.

## Services I chose, and what I rejected
Cohere judges the claim, and its citations point back at my passage IDs. Mistral was the plan, but its free API refused every call to the model I needed, and the best Mistral model I could reach scored 6 of 8 against Cohere's 8. Postgres keeps each review for the person approving it. I rejected SQLite because Render wipes its disk, and Render's own database because it is deleted after 30 days, so the live app uses Neon. I left out a vector database because one document fits in a single request.

## Secrets and failure
Keys come only from environment variables, and .env is ignored. The app never logs keys or PDF text and will not start without its database. Fully scanned PDFs, oversized files, timeouts and rate limits end in a plain message or in Needs review, never a crash.

## Where AI helped, and what it got wrong
AI wrote most of the code, one step at a time, and I checked each step. Twice it trusted an assumption over the data. It planned to split the PDF into paragraphs, but pypdf returned the brief with no paragraph breaks at all. Its fix, packing whole lines, would have cut sentences in half and failed correct quotes, so I packed whole sentences. Later, after 2 models returned no citations, it concluded that only Mistral's small model supports them. I doubted a rule drawn from 2 cases, so we tested every model the key could call. Ministral 3B did return citations, the markers that point back at my passage IDs. It scored 3 of 8, so I switched to Cohere because it scored higher, not because of the false rule.

## What I cut, and what I would harden
I cut OCR, login and long documents. For production I would add login, since anyone with the link can now approve results. Before real transcripts go in, I would move to a paid tier that does not train on your data and run it in your Compose stack behind Tailscale, so it is not on the public internet. PDFs would move to R2, which is built for files, and Postgres would keep only the reference.

## One tradeoff I'm still unsure about
How strict the verdicts should be. All 8 runs on the 4 claims I tuned on were right. On 4 new claims, run once with nothing changed, 2 were right and 1 went to Needs review with the right reasoning but no citations. The fourth was "WIP uses Kubernetes". The brief never mentions Kubernetes, so I expected not found. The model said contradicted and cited the passage on your Docker Compose setup, reading it as ruling Kubernetes out. Its verdict and citations were well formed, and my code flagged nothing. So the 8 of 8 overstated its accuracy. A strict rule misses fair inferences like that. A loose one accepts them, so the reviewer has to check the reasoning more often. I chose loose and rely on the person approving each result, but I'm not sure that is the rule you would choose.