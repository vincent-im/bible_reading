// 달성률 레벨 정의 (격려 메시지 포함)
export const LEVELS = [
  { min: 100, emoji: '😇', name: '완주', message: '완독을 축하해요!', color: '#6366F1' },
  { min: 90, emoji: '🔥', name: '불꽃', message: '마지막 스퍼트!', color: '#4F8DF1' },
  { min: 80, emoji: '👑', name: '왕관', message: '거의 다 왔어요!', color: '#3DA5D9' },
  { min: 65, emoji: '⭐', name: '별', message: '반짝반짝 빛나요!', color: '#34BFA3' },
  { min: 50, emoji: '☀️', name: '태양', message: '절반을 넘었어요!', color: '#7AC74F' },
  { min: 40, emoji: '🌸', name: '꽃', message: '아름답게 피었어요!', color: '#F7B500' },
  { min: 25, emoji: '🌷', name: '꽃봉오리', message: '곧 피어날 거예요!', color: '#FF9F43' },
  { min: 10, emoji: '🌿', name: '새싹', message: '쑥쑥 자라고 있어요!', color: '#FB8C5A' },
  { min: 0, emoji: '🌱', name: '씨앗', message: '시작이 반이에요!', color: '#F97362' },
]

export function getLevel(percent) {
  const p = Math.floor(percent || 0)
  return LEVELS.find((lv) => p >= lv.min) || LEVELS[LEVELS.length - 1]
}

const SIZES = {
  sm: { emoji: 'text-xl', name: 'text-xs', pad: 'px-2 py-1' },
  md: { emoji: 'text-3xl', name: 'text-sm', pad: 'px-3 py-1.5' },
  lg: { emoji: 'text-5xl', name: 'text-base', pad: 'px-4 py-2' },
}

export default function LevelBadge({
  percent,
  size = 'md',
  showName = true,
  showMessage = false,
  className = '',
}) {
  const level = getLevel(percent)
  const s = SIZES[size] || SIZES.md

  return (
    <div className={`inline-flex flex-col items-center ${className}`}>
      <div
        className={`flex items-center gap-2 rounded-full ${s.pad}`}
        style={{ backgroundColor: `${level.color}1A` }}
      >
        <span className={`${s.emoji} leading-none`} role="img" aria-label={level.name}>
          {level.emoji}
        </span>
        {showName && (
          <span
            className={`${s.name} font-bold`}
            style={{ color: level.color }}
          >
            {level.name}
          </span>
        )}
      </div>
      {showMessage && (
        <span className="mt-1.5 text-xs font-medium text-gray-500">
          {level.message}
        </span>
      )}
    </div>
  )
}
