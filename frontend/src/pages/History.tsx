import { useEffect, useMemo, useState } from 'react'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import DisclaimerBanner from '../components/DisclaimerBanner'
import HistoryFilters from '../components/HistoryFilters'
import type {
  HistoryStatusFilter,
  HistoryTypeFilter,
} from '../components/HistoryFilters'
import HistoryList from '../components/HistoryList'
import {
  filterHistoryItems,
  getHistoryItems,
  getHistorySummary,
} from '../services/historyService'
import type { HistoryItem, HistorySort } from '../types/history'
import './History.css'

function History() {
  const [rawItems, setRawItems] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [type, setType] = useState<HistoryTypeFilter>('all')
  const [status, setStatus] = useState<HistoryStatusFilter>('all')
  const [sort, setSort] = useState<HistorySort>('recent')

  useEffect(() => {
    let isMounted = true

    async function loadHistory() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getHistoryItems()
        if (isMounted) {
          setRawItems(data)
        }
      } catch (err) {
        if (isMounted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Failed to load activity history.',
          )
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadHistory()

    return () => {
      isMounted = false
    }
  }, [])

  const summary = useMemo(() => getHistorySummary(rawItems), [rawItems])

  const items = useMemo(
    () => filterHistoryItems(rawItems, search, { type, status, sort }),
    [rawItems, search, type, status, sort],
  )

  function handleClear() {
    setSearch('')
    setType('all')
    setStatus('all')
    setSort('recent')
  }

  const summaryCards = [
    { label: 'Legal Sessions', value: summary.assistantSessions },
    { label: 'Documents', value: summary.documents },
    { label: 'Research Topics', value: summary.researchTopics },
    { label: 'Total Activity', value: summary.totalItems },
  ]

  return (
    <div className="page-container">
      <PageHeader
        title="Case History"
        description="Review your legal assistance activity, document drafts, and research topics in one workspace."
      />

      {error ? (
        <div className="alert alert-error" role="alert" style={{ marginBottom: '1rem' }}>
          <p>{error}</p>
        </div>
      ) : null}

      <ul className="history-summary-grid">
        {summaryCards.map((card) => (
          <li key={card.label}>
            <Card title={card.label}>
              <p className="history-stat-value">{card.value}</p>
              <p className="history-stat-note">User records</p>
            </Card>
          </li>
        ))}
      </ul>

      <div className="history-toolbar">
        <div className="history-search-field">
          <label className="history-filter-label" htmlFor="history-search">
            Search activity
          </label>
          <input
            id="history-search"
            className="history-search-input"
            type="search"
            value={search}
            placeholder="Search activity..."
            autoComplete="off"
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>
        <HistoryFilters
          type={type}
          status={status}
          sort={sort}
          onTypeChange={setType}
          onStatusChange={setStatus}
          onSortChange={setSort}
          onClear={handleClear}
        />
      </div>

      {isLoading ? (
        <div className="history-empty">
          <p>Loading activity history...</p>
        </div>
      ) : rawItems.length === 0 ? (
        <div className="history-empty">
          <h2 className="history-empty-title">No activity yet</h2>
          <p className="history-empty-text">
            Activity from your document drafts and legal assistant sessions will
            appear here.
          </p>
        </div>
      ) : items.length === 0 ? (
        <div className="history-empty">
          <h2 className="history-empty-title">No matching activity found</h2>
          <p className="history-empty-text">
            Try changing your search terms or filters to view your activity
            records.
          </p>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleClear}
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <>
          <p className="history-count">
            Showing {items.length} of {summary.totalItems}{' '}
            {items.length === 1 ? 'record' : 'records'}.
          </p>
          <HistoryList items={items} />
        </>
      )}

      <DisclaimerBanner />
    </div>
  )
}

export default History
