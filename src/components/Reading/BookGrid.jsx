import { useState } from 'react'
import ChapterBubble from './ChapterBubble'

// 한 권의 장 라디오버튼 그리드 (접기/펼치기)
export default function BookGrid({
  book,
  statusFor,
  onToggle,
  defaultOpen = false,
}) {
  const [open, setOpen] = useState(defaultOpen)

  const chapters = Array.from({ length: book.chapters }, (_, i) => i + 1)

  let readCount = 0
  let todayCount = 0
  let overdueCount = 0
  const statuses = chapters.map((ch) => {
    const st = statusFor(book.id, ch)
    if (st === 'read') readCount++
    else if (st === 'today') todayCount++
    else if (st === 'overdue') overdueCount++
    return st
  })

  const allRead = readCount === book.chapters

  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-sm">
      {/* 헤더 */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left transition active:bg-gray-50"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-gray-800">{book.name}</span>
          {allRead && <span className="text-sm">✅</span>}
          {todayCount > 0 && (
            <span className="inline-flex h-4 items-center rounded-full bg-red-100 px-1.5 text-[10px] font-bold text-red-500">
              오늘 {todayCount}
            </span>
          )}
          {overdueCount > 0 && (
            <span className="inline-flex h-4 items-center rounded-full bg-orange-100 px-1.5 text-[10px] font-bold text-orange-400">
              밀림 {overdueCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">
            {readCount}/{book.chapters}
          </span>
          <span
            className={`text-gray-300 transition-transform ${open ? 'rotate-90' : ''}`}
          >
            ›
          </span>
        </div>
      </button>

      {/* 장 그리드 */}
      {open && (
        <div className="flex flex-wrap gap-1.5 px-4 pb-4 pt-1">
          {chapters.map((ch, i) => (
            <ChapterBubble
              key={ch}
              chapter={ch}
              status={statuses[i]}
              onClick={() => onToggle(book.id, ch)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
