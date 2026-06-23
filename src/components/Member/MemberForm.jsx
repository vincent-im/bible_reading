import { useState } from 'react'

// 순원 추가/편집 폼
export default function MemberForm({
  initialName = '',
  onSubmit,
  onCancel,
  submitLabel = '추가',
}) {
  const [name, setName] = useState(initialName)
  const trimmed = name.trim()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!trimmed) return
    onSubmit?.(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1.5 block text-sm font-semibold text-gray-700">
          순원 이름
        </label>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="예) 김믿음"
          maxLength={20}
          className="w-full rounded-xl border border-gray-200 bg-cream px-4 py-3 text-base text-gray-800 outline-none transition focus:border-indigo focus:ring-2 focus:ring-indigo/20"
        />
      </div>
      <div className="flex gap-2">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 rounded-xl bg-gray-100 py-3 font-semibold text-gray-600 transition active:scale-95"
          >
            취소
          </button>
        )}
        <button
          type="submit"
          disabled={!trimmed}
          className="flex-1 rounded-xl bg-indigo py-3 font-semibold text-white shadow-md transition active:scale-95 disabled:opacity-40"
        >
          {submitLabel}
        </button>
      </div>
    </form>
  )
}
