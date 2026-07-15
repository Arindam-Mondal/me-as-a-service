-- 0003_leads.sql — lead capture from the "Let's connect" form (Phase 7).
-- Paste into the Supabase SQL editor and run (same as 0001_init.sql / 0002_rate_limits.sql).

create table if not exists leads (
  id                   bigserial primary key,
  name                 text not null,
  email                text not null,
  message              text,
  conversation_context jsonb not null default '[]',
  status               text not null default 'new',   -- new | read | handled
  created_at           timestamptz not null default now()
);

-- Newest-first listing (for a future /admin view).
create index if not exists leads_created_at_idx on leads (created_at desc);

-- Leads are PII: enable RLS with NO policies so the anon key can neither read nor
-- write them. The backend inserts with the service-role key, which bypasses RLS.
alter table leads enable row level security;
