import { createClient } from '@supabase/supabase-js'
import { SUPABASE_URL, SUPABASE_ANON_KEY, APP_KEY_HEADER } from './supabaseConfig'

// 공유 암호(passphrase)를 x-app-key 헤더로 실어 보내는 Supabase 클라이언트 생성.
// RLS 정책이 이 헤더 값을 검증하므로, 올바른 암호가 아니면 데이터 접근이 차단된다.
export function makeClient(passphrase) {
  return createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
    auth: { persistSession: false, autoRefreshToken: false },
    global: { headers: { [APP_KEY_HEADER]: passphrase ?? '' } },
  })
}

// 공유 암호 검증: app_meta(id=1)를 읽을 수 있으면 통과.
// 암호가 틀리면 RLS로 인해 행이 반환되지 않아 false.
export async function verifyGate(client) {
  const { data, error } = await client
    .from('app_meta')
    .select('id')
    .eq('id', 1)
    .maybeSingle()
  if (error) throw error
  return !!data
}

// ── 순원 목록 CRUD ──
export async function fetchMembers(client) {
  const { data, error } = await client
    .from('members')
    .select('*')
    .order('created_at', { ascending: true })
  if (error) throw error
  return (data || []).map(rowToMember)
}

export async function upsertMemberRemote(client, member) {
  const { error } = await client
    .from('members')
    .upsert(memberToRow(member), { onConflict: 'id' })
  if (error) throw error
}

export async function deleteMemberRemote(client, id) {
  const { error } = await client.from('members').delete().eq('id', id)
  if (error) throw error
}

// ── 행 <-> 앱 모델 변환 ──
function rowToMember(r) {
  return {
    id: r.id,
    name: r.name,
    avatar: r.avatar || '🙂',
    plan: r.plan || null,
    progress: r.progress || {},
    createdAt: r.created_at || null,
  }
}

function memberToRow(m) {
  return {
    id: m.id,
    name: m.name,
    avatar: m.avatar || null,
    plan: m.plan ?? null,
    progress: m.progress || {},
    updated_at: new Date().toISOString(),
  }
}
