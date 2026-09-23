import {
  researchRecordsDemo,
  researchSummariesDemo,
} from '../data/mockResearchData'
import { PROTOTYPE_JURISDICTION } from '../types/research'
import type {
  ResearchQuery,
  ResearchResult,
  ResearchSourceType,
  ResearchSummary,
} from '../types/research'

/**
 * Frontend research service for the prototype.
 *
 * Operates on local mock data only. No fetch, no network calls.
 * When backend integration is added later, the Research page should keep
 * calling these functions while the implementation below switches to the API.
 */

const VALID_SOURCE_TYPES: ResearchSourceType[] = [
  'statute',
  'case',
  'precedent',
  'regulation',
  'general-reference',
]

function normalize(value: string): string {
  return value.trim().toLowerCase()
}

function tokenize(value: string): string[] {
  return normalize(value).split(/\s+/).filter((token) => token.length > 1)
}

function sanitizeQuery(filters: ResearchQuery): ResearchQuery {
  const sourceTypes = filters.sourceTypes.filter((item) =>
    VALID_SOURCE_TYPES.includes(item),
  )
  return {
    query: filters.query,
    sourceTypes,
    jurisdiction:
      filters.jurisdiction === PROTOTYPE_JURISDICTION
        ? PROTOTYPE_JURISDICTION
        : 'all',
    sort: filters.sort === 'date' ? 'date' : 'relevance',
  }
}

function scoreRecord(record: ResearchResult, tokens: string[]): number {
  const haystack = normalize(
    `${record.title} ${record.summary} ${record.topics.join(' ')} ${record.jurisdiction} ${record.sourceType.replace('-', ' ')}`,
  )
  let score = 0
  for (const token of tokens) {
    if (haystack.includes(token)) {
      score += 1
    }
  }
  return score
}

export function getResearchResults(): ResearchResult[] {
  return researchRecordsDemo.map((record) => ({ ...record }))
}

export function searchResearch(filters: ResearchQuery): ResearchResult[] {
  const sanitized = sanitizeQuery(filters)
  const tokens = tokenize(sanitized.query)

  const matched = researchRecordsDemo
    .map((record, index) => ({ record, index, score: scoreRecord(record, tokens) }))
    .filter(({ record, score }) => {
      if (tokens.length > 0 && score === 0) {
        return false
      }
      if (
        sanitized.sourceTypes.length > 0 &&
        !sanitized.sourceTypes.includes(record.sourceType)
      ) {
        return false
      }
      if (
        sanitized.jurisdiction !== 'all' &&
        record.jurisdiction !== sanitized.jurisdiction
      ) {
        return false
      }
      return true
    })

  matched.sort((a, b) => {
    if (sanitized.sort === 'date') {
      return (
        Date.parse(b.record.date) - Date.parse(a.record.date) ||
        a.index - b.index
      )
    }
    return b.score - a.score || a.index - b.index
  })

  return matched.map(({ record }) => ({
    ...record,
    topics: [...record.topics],
    relevanceReason:
      tokens.length > 0
        ? `Matches the research topic "${sanitized.query.trim()}".`
        : 'General prototype record.',
  }))
}

export function getResearchResult(id: string): ResearchResult | undefined {
  const record = researchRecordsDemo.find((item) => item.id === id)
  if (!record) {
    return undefined
  }
  return { ...record, topics: [...record.topics] }
}

export function getResearchSummary(queryText: string): ResearchSummary {
  const query = queryText.trim()
  const normalized = normalize(query)
  const predefined = researchSummariesDemo.find(
    (item) => normalized.length > 0 && normalized.includes(item.query),
  )
  if (predefined) {
    return {
      query,
      issue: predefined.issue,
      keyPoints: [...predefined.keyPoints],
      considerations: [...predefined.considerations],
      relatedTopics: [...predefined.relatedTopics],
    }
  }
  const topTopics = searchResearch({
    query,
    sourceTypes: [],
    jurisdiction: 'all',
    sort: 'relevance',
  })
    .slice(0, 3)
    .flatMap((record) => record.topics)
    .slice(0, 3)
  return {
    query,
    issue: `Prototype classification of "${query}".`,
    keyPoints: [
      'Identify the type of legal issue.',
      'Gather relevant facts and documents.',
      'Check the applicable jurisdiction.',
      'Verify authoritative sources before relying on the information.',
    ],
    considerations: [
      'Jurisdiction can affect the applicable rules.',
      'Facts and dates may materially change the analysis.',
      'Prototype references require independent verification.',
    ],
    relatedTopics:
      topTopics.length > 0
        ? [...new Set(topTopics)]
        : ['General legal information'],
  }
}
