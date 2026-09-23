/**
 * Case History service communicating with the authenticated FastAPI backend.
 */

import { apiRequest } from './apiClient'
import type {
  HistoryFilter,
  HistoryItem,
  HistoryItemResponse,
  HistoryListResponse,
  HistorySummary,
} from '../types/history'

function mapHistoryResponse(dto: HistoryItemResponse): HistoryItem {
  return {
    id: dto.item_id,
    type: dto.type,
    title: dto.title,
    description: dto.description,
    category: dto.category,
    status: dto.status,
    updatedAt: dto.updated_at,
    relatedRoute: dto.related_route,
  }
}

export async function getHistoryItems(): Promise<HistoryItem[]> {
  const response = await apiRequest<HistoryListResponse>('/history')
  return (response.items || []).map(mapHistoryResponse)
}

export async function getHistoryItem(id: string): Promise<HistoryItem> {
  const response = await apiRequest<HistoryItemResponse>(`/history/${id}`)
  return mapHistoryResponse(response)
}

export function filterHistoryItems(
  items: HistoryItem[],
  search: string,
  filters: HistoryFilter,
): HistoryItem[] {
  const tokens = search
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter((t) => t.length > 1)

  const matched = items.filter((record) => {
    if (filters.type !== 'all' && record.type !== filters.type) {
      return false
    }
    if (filters.status !== 'all' && record.status !== filters.status) {
      return false
    }
    if (tokens.length > 0) {
      const haystack =
        `${record.title} ${record.description} ${record.category} ${record.type}`.toLowerCase()
      const allMatch = tokens.every((token) => haystack.includes(token))
      if (!allMatch) {
        return false
      }
    }
    return true
  })

  matched.sort((a, b) => {
    if (filters.sort === 'title') {
      return a.title.localeCompare(b.title)
    }
    const dateDiff = Date.parse(a.updatedAt) - Date.parse(b.updatedAt)
    if (isNaN(dateDiff)) return 0
    return filters.sort === 'oldest' ? dateDiff : -dateDiff
  })

  return matched
}

export function getHistorySummary(items: HistoryItem[]): HistorySummary {
  return {
    totalItems: items.length,
    assistantSessions: items.filter((item) => item.type === 'assistant').length,
    documents: items.filter((item) => item.type === 'document').length,
    researchTopics: items.filter((item) => item.type === 'research').length,
  }
}
