# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

# Project rules: Claim Check (Studio WIP take-home)

## Read first
- docs/PRD.md for what we build and why
- docs/ARCHITECTURE.md for the parts and how they connect
- docs/BUILD_PLAN.md for the current step
- docs/DESIGN_SYSTEM.md before touching the page

## How to work with me (Dima)
- One BUILD_PLAN step at a time. Do not start the next step until I say so.
- Before writing code for a step, say in 3 to 5 lines what you will write and why.
- After each step, explain what the code does in plain words, then show me how to verify it.
- I must be able to explain every line to a reviewer. Prefer boring, readable code over clever code.
- If a step would need a new library, service or file not in ARCHITECTURE.md, stop and ask.

## Hard rules
- Secrets only come from environment variables. Never write a key into code, docs, tests or logs.
- `.env` stays git-ignored. `.env.example` has placeholders only.
- Never log request bodies, PDF text or API keys.
- Plain SQL with psycopg. No ORM.
- One plain HTML page with Jinja2 templates. No React, no build step, no JS framework.
- Keep the total code small. If a file passes about 150 lines, tell me.
