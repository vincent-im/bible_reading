import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

// 가로 막대 오른쪽 끝의 레벨 이모지 라벨
function EmojiLabel({ x, y, width, height, value }) {
  if (value == null) return null
  return (
    <text
      x={x + width + 6}
      y={y + height / 2}
      textAnchor="start"
      dominantBaseline="central"
      fontSize="15"
    >
      {value}
    </text>
  )
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null
  const d = payload[0].payload
  return (
    <div className="rounded-xl border border-gray-100 bg-white px-3 py-2 text-xs shadow-lg">
      <div className="font-bold text-gray-800">
        {d.emoji} {label}
      </div>
      <div className="mt-1 text-gray-500">
        달성률 <span className="font-semibold text-indigo">{d.percent}%</span>
      </div>
      <div className="text-gray-500">
        목표(오늘까지){' '}
        <span className="font-semibold text-gray-600">{d.target}%</span>
      </div>
      <div className="text-gray-400">{d.readCount}장 읽음</div>
    </div>
  )
}

// 순원별 달성률 비교 (가로 막대: 이름=세로축, 진도율=가로축)
// data: [{ name, percent, target, color, emoji, readCount }]
export default function ProgressChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-2xl bg-white text-sm text-gray-400 shadow-sm">
        표시할 진도가 없어요
      </div>
    )
  }

  // 순원마다 한 줄씩 차지 → 이름이 겹치지 않음
  const height = Math.max(160, data.length * 42 + 44)

  return (
    <div className="rounded-2xl bg-white p-4 pt-5 shadow-md">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          layout="vertical"
          data={data}
          margin={{ top: 4, right: 34, left: 4, bottom: 4 }}
          barGap={2}
        >
          {/* 진도율 (가로축) */}
          <XAxis
            type="number"
            domain={[0, 100]}
            ticks={[0, 25, 50, 75, 100]}
            tick={{ fontSize: 11, fill: '#9ca3af' }}
            axisLine={false}
            tickLine={false}
            unit="%"
          />
          {/* 순원 이름 (세로축) */}
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 12, fill: '#374151' }}
            axisLine={false}
            tickLine={false}
            width={64}
            interval={0}
          />
          <Tooltip
            content={<ChartTooltip />}
            cursor={{ fill: 'rgba(99,102,241,0.06)' }}
          />
          {/* 오늘까지 목표 (계획 대비 비교용) */}
          <Bar
            dataKey="target"
            fill="#E5E7EB"
            radius={[0, 6, 6, 0]}
            maxBarSize={13}
          />
          {/* 실제 달성률 */}
          <Bar dataKey="percent" radius={[0, 6, 6, 0]} maxBarSize={13}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
            <LabelList dataKey="emoji" content={<EmojiLabel />} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* 범례 */}
      <div className="mt-2 flex items-center justify-center gap-4 text-[11px] text-gray-400">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-indigo" />
          달성률
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2.5 w-2.5 rounded-sm bg-gray-200" />
          오늘까지 목표
        </span>
      </div>
    </div>
  )
}
