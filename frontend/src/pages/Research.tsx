import { useEffect, useRef, useState } from 'react'
import PageHeader from '../components/PageHeader'
import DisclaimerBanner from '../components/DisclaimerBanner'
import ResearchSearch from '../components/ResearchSearch'
import ResearchFilters from '../components/ResearchFilters'
import type { SourceTypeFilter } from '../components/ResearchFilters'
import ResearchResultCard from '../components/ResearchResultCard'
import ResearchDetail from '../components/ResearchDetail'
import { ApiError } from '../services/apiClient'
import { getResearchRecord, searchResearch } from '../services/researchService'
import type { ResearchResult, ResearchSort } from '../types/research'
import './Research.css'

const SUGGESTED_RESEARCH_TOPICS = [
  'Security deposit dispute',
  'Employment termination',
  'Confidentiality obligations',
]

function toSearchErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 0) {
      return 'Unable to connect to the research service. Please verify the backend server is running and try again.'
    }
    if (error.status === 400 || error.status === 422) {
      return 'The search request was invalid. Please adjust your query or filters and try again.'
    }
    if (error.status >= 500) {
      return 'The research service is temporarily unavailable. Please try again later.'
    }
    return 'The research search failed. Please try again.'
  }
  return 'The research search failed. Please try again.'
}

function toDetailErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return 'Research record not found.'
    }
    if (error.status === 0) {
      return 'Unable to connect to the research service. Please verify the backend server is running and try again.'
    }
    if (error.status >= 500) {
      return 'The research service is temporarily unavailable. Please try again later.'
    }
  }
  return 'Unable to load the research record. Please try again.'
}

