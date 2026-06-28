-- Me-as-a-Service — Slice 1 schema
-- Run this in the Supabase SQL Editor (or via the Supabase CLI).
-- Implements TECHNICAL_SPEC.md §4.1 (documents) and §5 (hybrid_search RPC).
-- RLS is intentionally deferred to a later slice; the backend uses the
-- service-role key, which bypasses RLS.

-- 1) pgvector extension --------------------------------------------------------
create extension if not exists vector;

-- 2) documents table -----------------------------------------------------------
create table if not exists documents (
  id          bigserial primary key,
  source_file text  not null,
  title       text,
  content     text  not null,
  metadata    jsonb not null default '{}'::jsonb,
  embedding   vector(1024) not null,            -- voyage-3
  fts         tsvector generated always as
                (to_tsvector('english', coalesce(title, '') || ' ' || content)) stored,
  created_at  timestamptz not null default now()
);

-- 3) indexes -------------------------------------------------------------------
-- Semantic (cosine) ANN index.
create index if not exists documents_embedding_idx
  on documents using hnsw (embedding vector_cosine_ops);

-- Lexical (BM25-style) full-text index.
create index if not exists documents_fts_idx
  on documents using gin (fts);

create index if not exists documents_source_file_idx
  on documents (source_file);

-- 4) hybrid_search RPC ---------------------------------------------------------
-- Combines a semantic leg (vector cosine distance) and a lexical leg
-- (full-text ts_rank) using Reciprocal Rank Fusion (RRF):
--   score(d) = Σ_legs 1 / (rrf_k + rank_leg(d))
-- query_embedding is accepted as a pgvector value; the backend passes it as the
-- bracketed string form (e.g. '[0.1,0.2,...]'), which pgvector parses.
create or replace function hybrid_search(
  query_text       text,
  query_embedding  vector(1024),
  match_count      int default 5,
  rrf_k            int default 60,
  candidate_count  int default 20
)
returns table (
  id          bigint,
  source_file text,
  title       text,
  content     text,
  metadata    jsonb,
  score       double precision
)
language sql
stable
as $$
  with vec as (
    select d.id,
           row_number() over (order by d.embedding <=> query_embedding) as rank
    from documents d
    order by d.embedding <=> query_embedding
    limit candidate_count
  ),
  fts as (
    select d.id,
           row_number() over (
             order by ts_rank(d.fts, websearch_to_tsquery('english', query_text)) desc
           ) as rank
    from documents d
    where d.fts @@ websearch_to_tsquery('english', query_text)
    limit candidate_count
  )
  select
    d.id,
    d.source_file,
    d.title,
    d.content,
    d.metadata,
    ( coalesce(1.0 / (rrf_k + vec.rank), 0.0)
    + coalesce(1.0 / (rrf_k + fts.rank), 0.0) )::double precision as score
  from vec
  full outer join fts on vec.id = fts.id
  join documents d on d.id = coalesce(vec.id, fts.id)
  order by score desc
  limit match_count;
$$;
