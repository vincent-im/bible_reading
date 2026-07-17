import { ABBR_TO_ID } from './bibleData'

// bible.json은 4.9MB이므로 최초 필요 시 1회만 fetch하여 메모리에 인덱싱한다.
// 인덱스 구조: { [bookId]: { [chapter]: [{ v: '절 라벨', t: '본문' }, ...] } }

let _promise = null

// "창1:1" / "삼상2:3" / "신6:18-19" / "요18:이" 모두 파싱
// 책 약칭(비숫자) + 장(숫자) + ':' + 절 라벨(나머지)
const KEY_RE = /^(\D+)(\d+):(.+)$/

function buildIndex(raw) {
  const index = {}
  for (const key of Object.keys(raw)) {
    const m = KEY_RE.exec(key)
    if (!m) continue
    const abbr = m[1]
    const chapter = Number(m[2])
    const verse = m[3]
    const bookId = ABBR_TO_ID[abbr]
    if (!bookId) continue
    if (!index[bookId]) index[bookId] = {}
    if (!index[bookId][chapter]) index[bookId][chapter] = []
    index[bookId][chapter].push({ v: verse, t: raw[key] })
  }
  return index
}

// 성경 인덱스를 반환하는 Promise (캐시됨). 실패 시 캐시를 비워 재시도 가능.
export function loadBibleIndex() {
  if (_promise) return _promise
  const url = `${import.meta.env.BASE_URL}bible.json`
  _promise = fetch(url)
    .then((res) => {
      if (!res.ok) throw new Error(`성경 데이터를 불러오지 못했어요 (${res.status})`)
      return res.json()
    })
    .then((raw) => buildIndex(raw))
    .catch((err) => {
      _promise = null // 다음에 재시도 가능하도록
      throw err
    })
  return _promise
}

// 이미 로드됐는지 여부 (프리페치 판단용)
export function isBibleLoaded() {
  return _promise !== null
}

export function getChapterVerses(index, bookId, chapter) {
  return index?.[bookId]?.[chapter] || []
}
