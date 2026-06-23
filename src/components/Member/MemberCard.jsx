import { getLevel } from '../Progress/LevelBadge'

// 홈 화면의 순원 카드 (달성 현황 요약)
export default function MemberCard({ member, stats, onClick }) {
  const level = getLevel(stats?.percent ?? 0)
  const percent = stats?.percent ?? 0
  const hasPlan = stats?.hasPlan

  return (
    <button
      onClick={onClick}
      className="w-full rounded-2xl bg-white p-4 text-left shadow-md transition active:scale-[0.98]"
    >
      <div className="flex items-center gap-3">
        {/* 아바타 */}
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-cream text-2xl">
          {member.avatar || '🙂'}
        </div>

        {/* 이름 + 상태 */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <span className="truncate text-base font-bold text-gray-800">
              {member.name}
            </span>
            <span className="text-lg" title={level.name}>
              {level.emoji}
            </span>
          </div>
          {hasPlan ? (
            <div className="mt-0.5 text-xs text-gray-500">
              {stats.todayTotal > 0 ? (
                <>
                  오늘{' '}
                  <span
                    className={
                      stats.todayDone >= stats.todayTotal
                        ? 'font-semibold text-blue-500'
                        : 'font-semibold text-red-500'
                    }
                  >
                    {stats.todayDone}/{stats.todayTotal}장
                  </span>
                  {stats.behindCount > 0 && (
                    <span className="ml-1 text-orange-400">
                      · 밀린 {stats.behindCount}장
                    </span>
                  )}
                </>
              ) : (
                <span className="text-gray-400">통독 기간이 아니에요</span>
              )}
            </div>
          ) : (
            <div className="mt-0.5 text-xs text-gray-400">계획 미설정</div>
          )}
        </div>

        {/* 퍼센트 */}
        <div className="shrink-0 text-right">
          <div
            className="text-lg font-extrabold"
            style={{ color: level.color }}
          >
            {Math.floor(percent)}%
          </div>
          <div className="text-[10px] text-gray-400">
            {stats?.readCount ?? 0}/{stats?.totalChapters ?? 1189}장
          </div>
        </div>
      </div>

      {/* 진행 바 */}
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${Math.min(100, percent)}%`,
            backgroundColor: level.color,
          }}
        />
      </div>
    </button>
  )
}
