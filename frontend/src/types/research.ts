export type ResearchSourceType =
  | 'statute'
  | 'case'
  | 'precedent'
  | 'regulation'
  | 'general-reference'

export type ResearchRecordStatus = 'Prototype'

export type ResearchSort = 'relevance' | 'date'

export const PROTOTYPE_JURISDICTION = 'Prototype / General'

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

export interface ResearchSummary {
  query: string
  issue: string
  keyPoints: string[]
  considerations: string[]
  relatedTopics: string[]
}
