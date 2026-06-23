import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useMembers from '../hooks/useMembers'
import { computeMemberStats } from '../hooks/usePlan'
import MemberCard from '../components/Member/MemberCard'
import MemberForm from '../components/Member/MemberForm'
import Modal from '../components/common/Modal'

export default function HomePage() {
  const { members, addMember, selectMember } = useMembers()
  const navigate = useNavigate()
  const [showAdd, setShowAdd] = useState(false)

  const rows = useMemo(
    () =>
      members.map((m) => ({ member: m, stats: computeMemberStats(m) })),
    [members]
  )

  const avg =
    rows.length > 0
      ? Math.round(
          rows.reduce((s, r) => s + r.stats.percent, 0) / rows.length
        )
      : 0

  const handleSelect = (id) => {
    selectMember(id)
    navigate('/reading')
  }

  const handleAdd = (name) => {
    const id = addMember(name)
    setShowAdd(false)
    if (id) handleSelect(id)
  }

  return (
    <div className="space-y-4">
      {/* 헤더 */}
      <header className="rounded-2xl bg-gradient-to-br from-indigo to-violet-500 p-5 text-white shadow-md">
        <h1 className="text-xl font-extrabold">📖 다락방 성경통독</h1>
        <p className="mt-1 text-sm opacity-90">
          순원들과 함께 말씀으로 채워가요
        </p>
        {rows.length > 0 && (
          <div className="mt-4 flex items-center gap-4">
            <div>
              <div className="text-2xl font-extrabold">{rows.length}명</div>
              <div className="text-[11px] opacity-80">참여 순원</div>
            </div>
            <div className="h-8 w-px bg-white/30" />
            <div>
              <div className="text-2xl font-extrabold">{avg}%</div>
              <div className="text-[11px] opacity-80">평균 달성률</div>
            </div>
          </div>
        )}
      </header>

      {/* 순원 목록 */}
      <section>
        <div className="mb-2 flex items-center justify-between px-1">
          <h2 className="text-sm font-bold text-gray-700">순원 현황</h2>
          <button
            onClick={() => setShowAdd(true)}
            className="rounded-full bg-indigo px-3 py-1.5 text-xs font-semibold text-white shadow transition active:scale-95"
          >
            + 순원 추가
          </button>
        </div>

        {rows.length === 0 ? (
          <EmptyState onAdd={() => setShowAdd(true)} />
        ) : (
          <div className="space-y-3">
            {rows.map(({ member, stats }) => (
              <MemberCard
                key={member.id}
                member={member}
                stats={stats}
                onClick={() => handleSelect(member.id)}
              />
            ))}
          </div>
        )}
      </section>

      <p className="px-1 pt-2 text-center text-[11px] text-gray-400">
        순원을 선택하면 본인의 통독 현황을 확인하고 업데이트할 수 있어요
      </p>

      {/* 순원 추가 모달 */}
      <Modal
        open={showAdd}
        onClose={() => setShowAdd(false)}
        title="순원 추가"
      >
        <MemberForm
          submitLabel="추가하기"
          onSubmit={handleAdd}
          onCancel={() => setShowAdd(false)}
        />
      </Modal>
    </div>
  )
}

function EmptyState({ onAdd }) {
  return (
    <div className="rounded-2xl bg-white p-8 text-center shadow-sm">
      <div className="text-4xl">🌱</div>
      <p className="mt-3 font-bold text-gray-700">아직 순원이 없어요</p>
      <p className="mt-1 text-sm text-gray-400">
        첫 순원을 추가하고 통독을 시작해보세요
      </p>
      <button
        onClick={onAdd}
        className="mt-4 rounded-xl bg-indigo px-5 py-2.5 text-sm font-semibold text-white shadow-md transition active:scale-95"
      >
        + 순원 추가하기
      </button>
    </div>
  )
}
