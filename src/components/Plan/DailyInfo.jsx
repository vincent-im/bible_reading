import { getBook } from '../../data/bibleData'
import { formatDateKo, todayStr, parseDate } from '../../hooks/usePlan'

// [{bookId, chapter}] -> "창세기 1~4장" 또는 "말라기 4장, 마태복음 1~2장"
export function formatRange(rangeArr) {
  if (!rangeArr || rangeArr.length === 0) return ''
  const segments = []
  let cur = null
  for (const { bookId, chapter } of rangeArr) {
    if (cur && cur.bookId === bookId && chapter === cur.end + 1) {
      cur.end = chapter
    } else {
      if (cur) segments.push(cur)
      cur = { bookId, start: chapter, end: chapter }
    }
  }
  if (cur) segments.push(cur)
  return segments
    .map((s) => {
      const name = getBook(s.bookId)?.name ?? ''
      return s.start === s.end
        ? `${name} ${s.start}장`
        : `${name} ${s.start}~${s.end}장`
    })
    .join(', ')
}

// 오늘의 읽기 정보 배너
export default function DailyInfo({ stats, plan, onMarkToday, onUndoToday, onSetup }) {
  // 계획 없음
  if (!stats?.hasPlan) {
    return (
      <div className="rounded-2xl bg-gradient-to-br from-indigo to-violet-500 p-5 text-white shadow-md">
        <div className="text-sm font-medium opacity-90">통독 계획이 없어요</div>
        <p className="mt-1 text-lg font-bold">먼저 통독 계획을 세워볼까요?</p>
        <button
          onClick={onSetup}
          className="mt-3 rounded-xl bg-white/20 px-4 py-2 text-sm font-semibold backdrop-blur transition active:scale-95"
        >
          + 통독 계획 세우기
        </button>
      </div>
    )
  }

  const { planInfo } = stats

  // 시작 전
  if (!planInfo.started) {
    const dDay = -planInfo.rawIndex
    return (
      <div className="rounded-2xl bg-gradient-to-br from-amber-400 to-orange-400 p-5 text-white shadow-md">
        <div className="text-sm font-medium opacity-90">통독 시작 전</div>
        <p className="mt-1 text-2xl font-extrabold">D-{dDay}</p>
        <p className="mt-1 text-sm opacity-90">
          {formatDateKo(plan.startDate)}부터 시작해요
        </p>
      </div>
    )
  }

  // 기간 종료
  if (planInfo.periodOver) {
    const done = stats.percent >= 100
    return (
      <div className="rounded-2xl bg-gradient-to-br from-indigo to-violet-500 p-5 text-white shadow-md">
        <div className="text-sm font-medium opacity-90">통독 기간 종료</div>
        <p className="mt-1 text-lg font-bold">
          {done ? '🎉 통독을 완주했어요!' : `현재 ${Math.floor(stats.percent)}% 읽었어요`}
        </p>
        <p className="mt-1 text-sm opacity-90">
          {done ? '끝까지 함께해 주셔서 감사해요' : '남은 분량도 천천히 채워봐요'}
        </p>
      </div>
    )
  }

  // 정상 (오늘 분량)
  const allDone = stats.todayTotal > 0 && stats.todayDone >= stats.todayTotal
  const rangeText = formatRange(planInfo.todayRange)

  return (
    <div className="rounded-2xl bg-gradient-to-br from-indigo to-violet-500 p-5 text-white shadow-md">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium opacity-90">📖 오늘의 통독</span>
        <span className="text-xs opacity-75">{formatDateKo(todayStr())}</span>
      </div>

      <p className="mt-2 text-xl font-extrabold leading-snug">{rangeText}</p>
      <p className="mt-1 text-sm opacity-90">
        {planInfo.dayIndex + 1}일차 · 하루 {planInfo.dailyChapters}장
      </p>

      {/* 오늘 진행 */}
      <div className="mt-3 flex items-center gap-2">
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/25">
          <div
            className="h-full rounded-full bg-white transition-all duration-500"
            style={{
              width: `${(stats.todayDone / Math.max(1, stats.todayTotal)) * 100}%`,
            }}
          />
        </div>
        <span className="text-xs font-semibold">
          {stats.todayDone}/{stats.todayTotal}
        </span>
      </div>

      {/* 액션 */}
      {allDone ? (
        <div className="mt-3 flex items-center justify-between">
          <span className="text-sm font-bold">오늘 분량 완료! 🎉</span>
          <button
            onClick={() => onUndoToday?.(planInfo.todayRange)}
            className="text-xs font-medium underline opacity-80 active:opacity-100"
          >
            되돌리기
          </button>
        </div>
      ) : (
        <button
          onClick={() => onMarkToday?.(planInfo.todayRange)}
          className="mt-3 w-full rounded-xl bg-white py-2.5 text-sm font-bold text-indigo shadow transition active:scale-95"
        >
          오늘 분량 다 읽었어요 ✓
        </button>
      )}

      {stats.behindCount > 0 && (
        <p className="mt-2 text-center text-xs text-amber-100">
          ⏰ 밀린 분량 {stats.behindCount}장이 있어요
        </p>
      )}
    </div>
  )
}
