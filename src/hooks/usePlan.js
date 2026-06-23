import { useMemo } from 'react'
import {
  BIBLE_BOOKS,
  OT_BOOKS,
  NT_BOOKS,
  TOTAL_CHAPTERS,
  getBook,
} from '../data/bibleData'

const MS_PER_DAY = 86400000

/* ────────────────────────────────────────────────
 *  날짜 유틸
 * ──────────────────────────────────────────────── */

// "YYYY-MM-DD" -> 로컬 자정 Date
export function parseDate(str) {
  if (!str) return null
  const [y, m, d] = str.split('-').map(Number)
  if (!y || !m || !d) return null
  return new Date(y, m - 1, d)
}

// 오늘 날짜 "YYYY-MM-DD"
export function todayStr() {
  return toDateStr(new Date())
}

export function toDateStr(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

// "2026-06-23" -> "2026.06.23 (화)"
export function formatDateKo(str) {
  const d = parseDate(str)
  if (!d) return ''
  return `${str.replaceAll('-', '.')} (${WEEKDAYS[d.getDay()]})`
}

// 시작~종료 포함 일수
export function diffDaysInclusive(startStr, endStr) {
  const s = parseDate(startStr)
  const e = parseDate(endStr)
  if (!s || !e) return 0
  return Math.round((e - s) / MS_PER_DAY) + 1
}

// 시작일 기준 ref 날짜가 몇 번째 날인지 (0-based, 음수면 시작 전)
export function getDayIndex(startStr, refStr) {
  const s = parseDate(startStr)
  const r = parseDate(refStr)
  if (!s || !r) return 0
  return Math.round((r - s) / MS_PER_DAY)
}

/* ────────────────────────────────────────────────
 *  통독 순서
 *  OT 시작: 창세기(1)→말라기(39)→마태복음(40)→요한계시록(66)
 *  NT 시작: 마태복음(40)→요한계시록(66)→창세기(1)→말라기(39)
 * ──────────────────────────────────────────────── */
export function getBookOrder(startTestament) {
  return startTestament === 'NT'
    ? [...NT_BOOKS, ...OT_BOOKS]
    : [...OT_BOOKS, ...NT_BOOKS]
}

// 평탄화된 읽기 순서 배열: [{ bookId, chapter }, ...] (길이 1189)
export function buildReadingOrder(startTestament) {
  const order = []
  for (const book of getBookOrder(startTestament)) {
    for (let ch = 1; ch <= book.chapters; ch++) {
      order.push({ bookId: book.id, chapter: ch })
    }
  }
  return order
}

// "bookId-chapter" -> 통독 순서상의 전역 인덱스(0-based)
export function buildOrderIndexMap(order) {
  const map = new Map()
  order.forEach((item, i) => map.set(`${item.bookId}-${item.chapter}`, i))
  return map
}

/* ────────────────────────────────────────────────
 *  읽음 정보 (progress -> Set, count)
 *  progress 스키마: { [bookId]: [chapter, ...] }
 * ──────────────────────────────────────────────── */
export function getReadInfo(progress) {
  const readSet = new Set()
  let readCount = 0
  if (progress) {
    for (const bookId of Object.keys(progress)) {
      const arr = progress[bookId]
      if (!Array.isArray(arr)) continue
      const book = getBook(Number(bookId))
      if (!book) continue
      for (const ch of arr) {
        if (ch >= 1 && ch <= book.chapters) {
          const key = `${bookId}-${ch}`
          if (!readSet.has(key)) {
            readSet.add(key)
            readCount++
          }
        }
      }
    }
  }
  return { readSet, readCount }
}

/* ────────────────────────────────────────────────
 *  계획 계산
 * ──────────────────────────────────────────────── */
export function isPlanValid(plan) {
  return !!(plan && plan.startDate && plan.endDate && plan.startTestament)
}

export function computePlan(plan, refStr = todayStr()) {
  if (!isPlanValid(plan)) {
    return { valid: false }
  }
  const order = buildReadingOrder(plan.startTestament)
  const totalDays = Math.max(1, diffDaysInclusive(plan.startDate, plan.endDate))
  const dailyChapters = Math.max(1, Math.ceil(TOTAL_CHAPTERS / totalDays))

  const rawIndex = getDayIndex(plan.startDate, refStr)
  const started = rawIndex >= 0
  const periodOver = rawIndex > totalDays - 1
  const dayIndex = Math.min(Math.max(rawIndex, 0), totalDays - 1)

  // 오늘 읽을 범위 (누적 인덱스 기준 슬라이스)
  const todayStartIdx = dayIndex * dailyChapters
  const todayEndIdx = Math.min(todayStartIdx + dailyChapters, TOTAL_CHAPTERS) // exclusive
  const todayRange = started ? order.slice(todayStartIdx, todayEndIdx) : []

  // 오늘까지 읽었어야 하는 누적 장수 (계획 대비 비교용)
  const expectedByToday = started
    ? Math.min((dayIndex + 1) * dailyChapters, TOTAL_CHAPTERS)
    : 0

  return {
    valid: true,
    order,
    totalDays,
    dailyChapters,
    rawIndex,
    dayIndex,
    started,
    periodOver,
    todayRange,
    todayStartIdx,
    todayEndIdx,
    expectedByToday,
  }
}

// 개별 장의 상태: 'read' | 'today' | 'overdue' | 'future'
export function getChapterStatus(globalIndex, planInfo, isRead) {
  if (isRead) return 'read'
  if (!planInfo.valid || !planInfo.started || globalIndex < 0) return 'future'
  const sched = Math.floor(globalIndex / planInfo.dailyChapters)
  if (sched > planInfo.dayIndex) return 'future'
  if (sched === planInfo.dayIndex && !planInfo.periodOver) return 'today'
  return 'overdue'
}

// 순원 전체 통계 (홈/진도 비교용). 훅 없이 호출 가능.
export function computeMemberStats(member, refStr = todayStr()) {
  const planInfo = computePlan(member.plan, refStr)
  const { readSet, readCount } = getReadInfo(member.progress)

  const percent = Number(((readCount / TOTAL_CHAPTERS) * 100).toFixed(1))
  const expectedCount = planInfo.valid ? planInfo.expectedByToday : 0
  const behindCount = Math.max(0, expectedCount - readCount)
  const aheadCount = Math.max(0, readCount - expectedCount)
  const onTrack = readCount >= expectedCount

  let todayTotal = 0
  let todayDone = 0
  if (planInfo.valid && planInfo.started) {
    todayTotal = planInfo.todayRange.length
    todayDone = planInfo.todayRange.filter((c) =>
      readSet.has(`${c.bookId}-${c.chapter}`)
    ).length
  }

  return {
    planInfo,
    readSet,
    readCount,
    percent,
    expectedCount,
    behindCount,
    aheadCount,
    onTrack,
    todayTotal,
    todayDone,
    hasPlan: planInfo.valid,
    totalChapters: TOTAL_CHAPTERS,
  }
}

/* ────────────────────────────────────────────────
 *  훅: 단일 순원의 계획/상태 일체를 메모이즈해서 제공
 * ──────────────────────────────────────────────── */
export default function usePlan(member, refStr = todayStr()) {
  return useMemo(() => {
    if (!member) {
      return {
        stats: null,
        planInfo: { valid: false },
        orderIndexMap: new Map(),
        statusFor: () => 'future',
        isRead: () => false,
        books: BIBLE_BOOKS,
      }
    }
    const stats = computeMemberStats(member, refStr)
    const orderIndexMap = stats.planInfo.valid
      ? buildOrderIndexMap(stats.planInfo.order)
      : new Map()

    const isRead = (bookId, chapter) =>
      stats.readSet.has(`${bookId}-${chapter}`)

    const statusFor = (bookId, chapter) => {
      const gi = orderIndexMap.has(`${bookId}-${chapter}`)
        ? orderIndexMap.get(`${bookId}-${chapter}`)
        : -1
      return getChapterStatus(gi, stats.planInfo, isRead(bookId, chapter))
    }

    return {
      stats,
      planInfo: stats.planInfo,
      orderIndexMap,
      statusFor,
      isRead,
      books: BIBLE_BOOKS,
    }
  }, [member, refStr])
}
