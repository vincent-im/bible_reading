import { useCallback } from 'react'
import { useApp } from '../contexts/AppContext'

function genId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `m_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

const AVATAR_EMOJIS = ['🐰', '🐱', '🐶', '🦊', '🐻', '🐼', '🐯', '🦁', '🐵', '🐨', '🐧', '🦉']

// 순원 CRUD 훅
export default function useMembers() {
  const { members, setMembers, selectedMemberId, setSelectedMemberId } = useApp()

  const addMember = useCallback(
    (name) => {
      const trimmed = (name || '').trim()
      if (!trimmed) return null
      const newMember = {
        id: genId(),
        name: trimmed,
        avatar: AVATAR_EMOJIS[Math.floor(Math.random() * AVATAR_EMOJIS.length)],
        plan: null, // { startDate, endDate, startTestament }
        progress: {}, // { [bookId]: [chapter, ...] }
        createdAt: new Date().toISOString(),
      }
      setMembers((prev) => [...prev, newMember])
      return newMember.id
    },
    [setMembers]
  )

  const updateMember = useCallback(
    (id, patch) => {
      setMembers((prev) =>
        prev.map((m) => (m.id === id ? { ...m, ...patch } : m))
      )
    },
    [setMembers]
  )

  const removeMember = useCallback(
    (id) => {
      setMembers((prev) => prev.filter((m) => m.id !== id))
    },
    [setMembers]
  )

  const setMemberPlan = useCallback(
    (id, plan) => {
      setMembers((prev) =>
        prev.map((m) => (m.id === id ? { ...m, plan } : m))
      )
    },
    [setMembers]
  )

  // 한 장 읽음 토글
  const toggleChapter = useCallback(
    (id, bookId, chapter) => {
      setMembers((prev) =>
        prev.map((m) => {
          if (m.id !== id) return m
          const progress = { ...(m.progress || {}) }
          const arr = Array.isArray(progress[bookId])
            ? [...progress[bookId]]
            : []
          const idx = arr.indexOf(chapter)
          if (idx >= 0) {
            arr.splice(idx, 1)
          } else {
            arr.push(chapter)
            arr.sort((a, b) => a - b)
          }
          if (arr.length === 0) {
            delete progress[bookId]
          } else {
            progress[bookId] = arr
          }
          return { ...m, progress }
        })
      )
    },
    [setMembers]
  )

  // 여러 장을 한 번에 읽음 처리 (오늘 분량 완료 등)
  const markChapters = useCallback(
    (id, chapters, read = true) => {
      setMembers((prev) =>
        prev.map((m) => {
          if (m.id !== id) return m
          const progress = { ...(m.progress || {}) }
          for (const { bookId, chapter } of chapters) {
            const arr = Array.isArray(progress[bookId])
              ? [...progress[bookId]]
              : []
            const idx = arr.indexOf(chapter)
            if (read && idx < 0) {
              arr.push(chapter)
            } else if (!read && idx >= 0) {
              arr.splice(idx, 1)
            }
            arr.sort((a, b) => a - b)
            if (arr.length === 0) delete progress[bookId]
            else progress[bookId] = arr
          }
          return { ...m, progress }
        })
      )
    },
    [setMembers]
  )

  const resetProgress = useCallback(
    (id) => {
      setMembers((prev) =>
        prev.map((m) => (m.id === id ? { ...m, progress: {} } : m))
      )
    },
    [setMembers]
  )

  const getMember = useCallback(
    (id) => members.find((m) => m.id === id) || null,
    [members]
  )

  const selectedMember = members.find((m) => m.id === selectedMemberId) || null

  return {
    members,
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
    getMember,
  }
}
