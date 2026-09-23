import { useMemo, useState } from 'react'
import PageHeader from '../components/PageHeader'
import DisclaimerBanner from '../components/DisclaimerBanner'
import ResearchSearch from '../components/ResearchSearch'
import ResearchFilters from '../components/ResearchFilters'
import type { SourceTypeFilter } from '../components/ResearchFilters'
import ResearchResultCard from '../components/ResearchResultCard'
import ResearchDetail from '../components/ResearchDetail'
import ResearchSummary from '../components/ResearchSummary'
import {
  getResearchSummary,
  searchResearch,
} from '../services/researchService'
import type {
  ResearchResult,
  ResearchSort,
} from '../types/research'
import './Research.css'

const SUGGESTED_RESEARCH_TOPICS = [
  'Security deposit dispute',
  'Employment termination',
  'Confidentiality obligations',
]

function Research() {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState<string | null>(null)
  const [sourceType, setSourceType] = useState<SourceTypeFilter>('all')
  const [jurisdiction, setJurisdiction] = useState('all')
  const [sort, setSort] = useState<ResearchSort>('relevance')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const hasSearched = submittedQuery !== null

  const results = useMemo<ResearchResult[]>(() => {
    if (!hasSearched) {
      return []
    }
    return searchResearch({
      query: submittedQuery ?? '',
      sourceTypes: sourceType === 'all' ? [] : [sourceType],
      jurisdiction,
      sort,
    })
  }, [hasSearched, submittedQuery, sourceType, jurisdiction, sort])

  const summary = useMemo(() => {
    if (!hasSearched || (submittedQuery ?? '').trim().length === 0) {
      return null
    }
    return getResearchSummary(submittedQuery ?? '')
  }, [hasSearched, submittedQuery])

  const selected = selectedId
    ? results.find((item) => item.id === selectedId)
    : undefined

  function runSearch(value: string) {
    setSubmittedQuery(value)
    setSelectedId(null)
  }

  function handleClearSearch() {
    setQuery('')
    setSubmittedQuery(null)
    setSourceType('all')
    setJurisdiction('all')
    setSort('relevance')
    setSelectedId(null)
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
      ) : results.length === 0 ? (
        <div className="research-no-results">
          <h2 className="research-no-results-title">
            No prototype references found
          </h2>
          <p className="research-no-results-text">
            Try a broader research topic or choose a different source type.
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
                selected={result.id === selected?.id}
                onSelect={setSelectedId}
              />
            ))}
          </div>
          <div className="research-side-column">
            {summary ? (
              <ResearchSummary
                summary={summary}
                onRelatedTopicClick={(topic) => {
                  setQuery(topic)
                  runSearch(topic)
                }}
              />
            ) : null}
            {selected ? (
              <ResearchDetail
                result={selected}
                onUseAsStartingPoint={handleStartingPoint}
                onClose={() => setSelectedId(null)}
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
