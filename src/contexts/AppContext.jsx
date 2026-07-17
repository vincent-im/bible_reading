import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { SUPABASE_ENABLED, GATE_STORAGE_KEY } from '../lib/supabaseConfig'
import {
  makeClient,
  verifyGate,
  fetchMembers,
  upsertMemberRemote,
  deleteMemberRemote,
} from '../lib/supabaseClient'

const STORAGE_KEY = 'darakbang_app'
const AppContext = createContext(null)

function loadLocal() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { members: [] }
    const parsed = JSON.parse(raw)
    if (!parsed || !Array.isArray(parsed.members)) return { members: [] }
    return { members: parsed.members }
  } catch (e) {
    console.warn('저장된 데이터를 불러오지 못했습니다.', e)
    return { members: [] }
  }
}

export function AppProvider({ children }) {
  const [members, setMembers] = useState(() => loadLocal().members)
  const [selectedMemberId, setSelectedMemberId] = useState(null)

  const mode = SUPABASE_ENABLED ? 'remote' : 'local'
  // 로컬 모드는 항상 ready, 원격 모드는 공유 암호 잠금 상태로 시작
  const [status, setStatus] = useState(mode === 'remote' ? 'locked' : 'ready')
  const [error, setError] = useState('')
  const [syncError, setSyncError] = useState('')
  const clientRef = useRef(null)

  // localStorage 캐시 동기화 (오프라인 대비 · 양쪽 모드 공통)
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ members }))
    } catch (e) {
      console.warn('데이터 저장 실패', e)
    }
  }, [members])

  // 선택된 순원이 삭제되면 선택 해제
  useEffect(() => {
    if (selectedMemberId && !members.some((m) => m.id === selectedMemberId)) {
      setSelectedMemberId(null)
    }
  }, [members, selectedMemberId])

  // 공유 암호로 잠금 해제 → 데이터 로드 (+ 최초 1회 로컬 데이터 이전)
  const unlock = useCallback(async (passphrase, { remember = true } = {}) => {
    setStatus('loading')
    setError('')
    try {
      const client = makeClient(passphrase)
      const ok = await verifyGate(client)
      if (!ok) {
        setStatus('locked')
        setError('공유 암호가 올바르지 않아요.')
        return false
      }
      clientRef.current = client

      let remote = await fetchMembers(client)
      // 마이그레이션: 서버가 비어 있고 이 기기에 로컬 데이터가 있으면 업로드
      const local = loadLocal().members
      if (remote.length === 0 && local.length > 0) {
        for (const m of local) {
          try {
            await upsertMemberRemote(client, m)
          } catch (e) {
            console.warn('마이그레이션 실패', m?.name, e)
          }
        }
        remote = await fetchMembers(client)
      }

      setMembers(remote)
      if (remember) {
        try {
          sessionStorage.setItem(GATE_STORAGE_KEY, passphrase)
        } catch {
          /* 무시 */
        }
      }
      setStatus('ready')
      return true
    } catch (e) {
      console.warn('Supabase 연결 실패', e)
      setError('서버에 연결하지 못했어요. 인터넷 연결을 확인한 뒤 다시 시도해주세요.')
      setStatus('error')
      return false
    }
  }, [])

  // 세션에 저장된 암호로 자동 잠금 해제
  useEffect(() => {
    if (mode !== 'remote') return
    let saved = ''
    try {
      saved = sessionStorage.getItem(GATE_STORAGE_KEY) || ''
    } catch {
      /* 무시 */
    }
    if (saved) unlock(saved, { remember: false })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const lock = useCallback(() => {
    clientRef.current = null
    try {
      sessionStorage.removeItem(GATE_STORAGE_KEY)
    } catch {
      /* 무시 */
    }
    setStatus('locked')
  }, [])

  // 원격 동기화 헬퍼 (로컬 모드에서는 no-op)
  const remoteUpsert = useCallback(async (member) => {
    const client = clientRef.current
    if (!client) return
    try {
      await upsertMemberRemote(client, member)
      setSyncError('')
    } catch (e) {
      console.warn('저장 동기화 실패', e)
      setSyncError('변경사항을 서버에 저장하지 못했어요 (네트워크 확인).')
    }
  }, [])

  const remoteRemove = useCallback(async (id) => {
    const client = clientRef.current
    if (!client) return
    try {
      await deleteMemberRemote(client, id)
      setSyncError('')
    } catch (e) {
      console.warn('삭제 동기화 실패', e)
      setSyncError('삭제를 서버에 반영하지 못했어요.')
    }
  }, [])

  // 서버에서 최신 데이터 새로고침
  const refresh = useCallback(async () => {
    const client = clientRef.current
    if (!client) return
    try {
      setMembers(await fetchMembers(client))
    } catch (e) {
      console.warn('새로고침 실패', e)
    }
  }, [])

  const value = useMemo(
    () => ({
      members,
      setMembers,
      selectedMemberId,
      setSelectedMemberId,
      mode,
      status,
      error,
      syncError,
      unlock,
      lock,
      refresh,
      remote: {
        enabled: mode === 'remote',
        upsert: remoteUpsert,
        remove: remoteRemove,
      },
      storageKey: STORAGE_KEY,
    }),
    [
      members,
      selectedMemberId,
      mode,
      status,
      error,
      syncError,
      unlock,
      lock,
      refresh,
      remoteUpsert,
      remoteRemove,
    ]
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) {
    throw new Error('useApp must be used within an AppProvider')
  }
  return ctx
}
