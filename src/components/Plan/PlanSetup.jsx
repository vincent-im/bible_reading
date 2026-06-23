import { useMemo, useState } from 'react'
import DatePicker from '../common/DatePicker'
import {
  diffDaysInclusive,
  formatDateKo,
  parseDate,
  toDateStr,
  todayStr,
} from '../../hooks/usePlan'
import { TOTAL_CHAPTERS } from '../../data/bibleData'

function addDays(dateStr, days) {
  const d = parseDate(dateStr)
  d.setDate(d.getDate() + days)
  return toDateStr(d)
}

// 통독 계획 설정 (달력 + 시작책 선택)
export default function PlanSetup({ initialPlan, onSave, onCancel }) {
  const today = todayStr()
  const [startDate, setStartDate] = useState(initialPlan?.startDate || today)
  const [endDate, setEndDate] = useState(
    initialPlan?.endDate || addDays(today, 364)
  )
  const [startTestament, setStartTestament] = useState(
    initialPlan?.startTestament || 'OT'
  )
  const [activeField, setActiveField] = useState('start')

  const days = useMemo(
    () => Math.max(1, diffDaysInclusive(startDate, endDate)),
    [startDate, endDate]
  )
  const dailyChapters = Math.ceil(TOTAL_CHAPTERS / days)
  const invalid = parseDate(endDate) < parseDate(startDate)

  const handleDateChange = (ds) => {
    if (activeField === 'start') {
      setStartDate(ds)
      if (parseDate(ds) > parseDate(endDate)) setEndDate(ds)
    } else {
      setEndDate(ds)
    }
  }

  const handleSave = () => {
    if (invalid) return
    onSave?.({ startDate, endDate, startTestament })
  }

  return (
    <div className="space-y-5">
      {/* 기간 선택 */}
      <section>
        <h3 className="mb-2 text-sm font-bold text-gray-700">📅 통독 기간</h3>
        <div className="mb-3 grid grid-cols-2 gap-2">
          <FieldButton
            label="시작일"
            value={formatDateKo(startDate)}
            active={activeField === 'start'}
            onClick={() => setActiveField('start')}
          />
          <FieldButton
            label="종료일"
            value={formatDateKo(endDate)}
            active={activeField === 'end'}
            onClick={() => setActiveField('end')}
          />
        </div>
        <DatePicker
          value={activeField === 'start' ? startDate : endDate}
          onChange={handleDateChange}
          min={activeField === 'end' ? startDate : undefined}
        />
      </section>

      {/* 시작 위치 선택 */}
      <section>
        <h3 className="mb-2 text-sm font-bold text-gray-700">
          📖 어디부터 시작할까요?
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <TestamentButton
            active={startTestament === 'OT'}
            onClick={() => setStartTestament('OT')}
            title="구약부터"
            path="창세기 → 말라기 → 마태복음 → 요한계시록"
          />
          <TestamentButton
            active={startTestament === 'NT'}
            onClick={() => setStartTestament('NT')}
            title="신약부터"
            path="마태복음 → 요한계시록 → 창세기 → 말라기"
          />
        </div>
      </section>

      {/* 요약 */}
      <section className="rounded-2xl bg-indigo/5 p-4">
        <div className="flex items-center justify-around text-center">
          <Summary label="총 기간" value={`${days}일`} />
          <div className="h-8 w-px bg-indigo/20" />
          <Summary label="하루 분량" value={`${dailyChapters}장`} />
          <div className="h-8 w-px bg-indigo/20" />
          <Summary label="전체" value={`${TOTAL_CHAPTERS}장`} />
        </div>
        <p className="mt-3 text-center text-xs text-gray-500">
          전체 {TOTAL_CHAPTERS}장을 {days}일로 나누어{' '}
          <span className="font-bold text-indigo">하루 약 {dailyChapters}장</span>{' '}
          읽어요
        </p>
      </section>

      {invalid && (
        <p className="text-center text-sm font-medium text-red-500">
          종료일은 시작일보다 빠를 수 없어요.
        </p>
      )}

      {/* 버튼 */}
      <div className="flex gap-2 pt-1">
        {onCancel && (
          <button
            onClick={onCancel}
            className="flex-1 rounded-xl bg-gray-100 py-3 font-semibold text-gray-600 transition active:scale-95"
          >
            취소
          </button>
        )}
        <button
          onClick={handleSave}
          disabled={invalid}
          className="flex-1 rounded-xl bg-indigo py-3 font-semibold text-white shadow-md transition active:scale-95 disabled:opacity-40"
        >
          계획 저장
        </button>
      </div>
    </div>
  )
}

function FieldButton({ label, value, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'rounded-xl border px-3 py-2 text-left transition',
        active
          ? 'border-indigo bg-indigo/5 ring-2 ring-indigo/20'
          : 'border-gray-200 bg-white',
      ].join(' ')}
    >
      <div className="text-[11px] font-medium text-gray-400">{label}</div>
      <div className="text-sm font-bold text-gray-800">{value}</div>
    </button>
  )
}

function TestamentButton({ active, onClick, title, path }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'rounded-xl border p-3 text-left transition active:scale-95',
        active
          ? 'border-indigo bg-indigo/5 ring-2 ring-indigo/20'
          : 'border-gray-200 bg-white',
      ].join(' ')}
    >
      <div
        className={`text-sm font-bold ${active ? 'text-indigo' : 'text-gray-700'}`}
      >
        {title}
      </div>
      <div className="mt-1 text-[11px] leading-snug text-gray-400">{path}</div>
    </button>
  )
}

function Summary({ label, value }) {
  return (
    <div>
      <div className="text-[11px] text-gray-400">{label}</div>
      <div className="text-base font-extrabold text-indigo">{value}</div>
    </div>
  )
}
