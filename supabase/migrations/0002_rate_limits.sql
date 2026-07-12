-- 0002_rate_limits.sql — per-session + global daily rate-limit counters (Phase 6).
-- Paste into the Supabase SQL editor and run (same as 0001_init.sql).

create table if not exists rate_limits (
  key         text not null,                                   -- session id (sid), or 'global'
  kind        text not null,                                   -- 'session' | 'global'
  window_date date not null default (now() at time zone 'utc')::date,
  count       int  not null default 0,
  updated_at  timestamptz not null default now(),
  primary key (key, kind, window_date)
);

-- Backend uses the service-role key (bypasses RLS); no public/anon access to counters.
alter table rate_limits enable row level security;

-- Atomic check-and-consume. Reads today's session + global counts; if under both
-- caps, reserves a slot by incrementing both and returns allowed=true. Limits are
-- passed in by the app from env, so caps change with no migration/redeploy.
create or replace function check_rate_limit(
  p_session_key  text,
  p_session_limit int,
  p_daily_limit   int
) returns table(allowed boolean, limit_hit text)
language plpgsql
as $$
declare
  v_today   date := (now() at time zone 'utc')::date;
  v_session int;
  v_global  int;
begin
  select count into v_session from rate_limits
    where key = p_session_key and kind = 'session' and window_date = v_today;
  v_session := coalesce(v_session, 0);

  select count into v_global from rate_limits
    where key = 'global' and kind = 'global' and window_date = v_today;
  v_global := coalesce(v_global, 0);

  if v_session >= p_session_limit then
    return query select false, 'session'::text;
    return;
  end if;
  if v_global >= p_daily_limit then
    return query select false, 'daily'::text;
    return;
  end if;

  -- Under both caps: reserve a slot by incrementing both counters for today.
  insert into rate_limits (key, kind, count) values (p_session_key, 'session', 1)
    on conflict (key, kind, window_date)
    do update set count = rate_limits.count + 1, updated_at = now();

  insert into rate_limits (key, kind, count) values ('global', 'global', 1)
    on conflict (key, kind, window_date)
    do update set count = rate_limits.count + 1, updated_at = now();

  return query select true, null::text;
end;
$$;
