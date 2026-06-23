import { Route, Routes } from 'react-router-dom'
import BottomNav from './components/Layout/BottomNav'
import HomePage from './pages/HomePage'
import MyReadingPage from './pages/MyReadingPage'
import ProgressPage from './pages/ProgressPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <div className="relative min-h-screen w-full max-w-app bg-cream shadow-xl">
      {/* 콘텐츠 (하단 탭바 높이만큼 패딩) */}
      <main className="px-4 pb-28 pt-5">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/reading" element={<MyReadingPage />} />
          <Route path="/progress" element={<ProgressPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<HomePage />} />
        </Routes>
      </main>

      <BottomNav />
    </div>
  )
}
