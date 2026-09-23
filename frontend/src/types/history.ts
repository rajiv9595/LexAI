export type HistoryItemType = 'assistant' | 'document' | 'research'

export type HistoryStatus = 'prototype' | 'draft' | 'completed'

export type HistorySort = 'recent' | 'oldest' | 'title'

export interface AssistantMetadata {
  kind: 'assistant'
  sessionTopic: string
  messageCount: number
}

export interface DocumentMetadata {
  kind: 'document'
  documentType: string
  targetRoute: string
}

export interface ResearchMetadata {
  kind: 'research'
  topics: string[]
  resultCount: number
}

export type HistoryMetadata =
  | AssistantMetadata
  | DocumentMetadata
  | ResearchMetadata

export interface HistoryItem {
  id: string
  type: HistoryItemType
  title: string
  description: string
  createdAt?: string
  updatedAt: string
  status: HistoryStatus
  relatedRoute: string
  category: string
  metadata?: HistoryMetadata
}

export interface HistoryFilter {
  type: HistoryItemType | 'all'
  status: HistoryStatus | 'all'
  sort: HistorySort
}

export interface HistorySummary {
  totalItems: number
  assistantSessions: number
  documents: number
  researchTopics: number
}

/** Backend API DTOs */
export interface HistoryItemResponse {
  item_id: string
  type: HistoryItemType
  title: string
  description: string
  category: string
  status: HistoryStatus
  updated_at: string
  related_route: string
  prototype: boolean
}

export interface HistoryListResponse {
  count: number
  items: HistoryItemResponse[]
  prototype: boolean
}
