import { useCallback, useMemo } from 'react'
import { useApp } from '../contexts/AppContext'

function genId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `m_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

const AVATAR_EMOJIS = ['🐰', '🐱', '🐶', '🦊', '🐻', '🐼', '🐯', '🦁', '🐵', '🐨', '🐧', '🦉']

// 순원 CRUD 훅 (로컬 상태 + 공용 DB 동기화)
export default function useMembers() {
  const {
    members,
    setMembers,
    selectedMemberId,
    setSelectedMemberId,
    remote,
  } = useApp()

  // 화면 표시는 이름 가나다순으로 정렬 (원본 저장 순서는 그대로 유지)
  const sortedMembers = useMemo(
    () =>
      [...members].sort((a, b) =>
        (a.name || '').localeCompare(b.name || '', 'ko')
      ),
    [members]
  )

  // 현재 순원 조회 헬퍼
  const findMember = useCallback(
    (id) => members.find((m) => m.id === id) || null,
    [members]
  )

  const addMember = useCallback(
    (name) => {
      const trimmed = (name || '').trim()
      if (!trimmed) return null
      const newMember = {
        id: genId(),
        name: trimmed,
        avatar: AVATAR_EMOJIS[Math.floor(Math.random() * AVATAR_EMOJIS.length)],
        plan: null,
        progress: {},
        createdAt: new Date().toISOString(),
      }
      setMembers((prev) => [...prev, newMember])
      remote.upsert(newMember)
      return newMember.id
    },
    [setMembers, remote]
  )

  // 순원 하나를 patch로 갱신하고 서버 동기화
  const patchMember = useCallback(
    (id, patchFn) => {
      const current = members.find((m) => m.id === id)
      if (!current) return
      const updated = patchFn(current)
      setMembers((prev) => prev.map((m) => (m.id === id ? updated : m)))
      remote.upsert(updated)
    },
    [members, setMembers, remote]
  )

  const updateMember = useCallback(
    (id, patch) => patchMember(id, (m) => ({ ...m, ...patch })),
    [patchMember]
  )

  const removeMember = useCallback(
    (id) => {
      setMembers((prev) => prev.filter((m) => m.id !== id))
      remote.remove(id)
    },
    [setMembers, remote]
  )

  const setMemberPlan = useCallback(
    (id, plan) => patchMember(id, (m) => ({ ...m, plan })),
    [patchMember]
  )

  // 한 장 읽음 토글
  const toggleChapter = useCallback(
    (id, bookId, chapter) => {
      patchMember(id, (m) => {
        const progress = { ...(m.progress || {}) }
        const arr = Array.isArray(progress[bookId]) ? [...progress[bookId]] : []
        const idx = arr.indexOf(chapter)
        if (idx >= 0) arr.splice(idx, 1)
        else {
          arr.push(chapter)
          arr.sort((a, b) => a - b)
        }
        if (arr.length === 0) delete progress[bookId]
        else progress[bookId] = arr
        return { ...m, progress }
      })
    },
    [patchMember]
  )

  // 여러 장을 한 번에 읽음/취소 처리
  const markChapters = useCallback(
    (id, chapters, read = true) => {
      patchMember(id, (m) => {
        const progress = { ...(m.progress || {}) }
        for (const { bookId, chapter } of chapters) {
          const arr = Array.isArray(progress[bookId]) ? [...progress[bookId]] : []
          const idx = arr.indexOf(chapter)
          if (read && idx < 0) arr.push(chapter)
          else if (!read && idx >= 0) arr.splice(idx, 1)
          arr.sort((a, b) => a - b)
          if (arr.length === 0) delete progress[bookId]
          else progress[bookId] = arr
        }
        return { ...m, progress }
      })
    },
    [patchMember]
  )

  const resetProgress = useCallback(
    (id) => patchMember(id, (m) => ({ ...m, progress: {} })),
    [patchMember]
  )

  const selectedMember = members.find((m) => m.id === selectedMemberId) || null

  return {
    members: sortedMembers,
    selectedMemberId,
    selectedMember,
    selectMember: setSelectedMemberId,
    addMember,
    updateMember,
    removeMember,
    setMemberPlan,
    toggleChapter,
    markChapters,
    resetProgress,
    getMember: findMember,
  }
}
