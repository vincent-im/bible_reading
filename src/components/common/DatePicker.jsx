import { useMemo, useState } from 'react'
import { parseDate, toDateStr, todayStr } from '../../hooks/usePlan'

const WEEK_LABELS = ['일', '월', '화', '수', '목', '금', '토']

// 달력 모양 날짜 선택기 (인라인)
// value: "YYYY-MM-DD", onChange(dateStr), min/max: "YYYY-MM-DD"
export default function DatePicker({ value, onChange, min, max }) {
  const initial = parseDate(value) || new Date()
  const [view, setView] = useState({
    year: initial.getFullYear(),
    month: initial.getMonth(), // 0-based
  })

  const today = todayStr()
  const minDate = parseDate(min)
  const maxDate = parseDate(max)

  const cells = useMemo(() => {
    const first = new Date(view.year, view.month, 1)
    const startDay = first.getDay() // 0=일
    const daysInMonth = new Date(view.year, view.month + 1, 0).getDate()
    const arr = []
    for (let i = 0; i < startDay; i++) arr.push(null)
    for (let d = 1; d <= daysInMonth; d++) {
      arr.push(new Date(view.year, view.month, d))
    }
    while (arr.length % 7 !== 0) arr.push(null)
    return arr
  }, [view])

  const isDisabled = (date) => {
    if (minDate && date < minDate) return true
    if (maxDate && date > maxDate) return true
    return false
  }

  const goPrev = () =>
    setView((v) =>
      v.month === 0
        ? { year: v.year - 1, month: 11 }
        : { year: v.year, month: v.month - 1 }
    )
  const goNext = () =>
    setView((v) =>
      v.month === 11
        ? { year: v.year + 1, month: 0 }
        : { year: v.year, month: v.month + 1 }
    )

  return (
    <div className="rounded-2xl border border-gray-100 bg-white p-3">
      {/* 헤더 */}
      <div className="mb-2 flex items-center justify-between">
        <button
          type="button"
          onClick={goPrev}
          className="flex h-9 w-9 items-center justify-center rounded-full text-gray-500 transition active:scale-90 active:bg-gray-100"
          aria-label="이전 달"
        >
          ‹
        </button>
        <div className="text-base font-bold text-gray-800">
          {view.year}년 {view.month + 1}월
        </div>
        <button
          type="button"
          onClick={goNext}
          className="flex h-9 w-9 items-center justify-center rounded-full text-gray-500 transition active:scale-90 active:bg-gray-100"
          aria-label="다음 달"
        >
          ›
        </button>
      </div>

      {/* 요일 */}
      <div className="mb-1 grid grid-cols-7">
        {WEEK_LABELS.map((w, i) => (
          <div
            key={w}
            className={`py-1 text-center text-xs font-semibold ${
              i === 0 ? 'text-red-400' : i === 6 ? 'text-blue-400' : 'text-gray-400'
            }`}
          >
            {w}
          </div>
        ))}
      </div>

      {/* 날짜 */}
      <div className="grid grid-cols-7 gap-0.5">
        {cells.map((date, i) => {
          if (!date) return <div key={`e${i}`} />
          const ds = toDateStr(date)
          const selected = ds === value
          const isToday = ds === today
          const disabled = isDisabled(date)
          const dow = date.getDay()
          return (
            <button
              key={ds}
              type="button"
              disabled={disabled}
              onClick={() => onChange?.(ds)}
              className={[
                'flex aspect-square items-center justify-center rounded-full text-sm transition',
                selected
                  ? 'bg-indigo font-bold text-white shadow-md'
                  : disabled
                    ? 'cursor-not-allowed text-gray-300'
                    : 'text-gray-700 active:scale-90 active:bg-indigo/10',
                !selected && isToday ? 'ring-2 ring-indigo/40' : '',
                !selected && !disabled && dow === 0 ? 'text-red-400' : '',
                !selected && !disabled && dow === 6 ? 'text-blue-400' : '',
              ].join(' ')}
            >
              {date.getDate()}
            </button>
          )
        })}
      </div>
    </div>
  )
}
