import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import useMembers from '../hooks/useMembers'
import usePlan, { getBookOrder } from '../hooks/usePlan'
import { BIBLE_BOOKS } from '../data/bibleData'
import DailyInfo from '../components/Plan/DailyInfo'
import PlanSetup from '../components/Plan/PlanSetup'
import BookGrid from '../components/Reading/BookGrid'
import Modal from '../components/common/Modal'
import LevelBadge from '../components/Progress/LevelBadge'

const FILTERS = [
  { key: 'all', label: '전체' },
  { key: 'today', label: '오늘 분량' },
  { key: 'overdue', label: '밀린 분량' },
]

export default function MyReadingPage() {
  const {
    members,
    selectedMember,
    selectMember,
    setMemberPlan,
    toggleChapter,
    markChapters,
  } = useMembers()

  const plan = usePlan(selectedMember)
  const [showPlan, setShowPlan] = useState(false)
  const [showPicker, setShowPicker] = useState(false)
  const [filter, setFilter] = useState('all')

  const bookOrder = useMemo(() => {
    if (selectedMember?.plan?.startTestament) {
      return getBookOrder(selectedMember.plan.startTestament)
    }
    return BIBLE_BOOKS
  }, [selectedMember])

  // 책별 상태 요약 (필터링 / 자동 펼침용)
  const summary = useMemo(() => {
    const map = {}
    for (const book of bookOrder) {
      let today = 0
      let overdue = 0
      for (let ch = 1; ch <= book.chapters; ch++) {
        const st = plan.statusFor(book.id, ch)
        if (st === 'today') today++
        else if (st === 'overdue') overdue++
      }
      map[book.id] = { today, overdue }
    }
    return map
  }, [bookOrder, plan])

  // 순원 미선택 → 이름 선택 화면
  if (!selectedMember) {
    return <MemberPicker members={members} onPick={selectMember} />
  }

  const visibleBooks = bookOrder.filter((book) => {
    if (filter === 'today') return summary[book.id]?.today > 0
    if (filter === 'overdue') return summary[book.id]?.overdue > 0
    return true
  })

  const handleSavePlan = (newPlan) => {
    setMemberPlan(selectedMember.id, newPlan)
    setShowPlan(false)
  }

  return (
    <div className="space-y-4">
      {/* 순원 전환 바 */}
      <div className="flex items-center justify-between rounded-2xl bg-white p-3 shadow-sm">
        <div className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-cream text-xl">
            {selectedMember.avatar || '🙂'}
          </span>
          <div>
            <div className="text-sm font-bold text-gray-800">
              {selectedMember.name}
            </div>
            <div className="text-[11px] text-gray-400">님의 통독</div>
          </div>
        </div>
        <button
          onClick={() => setShowPicker(true)}
          className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-semibold text-gray-600 transition active:scale-95"
        >
          순원 변경
        </button>
      </div>

      {/* 오늘의 읽기 배너 */}
      <DailyInfo
        stats={plan.stats}
        plan={selectedMember.plan}
        onSetup={() => setShowPlan(true)}
        onMarkToday={(range) => markChapters(selectedMember.id, range, true)}
        onUndoToday={(range) => markChapters(selectedMember.id, range, false)}
      />

      {plan.stats?.hasPlan ? (
        <>
          {/* 진행 요약 + 계획 수정 */}
          <div className="flex items-center justify-between rounded-2xl bg-white p-4 shadow-sm">
            <LevelBadge percent={plan.stats.percent} size="sm" showMessage />
            <div className="text-right">
              <div className="text-2xl font-extrabold text-indigo">
                {Math.floor(plan.stats.percent)}%
              </div>
              <div className="text-[11px] text-gray-400">
                {plan.stats.readCount}/{plan.stats.totalChapters}장
              </div>
            </div>
          </div>

          {/* 범례 + 필터 */}
          <div className="space-y-2">
            <Legend />
            <div className="flex gap-1.5">
              {FILTERS.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  className={[
                    'flex-1 rounded-full py-2 text-xs font-semibold transition',
                    filter === f.key
                      ? 'bg-indigo text-white shadow'
                      : 'bg-white text-gray-500',
                  ].join(' ')}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* 계획 수정 버튼 */}
          <button
            onClick={() => setShowPlan(true)}
            className="w-full rounded-xl border border-indigo/30 bg-indigo/5 py-2.5 text-xs font-semibold text-indigo transition active:scale-95"
          >
            ⚙️ 통독 계획 수정 ({selectedMember.plan.startTestament === 'OT' ? '구약부터' : '신약부터'})
          </button>

          {/* 책 그리드 목록 */}
          {visibleBooks.length === 0 ? (
            <div className="rounded-2xl bg-white p-6 text-center text-sm text-gray-400 shadow-sm">
              {filter === 'today'
                ? '오늘 읽을 분량이 없어요 🎉'
                : '밀린 분량이 없어요 👍'}
            </div>
          ) : (
            <div className="space-y-2">
              {visibleBooks.map((book) => (
                <BookGrid
                  key={book.id}
                  book={book}
                  statusFor={plan.statusFor}
                  onToggle={(bookId, ch) =>
                    toggleChapter(selectedMember.id, bookId, ch)
                  }
                  defaultOpen={
                    filter !== 'all' ||
                    summary[book.id]?.today > 0 ||
                    summary[book.id]?.overdue > 0
                  }
                />
              ))}
            </div>
          )}
        </>
      ) : null}

      {/* 계획 설정/수정 모달 */}
      <Modal
        open={showPlan}
        onClose={() => setShowPlan(false)}
        title={selectedMember.plan ? '통독 계획 수정' : '통독 계획 세우기'}
      >
        <PlanSetup
          initialPlan={selectedMember.plan}
          onSave={handleSavePlan}
          onCancel={() => setShowPlan(false)}
        />
      </Modal>

      {/* 순원 변경 모달 */}
      <Modal
        open={showPicker}
        onClose={() => setShowPicker(false)}
        title="순원 선택"
      >
        <div className="space-y-2">
          {members.map((m) => (
            <button
              key={m.id}
              onClick={() => {
                selectMember(m.id)
                setShowPicker(false)
              }}
              className={[
                'flex w-full items-center gap-3 rounded-xl border p-3 text-left transition active:scale-95',
                m.id === selectedMember.id
                  ? 'border-indigo bg-indigo/5'
                  : 'border-gray-100 bg-white',
              ].join(' ')}
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-cream text-xl">
                {m.avatar || '🙂'}
              </span>
              <span className="font-semibold text-gray-800">{m.name}</span>
              {m.id === selectedMember.id && (
                <span className="ml-auto text-indigo">✓</span>
              )}
            </button>
          ))}
        </div>
      </Modal>
    </div>
  )
}