function Research() {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState<string | null>(null)
  const [sourceType, setSourceType] = useState<SourceTypeFilter>('all')
  const [jurisdiction, setJurisdiction] = useState('all')
  const [sort, setSort] = useState<ResearchSort>('relevance')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const [results, setResults] = useState<ResearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)

  const [selected, setSelected] = useState<ResearchResult | null>(null)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)

  const searchRequestId = useRef(0)
  const detailRequestId = useRef(0)

  const hasSearched = submittedQuery !== null

  useEffect(() => {
    if (!hasSearched) {
      return
    }
    const requestId = (searchRequestId.current += 1)
    setIsSearching(true)
    setSearchError(null)
    searchResearch({
      query: submittedQuery ?? '',
      sourceTypes: sourceType === 'all' ? [] : [sourceType],
      jurisdiction,
      sort,
    })
      .then((items) => {
        if (searchRequestId.current !== requestId) {
          return
        }
        setResults(items)
        setIsSearching(false)
      })
      .catch((error: unknown) => {
        if (searchRequestId.current !== requestId) {
          return
        }
        setResults([])
        setSearchError(toSearchErrorMessage(error))
        setIsSearching(false)
      })
  }, [hasSearched, submittedQuery, sourceType, jurisdiction, sort])

  function handleSelect(id: string) {
    setSelectedId(id)
    const requestId = (detailRequestId.current += 1)
    setIsDetailLoading(true)
    setDetailError(null)
    setSelected(null)
    getResearchRecord(id)
      .then((record) => {
        if (detailRequestId.current !== requestId) {
          return
        }
        setSelected(record)
        setIsDetailLoading(false)
      })
      .catch((error: unknown) => {
        if (detailRequestId.current !== requestId) {
          return
        }
        setSelected(null)
        setDetailError(toDetailErrorMessage(error))
        setIsDetailLoading(false)
      })
  }

  function handleCloseDetail() {
    detailRequestId.current += 1
    setSelectedId(null)
    setSelected(null)
    setDetailError(null)
    setIsDetailLoading(false)
  }

  function runSearch(value: string) {
    handleCloseDetail()
    setSubmittedQuery(value)
  }

  function handleClearSearch() {
    searchRequestId.current += 1
    handleCloseDetail()
    setQuery('')
    setSubmittedQuery(null)
    setSourceType('all')
    setJurisdiction('all')
    setSort('relevance')
    setResults([])
    setSearchError(null)
    setIsSearching(false)
  }

  function handleStartingPoint(result: ResearchResult) {
    const topic = result.topics[0] ?? result.title
    setQuery(topic)
    runSearch(topic)
  }

  return (
    <div className="page-container">
      <PageHeader
        title="Legal Research"
        description="Explore structured legal research information and prototype references."
        action={<span className="research-status">Prototype Research</span>}
      />

      <div className="research-search-panel">
        <ResearchSearch
          query={query}
          onQueryChange={setQuery}
          onSearch={() => runSearch(query)}
        />
        <ResearchFilters
          sourceType={sourceType}
          jurisdiction={jurisdiction}
          sort={sort}
          onSourceTypeChange={setSourceType}
          onJurisdictionChange={setJurisdiction}
          onSortChange={setSort}
        />
      </div>

      {!hasSearched ? (
        <div className="research-empty">
          <h2 className="research-empty-title">Start your legal research</h2>
          <p className="research-empty-text">
            Enter a legal issue or topic to explore the prototype research
            dataset.
          </p>
          <ul className="suggestion-list">
            {SUGGESTED_RESEARCH_TOPICS.map((topic) => (
              <li key={topic}>
                <button
                  type="button"
                  className="suggestion-button"
                  onClick={() => {
                    setQuery(topic)
                    runSearch(topic)
                  }}
                >
                  {topic}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : isSearching ? (
        <div className="research-loading" role="status">
          <h2 className="research-loading-title">Searching research records…</h2>
          <p className="research-loading-text">
            Querying the research index
            {submittedQuery && submittedQuery.trim()
              ? ` for “${submittedQuery.trim()}”`
              : ''}
            .
          </p>
        </div>
      ) : searchError ? (
        <div className="research-error" role="alert">
          <h2 className="research-error-title">Research search failed</h2>
          <p className="research-error-text">{searchError}</p>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => runSearch(submittedQuery ?? '')}
          >
            Try Again
          </button>
        </div>
      ) : results.length === 0 ? (
        <div className="research-no-results">
          <h2 className="research-no-results-title">
            No research results found
          </h2>
          <p className="research-no-results-text">
            No records matched your query. Try a broader research topic or
            choose a different source type.
          </p>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleClearSearch}
          >
            Clear Search
          </button>
        </div>
      ) : (
        <div className="research-workspace">
          <div className="research-results-column">
            <h2 className="research-results-heading">Research results</h2>
            <p className="research-results-count">
              {results.length} prototype{' '}
              {results.length === 1 ? 'record' : 'records'}
              {submittedQuery && submittedQuery.trim()
                ? ` for “${submittedQuery.trim()}”`
                : ''}
              .
            </p>
            {results.map((result) => (
              <ResearchResultCard
                key={result.id}
                result={result}
                selected={result.id === selectedId}
                onSelect={handleSelect}
              />
            ))}
          </div>
          <div className="research-side-column">
            {isDetailLoading ? (
              <div className="research-detail-loading" role="status">
                <p className="research-detail-loading-text">
                  Loading research record…
                </p>
              </div>
            ) : null}
            {detailError && !isDetailLoading ? (
              <div className="research-detail-error" role="alert">
                <p className="research-detail-error-text">{detailError}</p>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={handleCloseDetail}
                >
                  Close
                </button>
              </div>
            ) : null}
            {selected && !isDetailLoading && !detailError ? (
              <ResearchDetail
                result={selected}
                onUseAsStartingPoint={handleStartingPoint}
                onClose={handleCloseDetail}
              />
            ) : null}
          </div>
        </div>
      )}

      <p className="research-disclaimer">
        LexAssist research results are prototype information for demonstration
        purposes. They are not authoritative legal sources or legal advice.
        Verify important legal information using appropriate authoritative
        sources and qualified legal professionals.
      </p>
      <DisclaimerBanner />
    </div>
  )
}

export default Research
