import { Route, Routes } from 'react-router-dom'
import { useApp } from './contexts/AppContext'
import BottomNav from './components/Layout/BottomNav'
import Gate from './components/common/Gate'
import SettingsGate from './components/common/SettingsGate'
import HomePage from './pages/HomePage'
import MyReadingPage from './pages/MyReadingPage'
import ProgressPage from './pages/ProgressPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  const { mode, status } = useApp()

  // 공용 DB 모드: 공유 암호로 잠금 해제되기 전까지 게이트 화면
  if (mode === 'remote' && status !== 'ready') {
    return <Gate />
  }

  return (
    <div className="relative min-h-screen w-full max-w-app bg-cream shadow-xl">
      {/* 콘텐츠 (하단 탭바 높이만큼 패딩) */}
      <main className="px-4 pb-28 pt-5">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/reading" element={<MyReadingPage />} />
          <Route path="/progress" element={<ProgressPage />} />
          <Route
            path="/settings"
            element={
              <SettingsGate>
                <SettingsPage />
              </SettingsGate>
            }
          />
          <Route path="*" element={<HomePage />} />
        </Routes>
      </main>

      <BottomNav />
    </div>
  )
}
