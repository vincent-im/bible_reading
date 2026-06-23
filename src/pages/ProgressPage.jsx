import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import useMembers from '../hooks/useMembers'
import { computeMemberStats } from '../hooks/usePlan'
import { getLevel } from '../components/Progress/LevelBadge'
import ProgressChart from '../components/Progress/ProgressChart'

export default function ProgressPage() {
  const { members } = useMembers()

  const rows = useMemo(() => {
    return members
      .map((m) => {
        const stats = computeMemberStats(m)
        const level = getLevel(stats.percent)
        const target = stats.hasPlan
          ? Math.round((stats.expectedCount / stats.totalChapters) * 100)
          : 0
        return { member: m, stats, level, target }
      })
      .sort((a, b) => b.stats.percent - a.stats.percent)
  }, [members])

  const chartData = rows.map((r) => ({
    name: r.member.name,
    percent: r.stats.percent,
    target: r.target,
    color: r.level.color,
    emoji: r.level.emoji,
    readCount: r.stats.readCount,
  }))

  if (members.length === 0) {
    return (
      <div className="rounded-2xl bg-white p-8 text-center shadow-sm">
        <div className="text-4xl">📊</div>
        <p className="mt-3 font-bold text-gray-700">아직 데이터가 없어요</p>
        <p className="mt-1 text-sm text-gray-400">
          순원을 추가하고 통독을 시작해보세요
        </p>
        <Link
          to="/"
          className="mt-4 inline-block rounded-xl bg-indigo px-5 py-2.5 text-sm font-semibold text-white shadow-md transition active:scale-95"
        >
          홈으로 가기
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <header className="px-1">
        <h1 className="text-xl font-extrabold text-gray-800">📊 순원별 진도</h1>
        <p className="mt-0.5 text-sm text-gray-400">
          계획 대비 달성도를 한눈에 비교해요
        </p>
      </header>

      {/* 차트 */}
      <ProgressChart data={chartData} />

      {/* 순위 리스트 */}
      <section className="space-y-2">
        <h2 className="px-1 text-sm font-bold text-gray-700">달성 순위</h2>
        {rows.map((r, i) => (
          <RankRow key={r.member.id} rank={i + 1} {...r} />
        ))}
      </section>
    </div>
  )
}

function RankRow({ rank, member, stats, level }) {
  const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : null

  let statusEl
  if (!stats.hasPlan) {
    statusEl = <span className="text-gray-400">계획 미설정</span>
  } else if (stats.aheadCount > 0) {
    statusEl = (
      <span className="text-blue-500">🚀 {stats.aheadCount}장 앞서가요</span>
    )
  } else if (stats.behindCount > 0) {
    statusEl = (
      <span className="text-orange-400">⏰ {stats.behindCount}장 밀렸어요</span>
    )
  } else {
    statusEl = <span className="text-green-500">👍 순항 중</span>
  }

  return (
    <div className="flex items-center gap-3 rounded-2xl bg-white p-3.5 shadow-sm">
      {/* 순위 */}
      <div className="flex w-7 shrink-0 justify-center">
        {medal ? (
          <span className="text-xl">{medal}</span>
        ) : (
          <span className="text-sm font-bold text-gray-300">{rank}</span>
        )}
      </div>

      {/* 아바타 + 레벨 이모지 */}
      <div className="relative shrink-0">
        <span className="flex h-11 w-11 items-center justify-center rounded-full bg-cream text-2xl">
          {member.avatar || '🙂'}
        </span>
        <span className="absolute -bottom-1 -right-1 text-base">
          {level.emoji}
        </span>
      </div>

      {/* 이름 + 상태 */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="truncate font-bold text-gray-800">
            {member.name}
          </span>
          <span
            className="rounded-full px-1.5 py-0.5 text-[10px] font-bold"
            style={{
              color: level.color,
              backgroundColor: `${level.color}1A`,
            }}
          >
            {level.name}
          </span>
        </div>
        <div className="mt-0.5 text-xs">{statusEl}</div>
      </div>

      {/* 퍼센트 */}
      <div className="shrink-0 text-right">
        <div
          className="text-lg font-extrabold"
          style={{ color: level.color }}
        >
          {Math.floor(stats.percent)}%
        </div>
        <div className="text-[10px] text-gray-400">{stats.readCount}장</div>
      </div>
    </div>
  )
}
