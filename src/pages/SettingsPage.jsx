import { useRef, useState } from 'react'
import useMembers from '../hooks/useMembers'
import { useApp } from '../contexts/AppContext'
import { computeMemberStats } from '../hooks/usePlan'
import Modal from '../components/common/Modal'
import MemberForm from '../components/Member/MemberForm'

export default function SettingsPage() {
  const { members, addMember, updateMember, removeMember, resetProgress } =
    useMembers()
  const { setMembers } = useApp()
  const fileRef = useRef(null)

  const [editing, setEditing] = useState(null) // member or null
  const [adding, setAdding] = useState(false)
  const [confirm, setConfirm] = useState(null) // { type, member } | { type:'clearAll' }
  const [toast, setToast] = useState('')

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(''), 2000)
  }

  const handleExport = () => {
    const data = JSON.stringify({ members }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `예본6여통독_백업_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    showToast('백업 파일을 내보냈어요')
  }

  const handleImportFile = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(reader.result)
        if (parsed && Array.isArray(parsed.members)) {
          setMembers(parsed.members)
          showToast('데이터를 가져왔어요')
        } else {
          showToast('올바른 백업 파일이 아니에요')
        }
      } catch {
        showToast('파일을 읽을 수 없어요')
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  const doConfirm = () => {
    if (!confirm) return
    if (confirm.type === 'delete') {
      removeMember(confirm.member.id)
      showToast('순원을 삭제했어요')
    } else if (confirm.type === 'reset') {
      resetProgress(confirm.member.id)
      showToast('진도를 초기화했어요')
    } else if (confirm.type === 'clearAll') {
      setMembers([])
      showToast('모든 데이터를 초기화했어요')
    }
    setConfirm(null)
  }

  return (
    <div className="space-y-5">
      <header className="px-1">
        <h1 className="text-xl font-extrabold text-gray-800">⚙️ 설정</h1>
      </header>

      {/* 순원 관리 */}
      <Section title="순원 관리">
        <div className="space-y-2">
          {members.length === 0 && (
            <p className="py-4 text-center text-sm text-gray-400">
              등록된 순원이 없어요
            </p>
          )}
          {members.map((m) => {
            const stats = computeMemberStats(m)
            return (
              <div
                key={m.id}
                className="flex items-center gap-3 rounded-xl border border-gray-100 p-3"
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-cream text-xl">
                  {m.avatar || '🙂'}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-bold text-gray-800">
                    {m.name}
                  </div>
                  <div className="text-[11px] text-gray-400">
                    {Math.floor(stats.percent)}% · {stats.readCount}장 읽음
                  </div>
                </div>
                <button
                  onClick={() => setEditing(m)}
                  className="rounded-lg bg-gray-100 px-2.5 py-1.5 text-xs font-medium text-gray-600 transition active:scale-95"
                >
                  편집
                </button>
                <button
                  onClick={() => setConfirm({ type: 'reset', member: m })}
                  className="rounded-lg bg-amber-50 px-2.5 py-1.5 text-xs font-medium text-amber-500 transition active:scale-95"
                >
                  초기화
                </button>
                <button
                  onClick={() => setConfirm({ type: 'delete', member: m })}
                  className="rounded-lg bg-red-50 px-2.5 py-1.5 text-xs font-medium text-red-500 transition active:scale-95"
                >
                  삭제
                </button>
              </div>
            )
          })}
          <button
            onClick={() => setAdding(true)}
            className="w-full rounded-xl border border-dashed border-indigo/40 py-2.5 text-sm font-semibold text-indigo transition active:scale-95"
          >
            + 순원 추가
          </button>
        </div>
      </Section>

      {/* 데이터 관리 */}
      <Section title="데이터 관리">
        <p className="mb-3 text-xs text-gray-400">
          모든 데이터는 이 기기에만 저장돼요. 기기를 바꾸거나 백업하려면
          내보내기를 이용하세요.
        </p>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={handleExport}
            className="rounded-xl bg-indigo/10 py-2.5 text-sm font-semibold text-indigo transition active:scale-95"
          >
            ⬇️ 백업 내보내기
          </button>
          <button
            onClick={() => fileRef.current?.click()}
            className="rounded-xl bg-indigo/10 py-2.5 text-sm font-semibold text-indigo transition active:scale-95"
          >
            ⬆️ 백업 가져오기
          </button>
        </div>
        <input
          ref={fileRef}
          type="file"
          accept="application/json,.json"
          onChange={handleImportFile}
          className="hidden"
        />
        <button
          onClick={() => setConfirm({ type: 'clearAll' })}
          className="mt-2 w-full rounded-xl bg-red-50 py-2.5 text-sm font-semibold text-red-500 transition active:scale-95"
        >
          전체 데이터 초기화
        </button>
      </Section>

      {/* 앱 정보 */}
      <Section title="앱 정보">
        <div className="space-y-1 text-sm text-gray-500">
          <InfoRow label="앱 이름" value="예본6여 성경통독" />
          <InfoRow label="버전" value="1.0.0" />
          <InfoRow label="전체 장수" value="1,189장 (구약 929 · 신약 260)" />
          <InfoRow label="저장 방식" value="오프라인 (localStorage)" />
        </div>
        <p className="mt-3 text-center text-[11px] text-gray-400">
          순장과 순원들의 은혜로운 통독을 응원해요 🙏
        </p>
      </Section>

      {/* 편집 모달 */}
      <Modal open={!!editing} onClose={() => setEditing(null)} title="순원 이름 편집">
        {editing && (
          <MemberForm
            initialName={editing.name}
            submitLabel="저장"
            onSubmit={(name) => {
              updateMember(editing.id, { name })
              setEditing(null)
              showToast('이름을 수정했어요')
            }}
            onCancel={() => setEditing(null)}
          />
        )}
      </Modal>

      {/* 추가 모달 */}
      <Modal open={adding} onClose={() => setAdding(false)} title="순원 추가">
        <MemberForm
          submitLabel="추가하기"
          onSubmit={(name) => {
            addMember(name)
            setAdding(false)
            showToast('순원을 추가했어요')
          }}
          onCancel={() => setAdding(false)}
        />
      </Modal>

      {/* 확인 모달 */}
      <Modal
        open={!!confirm}
        onClose={() => setConfirm(null)}
        title="확인"
        footer={
          <div className="flex gap-2">
            <button
              onClick={() => setConfirm(null)}
              className="flex-1 rounded-xl bg-gray-100 py-3 font-semibold text-gray-600 transition active:scale-95"
            >
              취소
            </button>
            <button
              onClick={doConfirm}
              className="flex-1 rounded-xl bg-red-500 py-3 font-semibold text-white transition active:scale-95"
            >
              확인
            </button>
          </div>
        }
      >
        <p className="text-sm text-gray-600">
          {confirm?.type === 'delete' &&
            `'${confirm.member.name}' 순원을 삭제할까요? 통독 기록도 함께 삭제돼요.`}
          {confirm?.type === 'reset' &&
            `'${confirm.member.name}' 순원의 통독 진도를 모두 초기화할까요?`}
          {confirm?.type === 'clearAll' &&
            '모든 순원과 통독 기록이 삭제돼요. 정말 초기화할까요?'}
        </p>
      </Modal>

      {/* 토스트 */}
      {toast && (
        <div className="fixed bottom-24 left-1/2 z-50 -translate-x-1/2 animate-pop-in rounded-full bg-gray-800 px-4 py-2 text-sm text-white shadow-lg">
          {toast}
        </div>
      )}
    </div>
  )
}

function Section({ title, children }) {
  return (
    <section className="rounded-2xl bg-white p-4 shadow-md">
      <h2 className="mb-3 text-sm font-bold text-gray-700">{title}</h2>
      {children}
    </section>
  )
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="font-medium text-gray-600">{value}</span>
    </div>
  )
}
