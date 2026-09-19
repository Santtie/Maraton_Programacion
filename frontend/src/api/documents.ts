import { apiGet, apiGetBlob, apiPost } from './client'
import type { HabeasDataRequestResult, TiposResponse } from './types'

export function getTipos() {
  return apiGet<TiposResponse>('/api/documents/tipos/')
}

export function generate(tipo: string, campos: Record<string, string>) {
  return apiPost<HabeasDataRequestResult>('/api/documents/generate/', { tipo, campos })
}

export async function downloadPdf(id: number, filename: string) {
  const blob = await apiGetBlob(`/api/documents/${id}/pdf/`)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
