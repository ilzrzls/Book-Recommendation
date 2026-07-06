/**
 * 默认头像生成器
 * 当用户没有自定义头像时，生成统一风格的圆形字母头像 (SVG data URI)
 *
 * 设计规范：
 *   - 背景色：导航栏同款深蓝 #2C3E50
 *   - 文字色：金色 #D4A24C（与 Logo 色调一致）
 *   - 文字严格居中（text-anchor="middle" + dominant-baseline="central"）
 */

const BG_COLOR = '#2C3E50'
const FG_COLOR = '#D4A24C'

/**
 * 获取用户名的首字符 (中文取第一个字, 英文取首字母大写)
 */
function getInitial(name) {
  const str = String(name || '').trim()
  if (!str) return '?'
  if (/[一-鿿]/.test(str[0])) {
    return str[0]
  }
  return str[0].toUpperCase()
}

/**
 * 生成默认头像 SVG data URI
 * @param {string} username - 用户名
 * @returns {string} SVG data URI (可直接用作 img src)
 */
export function generateDefaultAvatar(username) {
  const initial = getInitial(username)

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="100" fill="${BG_COLOR}"/>
  <text x="100" y="100" fill="${FG_COLOR}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif" font-size="90" font-weight="600" text-anchor="middle" dominant-baseline="central" alignment-baseline="central">${initial}</text>
</svg>`

  // base64 编码：避免 encodeURIComponent 对特殊 Unicode 字符抛出 URIError
  const bytes = new TextEncoder().encode(svg)
  const binary = String.fromCharCode(...bytes)
  return 'data:image/svg+xml;base64,' + btoa(binary)
}

/**
 * 获取头像 URL — 有自定义头像则返回原 URL，否则生成默认头像
 * @param {string|null|undefined} avatarUrl - 数据库中存储的头像 URL
 * @param {string} username - 用户名 (用于生成默认头像)
 * @returns {string} 可用的头像 URL
 */
export function getAvatarUrl(avatarUrl, username) {
  if (avatarUrl && avatarUrl.trim()) {
    return avatarUrl
  }
  return generateDefaultAvatar(username)
}
