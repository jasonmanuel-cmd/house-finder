-- Private seller lead system: leads table (one row per scraped lead).
-- Owner names are private data; this table lives in the private Harbison
-- Supabase project and is only readable through the token-authenticated API.

create table if not exists private_seller_leads (
  id text primary key,
  address text not null default '',
  city text not null default '',
  price integer not null default 0,
  price_text text not null default '',
  source text not null default '',
  source_type text not null default '',
  link text not null default '',
  description text not null default '',
  owner_name text not null default '',
  owner_mailing text not null default '',
  motivation text not null default '',
  deal_score integer not null default 0,
  equity_estimate text not null default '',
  status text not null default 'new',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  raw_data text not null default ''
);

-- No RLS policy for anon: the table must never be publicly readable.
-- Access is service-role only, through the dashboard API with ADMIN_TOKEN.
alter table private_seller_leads enable row level security;

create index if not exists private_seller_leads_score_idx on private_seller_leads (deal_score desc);
create index if not exists private_seller_leads_source_idx on private_seller_leads (source);
create index if not exists private_seller_leads_status_idx on private_seller_leads (status);

-- Bulk upsert used by scripts/sync_to_supabase.py (service role only).
create or replace function upsert_private_seller_leads(payload json)
returns void
language plpgsql
security definer
as $$
begin
  insert into private_seller_leads (id, address, city, price, price_text, source,
                                    source_type, link, description, owner_name,
                                    owner_mailing, motivation, deal_score,
                                    equity_estimate, status, created_at, updated_at,
                                    raw_data)
  select
    r->>'id', r->>'address', coalesce(r->>'city', ''), coalesce((r->>'price')::int, 0),
    coalesce(r->>'price_text', ''), coalesce(r->>'source', ''), coalesce(r->>'source_type', ''),
    coalesce(r->>'link', ''), coalesce(r->>'description', ''), coalesce(r->>'owner_name', ''),
    coalesce(r->>'owner_mailing', ''), coalesce(r->>'motivation', ''), coalesce((r->>'deal_score')::int, 0),
    coalesce(r->>'equity_estimate', ''), coalesce(r->>'status', 'new'),
    coalesce((r->>'created_at')::timestamptz, now()), coalesce((r->>'updated_at')::timestamptz, now()),
    coalesce(r->>'raw_data', '')
  from json_array_elements(payload) as r
  on conflict (id) do update set
    address = excluded.address,
    city = excluded.city,
    price = excluded.price,
    price_text = excluded.price_text,
    source = excluded.source,
    source_type = excluded.source_type,
    link = excluded.link,
    description = excluded.description,
    owner_name = excluded.owner_name,
    owner_mailing = excluded.owner_mailing,
    motivation = excluded.motivation,
    deal_score = excluded.deal_score,
    equity_estimate = excluded.equity_estimate,
    status = case when private_seller_leads.status = 'new' then 'new' else private_seller_leads.status end,
    updated_at = excluded.updated_at,
    raw_data = excluded.raw_data;
end;
$$;

revoke all on function upsert_private_seller_leads(json) from anon, authenticated;
