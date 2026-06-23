import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'darakbang_app'

const AppContext = createContext(null)

function loadState() {
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
  const [members, setMembers] = useState(() => loadState().members)
  const [selectedMemberId, setSelectedMemberId] = useState(null)

  // 변경 시마다 localStorage 동기화 (오프라인 동작)
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ members }))
    } catch (e) {
      console.warn('데이터 저장에 실패했습니다.', e)
    }
  }, [members])

  // 선택된 순원이 삭제되면 선택 해제
  useEffect(() => {
    if (
      selectedMemberId &&
      !members.some((m) => m.id === selectedMemberId)
    ) {
      setSelectedMemberId(null)
    }
  }, [members, selectedMemberId])

  const value = useMemo(
    () => ({
      members,
      setMembers,
      selectedMemberId,
      setSelectedMemberId,
      storageKey: STORAGE_KEY,
    }),
    [members, selectedMemberId]
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
