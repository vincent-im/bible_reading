import { useEffect, useState } from 'react'
import { getBook } from '../../data/bibleData'
import { loadBibleIndex, getChapterVerses } from '../../data/bibleText'

// 성경 본문 팝업 (성경 바로읽기 모드)
// bookId/chapter의 본문을 보여주고, '완료' 시 읽음 처리 + 닫기
export default function BibleReaderModal({
  open,
  bookId,
  chapter,
  isRead,
  onComplete,
  onUnread,
  onClose,
}) {
  const [status, setStatus] = useState({ loading: true, error: null, verses: [] })

  useEffect(() => {
    if (!open) return
    let alive = true
    setStatus({ loading: true, error: null, verses: [] })
    loadBibleIndex()
      .then((index) => {
        if (!alive) return
        setStatus({
          loading: false,
          error: null,
          verses: getChapterVerses(index, bookId, chapter),
        })
      })
      .catch((err) => {
        if (!alive) return
        setStatus({ loading: false, error: err.message, verses: [] })
      })
    return () => {
      alive = false
    }
  }, [open, bookId, chapter])

  // 배경 스크롤 잠금 + ESC 닫기
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose?.()
    document.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [open, onClose])

  if (!open) return null

  const book = getBook(bookId)
  const title = book ? `${book.name} ${chapter}장` : `${chapter}장`

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center"
      role="dialog"
      aria-modal="true"
    >
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[1px]" onClick={onClose} />

      <div className="relative z-10 flex max-h-[90vh] w-full max-w-app flex-col rounded-t-3xl bg-cream shadow-2xl animate-pop-in">
        {/* 헤더 */}
        <div className="shrink-0 rounded-t-3xl bg-white px-5 pb-3 pt-3">
          <div className="mx-auto mb-3 h-1.5 w-10 rounded-full bg-gray-200" />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">📖</span>
              <h2 className="text-lg font-extrabold text-gray-800">{title}</h2>
              {isRead && (
                <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-bold text-blue-500">
                  읽음
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-gray-500 transition active:scale-90"
              aria-label="닫기"
            >
              ✕
            </button>
          </div>
        </div>

        {/* 본문 */}
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          {status.loading && (
            <div className="flex h-40 flex-col items-center justify-center gap-3 text-gray-400">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo/30 border-t-indigo" />
              <span className="text-sm">성경 본문을 불러오는 중…</span>
            </div>
          )}

          {status.error && (
            <div className="flex h-40 flex-col items-center justify-center gap-2 text-center text-gray-500">
              <span className="text-3xl">😢</span>
              <p className="text-sm">{status.error}</p>
              <p className="text-xs text-gray-400">
                인터넷 연결을 확인한 뒤 다시 열어주세요.
              </p>
            </div>
          )}

          {!status.loading && !status.error && status.verses.length === 0 && (
            <div className="flex h-40 items-center justify-center text-sm text-gray-400">
              본문을 찾을 수 없어요.
            </div>
          )}

          {!status.loading && !status.error && status.verses.length > 0 && (
            <div className="space-y-2.5 leading-relaxed">
              {status.verses.map((verse, i) => (
                <p key={i} className="text-[15px] text-gray-700">
                  <span className="mr-1.5 align-top text-xs font-bold text-indigo">
                    {verse.v}
                  </span>
                  {verse.t?.trim()}
                </p>
              ))}
            </div>
          )}
        </div>

        {/* 하단 액션 */}
        <div className="shrink-0 border-t border-gray-100 bg-white px-5 pb-[calc(0.75rem+env(safe-area-inset-bottom))] pt-3">
          {isRead ? (
            <div className="flex gap-2">
              <button
                onClick={onUnread}
                className="flex-1 rounded-xl bg-gray-100 py-3 font-semibold text-gray-600 transition active:scale-95"
              >
                읽음 취소
              </button>
              <button
                onClick={onClose}
                className="flex-1 rounded-xl bg-indigo py-3 font-semibold text-white shadow-md transition active:scale-95"
              >
                닫기
              </button>
            </div>
          ) : (
            <button
              onClick={onComplete}
              disabled={status.loading || !!status.error}
              className="w-full rounded-xl bg-indigo py-3.5 font-bold text-white shadow-md transition active:scale-95 disabled:opacity-40"
            >
              ✓ 완료 (읽음으로 표시)
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
