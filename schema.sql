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
