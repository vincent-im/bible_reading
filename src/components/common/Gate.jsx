import { useState } from 'react'
import { useApp } from '../../contexts/AppContext'

// 공용 DB 접속용 공유 암호 게이트
export default function Gate() {
  const { unlock, status, error } = useApp()
  const [pass, setPass] = useState('')
  const loading = status === 'loading'

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!pass.trim() || loading) return
    unlock(pass.trim())
  }

  return (
    <div className="flex min-h-screen w-full max-w-app flex-col justify-center bg-cream px-6">
      <div className="rounded-3xl bg-white p-7 shadow-md">
        <div className="text-center">
          <div className="text-5xl">📖</div>
          <h1 className="mt-3 text-xl font-extrabold text-gray-800">
            예본6여 성경통독
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            다락방 공유 암호를 입력해주세요
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-3">
          <input
            type="password"
            inputMode="text"
            autoFocus
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            placeholder="공유 암호"
            className="w-full rounded-xl border border-gray-200 bg-cream px-4 py-3 text-center text-base tracking-wider text-gray-800 outline-none transition focus:border-indigo focus:ring-2 focus:ring-indigo/20"
          />

          {error && (
            <p className="text-center text-sm font-medium text-red-500">{error}</p>
          )}

          <button
            type="submit"
            disabled={!pass.trim() || loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo py-3 font-semibold text-white shadow-md transition active:scale-95 disabled:opacity-50"
          >
            {loading ? (
              <>
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                연결 중…
              </>
            ) : (
              '입장하기'
            )}
          </button>
        </form>

        <p className="mt-5 text-center text-[11px] leading-relaxed text-gray-400">
          암호는 순장님께 문의하세요.
          <br />
          같은 암호를 쓰는 순원끼리 통독 현황을 함께 봅니다.
        </p>
      </div>
    </div>
  )
}
