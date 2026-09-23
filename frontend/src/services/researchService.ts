import { ApiError, apiRequest } from './apiClient'
import { PROTOTYPE_JURISDICTION } from '../types/research'
import type {
  ResearchQuery,
  ResearchResult,
  ResearchResultDto,
  ResearchSearchRequestDto,
  ResearchSearchResponseDto,
  ResearchSourceType,
} from '../types/research'

/**
 * Research service backed by the real FastAPI + PostgreSQL API.
 *
 * - POST /api/v1/research/search for searches (server-side filtering
 *   by source_type/jurisdiction and server-side sort by relevance/date).
 * - GET /api/v1/research/{id} for single-record detail.
 *
 * Research records are global/shared: no user ownership, no credentials
 * required. Requests are sent explicitly unauthenticated (token: null)
 * so they work with or without a stored JWT.
 */

const VALID_SOURCE_TYPES: ResearchSourceType[] = [
  'statute',
  'case',
  'precedent',
  'regulation',
  'general-reference',
]

function sanitizeQuery(filters: ResearchQuery): {
  query: string
  sourceType: ResearchSourceType | undefined
  jurisdiction: string | undefined
  sort: 'relevance' | 'date'
} {
  const sourceType = filters.sourceTypes.find((item) =>
    VALID_SOURCE_TYPES.includes(item),
  )
  return {
    query: filters.query,
    sourceType,
    jurisdiction:
      filters.jurisdiction === PROTOTYPE_JURISDICTION
        ? PROTOTYPE_JURISDICTION
        : undefined,
    sort: filters.sort === 'date' ? 'date' : 'relevance',
  }
}

/**
 * Map the backend DTO to the frontend Research model.
 * The relevance note describes only that the record was returned for the
 * submitted query — the backend performs all-token matching, so every
 * returned record genuinely matches a non-empty query.
 */
function mapResearchResult(dto: ResearchResultDto, query: string): ResearchResult {
  const trimmedQuery = query.trim()
  return {
    id: dto.result_id,
    title: dto.title,
    sourceType: dto.source_type,
    jurisdiction: dto.jurisdiction,
    date: dto.date,
    citationLabel: dto.citation_label,
    summary: dto.summary,
    relevanceReason:
      trimmedQuery.length > 0
        ? `Matches the research topic "${trimmedQuery}".`
        : 'General prototype record.',
    topics: [...(dto.topics ?? [])],
    status: 'Prototype',
  }
}

export async function searchResearch(
  filters: ResearchQuery,
): Promise<ResearchResult[]> {
  const sanitized = sanitizeQuery(filters)
  const body: ResearchSearchRequestDto = {
    query: sanitized.query,
    sort: sanitized.sort,
  }
  if (sanitized.sourceType !== undefined) {
    body.source_type = sanitized.sourceType
  }
  if (sanitized.jurisdiction !== undefined) {
    body.jurisdiction = sanitized.jurisdiction
  }
  const response = await apiRequest<ResearchSearchResponseDto>(
    '/research/search',
    {
      method: 'POST',
      body: JSON.stringify(body),
      token: null,
    },
  )
  return (response.results ?? []).map((dto) =>
    mapResearchResult(dto, sanitized.query),
  )
}

export async function getResearchRecord(id: string): Promise<ResearchResult> {
  try {
    const dto = await apiRequest<ResearchResultDto>(
      `/research/${encodeURIComponent(id)}`,
      { token: null },
    )
    return mapResearchResult(dto, '')
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      throw new ApiError(404, 'Research record not found.')
    }
    throw error
  }
}
