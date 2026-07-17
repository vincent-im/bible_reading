// Supabase 연결 설정
// ─────────────────────────────────────────────────────────────
// 아래 두 값은 Supabase 대시보드 → Project Settings → API 에서 복사합니다.
// anon(public) 키는 "공개용"으로 설계된 값이라 저장소에 넣어도 안전합니다.
// (실제 보호는 공유 암호 + RLS 정책이 담당합니다.  service_role 키는 절대 넣지 마세요.)
//
// 값이 비어 있으면 앱은 예전처럼 '로컬 모드'(localStorage)로 동작합니다.
// 값이 채워지면 '공용 DB 모드'로 전환되어 접속 시 공유 암호를 요구합니다.

export const SUPABASE_URL = 'https://iqctywyhktlggrqnnmma.supabase.co'
export const SUPABASE_ANON_KEY =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY3R5d3loa3RsZ2dycW5ubW1hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyODk4NDQsImV4cCI6MjA5OTg2NTg0NH0.pH20Fy827srFxHCpEWVz---WLBj8IilOES32OWIAdMg'

export const SUPABASE_ENABLED = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY)

// 공유 암호를 요청 헤더로 전달할 때 사용하는 헤더 이름 (RLS에서 검증)
export const APP_KEY_HEADER = 'x-app-key'

// 세션 동안 공유 암호를 기억하는 sessionStorage 키
export const GATE_STORAGE_KEY = 'darakbang_gate_key'
