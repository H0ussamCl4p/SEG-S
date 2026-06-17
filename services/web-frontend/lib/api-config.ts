// API Configuration
// This dynamically detects the host to work on both localhost and network IPs

function normalizeBaseUrl(url: string): string {
  return url.replace(/\/+$/, '')
}

function getBaseUrl(envUrl: string | undefined, port: number): string {
  // In production we MUST use the configured public URL. Using window.location +
  // :8000/:8001 breaks behind an HTTPS reverse-proxy (ERR_SSL_PROTOCOL_ERROR).
  if (envUrl) {
    return normalizeBaseUrl(envUrl)
  }

  // Dev/local fallback: same host + explicit port.
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol
    const hostname = window.location.hostname
    return `${protocol}//${hostname}:${port}`
  }

  // SSR fallback
  return `http://localhost:${port}`
}

export const API_BASE_URL = getBaseUrl(process.env.NEXT_PUBLIC_API_URL, 8000)
export const AUTH_BASE_URL = getBaseUrl(process.env.NEXT_PUBLIC_AUTH_URL, 8001)

// Helper function to build API URLs
export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

export function authUrl(path: string): string {
  return `${AUTH_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}