function Legend() {
  const items = [
    { cls: 'bg-red-100 border-2 border-red-400', label: '오늘' },
    { cls: 'bg-blue-500', label: '읽음' },
    { cls: 'bg-orange-100 border border-orange-200', label: '밀림' },
    { cls: 'bg-gray-100', label: '예정' },
  ]
  return (
    <div className="flex items-center justify-center gap-3 rounded-xl bg-white py-2 text-[11px] text-gray-500 shadow-sm">
      {items.map((it) => (
        <span key={it.label} className="flex items-center gap-1">
          <span className={`inline-block h-3.5 w-3.5 rounded-full ${it.cls}`} />
          {it.label}
        </span>
      ))}
    </div>
  )
}

function MemberPicker({ members, onPick }) {
  if (members.length === 0) {
    return (
      <div className="rounded-2xl bg-white p-8 text-center shadow-sm">
        <div className="text-4xl">🙋</div>
        <p className="mt-3 font-bold text-gray-700">등록된 순원이 없어요</p>
        <p className="mt-1 text-sm text-gray-400">
          홈에서 순원을 먼저 추가해주세요
        </p>
        <Link
          to="/"
          className="mt-4 inline-block rounded-xl bg-indigo px-5 py-2.5 text-sm font-semibold text-white shadow-md transition active:scale-95"
        >
          홈으로 가기
        </Link>
      </div>
    )
  }
  return (
    <div>
      <h2 className="mb-1 px-1 text-lg font-extrabold text-gray-800">
        누구의 통독인가요?
      </h2>
      <p className="mb-4 px-1 text-sm text-gray-400">
        본인의 이름을 선택해주세요
      </p>
      <div className="grid grid-cols-2 gap-3">
        {members.map((m) => (
          <button
            key={m.id}
            onClick={() => onPick(m.id)}
            className="flex flex-col items-center gap-2 rounded-2xl bg-white p-5 shadow-md transition active:scale-95"
          >
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-cream text-3xl">
              {m.avatar || '🙂'}
            </span>
            <span className="font-bold text-gray-800">{m.name}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
