import { NavLink } from 'react-router-dom'

const TABS = [
  { to: '/', label: '홈', icon: '🏠', end: true },
  { to: '/reading', label: '내 통독', icon: '📖' },
  { to: '/progress', label: '진도', icon: '📊' },
  { to: '/settings', label: '설정', icon: '⚙️' },
]

export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-1/2 z-40 w-full max-w-app -translate-x-1/2 border-t border-gray-100 bg-white/95 backdrop-blur-md">
      <ul className="flex">
        {TABS.map((tab) => (
          <li key={tab.to} className="flex-1">
            <NavLink
              to={tab.to}
              end={tab.end}
              className={({ isActive }) =>
                [
                  'flex flex-col items-center gap-0.5 py-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))] text-[11px] font-medium transition',
                  isActive ? 'text-indigo' : 'text-gray-400',
                ].join(' ')
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`text-xl transition-transform ${
                      isActive ? 'scale-110' : ''
                    }`}
                  >
                    {tab.icon}
                  </span>
                  <span>{tab.label}</span>
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
