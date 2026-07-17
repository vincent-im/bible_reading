// '설정' 탭 진입용 암호 관리 (이 기기 localStorage에 저장)
const KEY = 'bible_settings_pw'
export const DEFAULT_SETTINGS_PW = 'jb'

export function getSettingsPassword() {
  try {
    return localStorage.getItem(KEY) || DEFAULT_SETTINGS_PW
  } catch {
    return DEFAULT_SETTINGS_PW
  }
}

export function setSettingsPassword(pw) {
  try {
    localStorage.setItem(KEY, pw)
  } catch {
    /* 무시 */
  }
}

// 초기 암호('jb')로 되돌리기
export function resetSettingsPassword() {
  try {
    localStorage.removeItem(KEY)
  } catch {
    /* 무시 */
  }
}
