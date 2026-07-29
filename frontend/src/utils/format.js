/**
 * Format a date string or timestamp
 */
export function formatDate(date, fmt = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) return '-'
  const d = new Date(date)
  const o = {
    'YYYY': d.getFullYear(),
    'MM': String(d.getMonth() + 1).padStart(2, '0'),
    'DD': String(d.getDate()).padStart(2, '0'),
    'HH': String(d.getHours()).padStart(2, '0'),
    'mm': String(d.getMinutes()).padStart(2, '0'),
    'ss': String(d.getSeconds()).padStart(2, '0'),
  }
  let result = fmt
  for (const [k, v] of Object.entries(o)) {
    result = result.replace(k, v)
  }
  return result
}

/**
 * Format file size
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + units[i]
}

/**
 * Format number with comma separators
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '-'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * Format percentage
 */
export function formatPercent(value, decimals = 2) {
  if (value === null || value === undefined) return '-'
  return (value * 100).toFixed(decimals) + '%'
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = text
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    return true
  }
}

/**
 * Get data source type icon class
 */
export function getDsTypeIcon(type) {
  const map = {
    mysql: 'mysql',
    postgresql: 'postgresql',
    postgres: 'postgresql',
    sqlite: 'db',
    sqlserver: 'sql-server',
    oracle: 'database',
    mongodb: 'mongodb',
    redis: 'redis',
    clickhouse: 'clickhouse',
    elasticsearch: 'elasticsearch',
    csv: 'csv',
    excel: 'excel',
  }
  return map[type?.toLowerCase()] || 'data-board'
}

/**
 * Truncate text
 */
export function truncate(str, len = 50) {
  if (!str) return ''
  return str.length > len ? str.substring(0, len) + '...' : str
}

/**
 * Safe JSON parse
 */
export function safeJsonParse(str, defaultVal = null) {
  try {
    return JSON.parse(str)
  } catch {
    return defaultVal
  }
}
