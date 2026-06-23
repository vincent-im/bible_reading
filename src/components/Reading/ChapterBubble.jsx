// 개별 장 버튼 (동그라미 숫자 라디오버튼)
// status: 'read' | 'today' | 'overdue' | 'future'
const STATUS_CLASS = {
  future: 'bg-gray-100 text-gray-500',
  today: 'bg-red-100 text-red-600 border-2 border-red-400 animate-blink font-bold',
  read: 'bg-blue-500 text-white shadow-sm',
  overdue: 'bg-orange-100 text-orange-400 border border-orange-200',
}

export default function ChapterBubble({ chapter, status = 'future', onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={status === 'read'}
      title={`${chapter}장`}
      className={[
        'flex h-9 w-9 items-center justify-center rounded-full text-xs transition active:scale-90',
        STATUS_CLASS[status] || STATUS_CLASS.future,
      ].join(' ')}
    >
      {chapter}
    </button>
  )
}
