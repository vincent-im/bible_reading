import { useState } from 'react'

// 설정 화면 진입용 간단 암호 게이트 (순장 전용).
// 라우트 이동 시 언마운트되므로 설정에 들어올 때마다 암호를 요구한다.
const SETTINGS_PASSWORD = 'jb'

export default function SettingsGate({ children }) {
  const [unlocked, setUnlocked] = useState(false)
  const [pass, setPass] = useState('')
  const [error, setError] = useState('')

  if (unlocked) return children

  const submit = (e) => {
    e.preventDefault()
    if (pass === SETTINGS_PASSWORD) {
      setError('')
      setUnlocked(true)
    } else {
      setError('암호가 올바르지 않아요.')
      setPass('')
    }
  }

  return (
    <div className="space-y-4">
      <header className="px-1">
        <h1 className="text-xl font-extrabold text-gray-800">⚙️ 설정</h1>
      </header>

      <div className="rounded-2xl bg-white p-6 text-center shadow-md">
        <div className="text-4xl">🔒</div>
        <p className="mt-3 font-bold text-gray-700">설정은 암호가 필요해요</p>
        <p className="mt-1 text-sm text-gray-400">순장님만 접근할 수 있어요</p>

        <form onSubmit={submit} className="mx-auto mt-5 max-w-xs space-y-3">
          <input
            type="password"
            inputMode="text"
            autoFocus
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            placeholder="암호"
            className="w-full rounded-xl border border-gray-200 bg-cream px-4 py-3 text-center text-base tracking-wider text-gray-800 outline-none transition focus:border-indigo focus:ring-2 focus:ring-indigo/20"
          />
          {error && (
            <p className="text-sm font-medium text-red-500">{error}</p>
          )}
          <button
            type="submit"
            disabled={!pass.trim()}
            className="w-full rounded-xl bg-indigo py-3 font-semibold text-white shadow-md transition active:scale-95 disabled:opacity-50"
          >
            확인
          </button>
        </form>
      </div>
    </div>
  )
}
