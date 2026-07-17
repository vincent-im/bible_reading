-- 예본6여 성경통독 · 공용 DB 스키마 (공유 암호 보호)
-- ─────────────────────────────────────────────────────────────
-- 사용법:
--   1) Supabase 대시보드 → 프로젝트(Bible_reading) → SQL Editor
--   2) 아래 전체를 붙여넣기
--   3) '여기에_공유암호' 를 순원들과 공유할 실제 암호로 바꾸기 (따옴표는 유지)
--   4) Run
--
-- 동작: 앱은 접속 시 공유 암호를 입력받아 요청 헤더(x-app-key)로 보냅니다.
--       아래 RLS 정책이 그 헤더가 공유 암호와 일치할 때만 데이터 접근을 허용합니다.

-- 1) 순원 테이블 (이름 · 통독계획 · 통독현황)
create table if not exists public.members (
  id          text primary key,
  name        text not null,
  avatar      text,
  plan        jsonb,
  progress    jsonb not null default '{}'::jsonb,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

-- 2) 공유 암호 검증용 메타 테이블 (게이트 확인)
create table if not exists public.app_meta (
  id   int primary key,
  note text
);
insert into public.app_meta (id, note) values (1, 'ok')
  on conflict (id) do nothing;

-- 3) 테이블 접근 권한 (RLS가 실제 접근을 통제하므로 grant는 넓게)
grant select, insert, update, delete on public.members  to anon, authenticated;
grant select                        on public.app_meta to anon, authenticated;

-- 4) RLS 활성화
alter table public.members  enable row level security;
alter table public.app_meta enable row level security;

-- 5) 공유 암호(헤더 x-app-key) 일치 여부 검증 함수
--    ↓↓↓ '여기에_공유암호' 를 실제 공유 암호로 바꾸세요 ↓↓↓
create or replace function public.app_key_ok()
returns boolean
language sql
stable
as $$
  select coalesce(
    current_setting('request.headers', true)::json ->> 'x-app-key',
    ''
  ) = '여기에_공유암호';
$$;

-- 6) 정책: 올바른 공유 암호일 때만 읽기/쓰기 허용
drop policy if exists members_gate on public.members;
create policy members_gate on public.members
  for all
  to anon, authenticated
  using ( public.app_key_ok() )
  with check ( public.app_key_ok() );

drop policy if exists app_meta_gate on public.app_meta;
create policy app_meta_gate on public.app_meta
  for select
  to anon, authenticated
  using ( public.app_key_ok() );

-- 끝. 이후 공유 암호를 바꾸려면 4)의 함수만 다시 실행하면 됩니다.
