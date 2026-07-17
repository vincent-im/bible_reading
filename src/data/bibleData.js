// 성경 66권 데이터
// id: 1~39 = 구약(OT, 929장), 40~66 = 신약(NT, 260장), 합계 1189장
// testament: "OT"(구약) / "NT"(신약)

export const BIBLE_BOOKS = [
  // ── 구약 (Old Testament) 39권 / 929장 ──
  { id: 1, name: '창세기', chapters: 50, testament: 'OT' },
  { id: 2, name: '출애굽기', chapters: 40, testament: 'OT' },
  { id: 3, name: '레위기', chapters: 27, testament: 'OT' },
  { id: 4, name: '민수기', chapters: 36, testament: 'OT' },
  { id: 5, name: '신명기', chapters: 34, testament: 'OT' },
  { id: 6, name: '여호수아', chapters: 24, testament: 'OT' },
  { id: 7, name: '사사기', chapters: 21, testament: 'OT' },
  { id: 8, name: '룻기', chapters: 4, testament: 'OT' },
  { id: 9, name: '사무엘상', chapters: 31, testament: 'OT' },
  { id: 10, name: '사무엘하', chapters: 24, testament: 'OT' },
  { id: 11, name: '열왕기상', chapters: 22, testament: 'OT' },
  { id: 12, name: '열왕기하', chapters: 25, testament: 'OT' },
  { id: 13, name: '역대상', chapters: 29, testament: 'OT' },
  { id: 14, name: '역대하', chapters: 36, testament: 'OT' },
  { id: 15, name: '에스라', chapters: 10, testament: 'OT' },
  { id: 16, name: '느헤미야', chapters: 13, testament: 'OT' },
  { id: 17, name: '에스더', chapters: 10, testament: 'OT' },
  { id: 18, name: '욥기', chapters: 42, testament: 'OT' },
  { id: 19, name: '시편', chapters: 150, testament: 'OT' },
  { id: 20, name: '잠언', chapters: 31, testament: 'OT' },
  { id: 21, name: '전도서', chapters: 12, testament: 'OT' },
  { id: 22, name: '아가', chapters: 8, testament: 'OT' },
  { id: 23, name: '이사야', chapters: 66, testament: 'OT' },
  { id: 24, name: '예레미야', chapters: 52, testament: 'OT' },
  { id: 25, name: '예레미야애가', chapters: 5, testament: 'OT' },
  { id: 26, name: '에스겔', chapters: 48, testament: 'OT' },
  { id: 27, name: '다니엘', chapters: 12, testament: 'OT' },
  { id: 28, name: '호세아', chapters: 14, testament: 'OT' },
  { id: 29, name: '요엘', chapters: 3, testament: 'OT' },
  { id: 30, name: '아모스', chapters: 9, testament: 'OT' },
  { id: 31, name: '오바댜', chapters: 1, testament: 'OT' },
  { id: 32, name: '요나', chapters: 4, testament: 'OT' },
  { id: 33, name: '미가', chapters: 7, testament: 'OT' },
  { id: 34, name: '나훔', chapters: 3, testament: 'OT' },
  { id: 35, name: '하박국', chapters: 3, testament: 'OT' },
  { id: 36, name: '스바냐', chapters: 3, testament: 'OT' },
  { id: 37, name: '학개', chapters: 2, testament: 'OT' },
  { id: 38, name: '스가랴', chapters: 14, testament: 'OT' },
  { id: 39, name: '말라기', chapters: 4, testament: 'OT' },

  // ── 신약 (New Testament) 27권 / 260장 ──
  { id: 40, name: '마태복음', chapters: 28, testament: 'NT' },
  { id: 41, name: '마가복음', chapters: 16, testament: 'NT' },
  { id: 42, name: '누가복음', chapters: 24, testament: 'NT' },
  { id: 43, name: '요한복음', chapters: 21, testament: 'NT' },
  { id: 44, name: '사도행전', chapters: 28, testament: 'NT' },
  { id: 45, name: '로마서', chapters: 16, testament: 'NT' },
  { id: 46, name: '고린도전서', chapters: 16, testament: 'NT' },
  { id: 47, name: '고린도후서', chapters: 13, testament: 'NT' },
  { id: 48, name: '갈라디아서', chapters: 6, testament: 'NT' },
  { id: 49, name: '에베소서', chapters: 6, testament: 'NT' },
  { id: 50, name: '빌립보서', chapters: 4, testament: 'NT' },
  { id: 51, name: '골로새서', chapters: 4, testament: 'NT' },
  { id: 52, name: '데살로니가전서', chapters: 5, testament: 'NT' },
  { id: 53, name: '데살로니가후서', chapters: 3, testament: 'NT' },
  { id: 54, name: '디모데전서', chapters: 6, testament: 'NT' },
  { id: 55, name: '디모데후서', chapters: 4, testament: 'NT' },
  { id: 56, name: '디도서', chapters: 3, testament: 'NT' },
  { id: 57, name: '빌레몬서', chapters: 1, testament: 'NT' },
  { id: 58, name: '히브리서', chapters: 13, testament: 'NT' },
  { id: 59, name: '야고보서', chapters: 5, testament: 'NT' },
  { id: 60, name: '베드로전서', chapters: 5, testament: 'NT' },
  { id: 61, name: '베드로후서', chapters: 3, testament: 'NT' },
  { id: 62, name: '요한일서', chapters: 5, testament: 'NT' },
  { id: 63, name: '요한이서', chapters: 1, testament: 'NT' },
  { id: 64, name: '요한삼서', chapters: 1, testament: 'NT' },
  { id: 65, name: '유다서', chapters: 1, testament: 'NT' },
  { id: 66, name: '요한계시록', chapters: 22, testament: 'NT' },
]

// 빠른 조회용 맵 (id -> book)
export const BOOK_BY_ID = BIBLE_BOOKS.reduce((acc, b) => {
  acc[b.id] = b
  return acc
}, {})

export const OT_BOOKS = BIBLE_BOOKS.filter((b) => b.testament === 'OT')
export const NT_BOOKS = BIBLE_BOOKS.filter((b) => b.testament === 'NT')

export const OT_CHAPTERS = OT_BOOKS.reduce((s, b) => s + b.chapters, 0) // 929
export const NT_CHAPTERS = NT_BOOKS.reduce((s, b) => s + b.chapters, 0) // 260
export const TOTAL_CHAPTERS = OT_CHAPTERS + NT_CHAPTERS // 1189

// bible.json의 책 약칭 (id 1~66 순서와 동일)
export const BOOK_ABBRS = [
  '창', '출', '레', '민', '신', '수', '삿', '룻', '삼상', '삼하',
  '왕상', '왕하', '대상', '대하', '스', '느', '에', '욥', '시', '잠',
  '전', '아', '사', '렘', '애', '겔', '단', '호', '욜', '암',
  '옵', '욘', '미', '나', '합', '습', '학', '슥', '말',
  '마', '막', '눅', '요', '행', '롬', '고전', '고후', '갈', '엡',
  '빌', '골', '살전', '살후', '딤전', '딤후', '딛', '몬', '히', '약',
  '벧전', '벧후', '요일', '요이', '요삼', '유', '계',
]

// 약칭 -> book id
export const ABBR_TO_ID = BOOK_ABBRS.reduce((acc, ab, i) => {
  acc[ab] = i + 1
  return acc
}, {})

export function getAbbr(id) {
  return BOOK_ABBRS[id - 1]
}

export function getBook(id) {
  return BOOK_BY_ID[id]
}
