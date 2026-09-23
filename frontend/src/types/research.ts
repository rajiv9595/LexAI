export type ResearchSourceType =
  | 'statute'
  | 'case'
  | 'precedent'
  | 'regulation'
  | 'general-reference'

export type ResearchRecordStatus = 'Prototype'

export type ResearchSort = 'relevance' | 'date'

export const PROTOTYPE_JURISDICTION = 'Prototype / General'

/**
 * Frontend research record rendered by the Research workspace.
 * Field names are camelCase; values originate from the backend DTO
 * (see ResearchResultDto) via the mapping in researchService.ts.
 */
export interface ResearchResult {
  id: string
  title: string
  sourceType: ResearchSourceType
  jurisdiction: string
  date: string
  citationLabel: string
  summary: string
  relevanceReason: string
  topics: string[]
  status: ResearchRecordStatus
}

export interface ResearchQuery {
  query: string
  sourceTypes: ResearchSourceType[]
  jurisdiction: string
  sort: ResearchSort
}

/**
 * Backend DTOs — exact shape of the FastAPI research API.
 * POST /api/v1/research/search and GET /api/v1/research/{id}.
 * Research records are global/shared: no user ownership fields exist.
 */
export interface ResearchResultDto {
  result_id: string
  title: string
  source_type: ResearchSourceType
  jurisdiction: string
  date: string
  citation_label: string
  summary: string
  topics: string[]
  prototype: boolean
}

export interface ResearchSearchRequestDto {
  query: string
  source_type?: ResearchSourceType
  jurisdiction?: string
  sort: ResearchSort
}

export interface ResearchSearchResponseDto {
  query: string
  count: number
  results: ResearchResultDto[]
  prototype: boolean
}
