-- 랩 업무일지 (공개 버전) — Supabase 스키마. SQL Editor에 그대로 붙여넣고 Run.
create table if not exists public.docs (
  collection text not null,
  id         text not null,
  data       jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (collection, id)
);
create index if not exists docs_col_date   on public.docs (collection, (data->>'date'));
create index if not exists docs_col_member on public.docs (collection, (data->>'memberId'));
create index if not exists docs_col_start  on public.docs (collection, (data->>'start'));

alter table public.docs enable row level security;
drop policy if exists "public read"   on public.docs;
drop policy if exists "public insert" on public.docs;
drop policy if exists "public update" on public.docs;
drop policy if exists "public delete" on public.docs;
create policy "public read"   on public.docs for select using (true);
create policy "public insert" on public.docs for insert with check (true);
create policy "public update" on public.docs for update using (true) with check (true);
create policy "public delete" on public.docs for delete using (true);

-- 실시간 동기화 (다른 기기에서 쓴 내용이 바로 보이게)
alter publication supabase_realtime add table public.docs;
