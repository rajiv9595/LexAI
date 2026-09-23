import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
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
import { listConversations } from '../services/chatService'
import type { AssistantConversationListResponse } from '../types/assistant'
import type { HistoryItem, HistorySort } from '../types/history'
import './History.css'

const CONVERSATIONS_PAGE_SIZE = 10

function History() {
  const [rawItems, setRawItems] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [type, setType] = useState<HistoryTypeFilter>('all')
  const [status, setStatus] = useState<HistoryStatusFilter>('all')
  const [sort, setSort] = useState<HistorySort>('recent')

  // STEP 24: real assistant conversations from the list endpoint.
  const [convPage, setConvPage] = useState(1)
  const [convData, setConvData] =
    useState<AssistantConversationListResponse | null>(null)
  const [convLoading, setConvLoading] = useState(true)
  const [convError, setConvError] = useState<string | null>(null)

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

  useEffect(() => {
    let isMounted = true

    async function loadConversations() {
      setConvLoading(true)
      setConvError(null)
      try {
        const data = await listConversations(
          convPage,
          CONVERSATIONS_PAGE_SIZE,
        )
        if (isMounted) {
          setConvData(data)
        }
      } catch (err) {
        if (isMounted) {
          setConvError(
            err instanceof Error
              ? err.message
              : 'Failed to load conversations.',
          )
        }
      } finally {
        if (isMounted) {
          setConvLoading(false)
        }
      }
    }

    void loadConversations()

    return () => {
      isMounted = false
    }
  }, [convPage])

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

      <section aria-label="Assistant conversations" style={{ marginTop: '2rem' }}>
        <h2 className="history-empty-title">Assistant conversations</h2>
        {convLoading ? (
          <div className="history-empty">
            <p>Loading conversations...</p>
          </div>
        ) : convError ? (
          <div className="alert alert-error" role="alert">
            <p>{convError}</p>
          </div>
        ) : !convData || convData.total === 0 ? (
          <div className="history-empty">
            <p className="history-empty-text">No conversations yet.</p>
          </div>
        ) : (
          <>
            <p className="history-count">
              Showing {(convData.page - 1) * convData.page_size + 1}–
              {(convData.page - 1) * convData.page_size +
                convData.items.length}{' '}
              of {convData.total}{' '}
              {convData.total === 1 ? 'conversation' : 'conversations'}.
            </p>
            <ul className="history-list">
              {convData.items.map((conv) => (
                <li key={conv.conversation_id} className="history-item">
                  <div className="history-item-top">
                    <span className="history-item-type">Legal Assistant</span>
                    <span className="history-item-status">
                      {conv.message_count}{' '}
                      {conv.message_count === 1 ? 'message' : 'messages'}
                    </span>
                  </div>
                  <h3 className="history-item-title">
                    {conv.first_user_message_preview ?? 'Conversation'}
                  </h3>
                  <p className="history-item-facts">
                    <span>
                      <strong>Date: </strong>
                      {conv.updated_at}
                    </span>
                  </p>
                  <Link
                    className="btn btn-secondary"
                    to={`/app/assistant?conversationId=${encodeURIComponent(conv.conversation_id)}`}
                    aria-label={`Open conversation ${conv.conversation_id}`}
                  >
                    Open
                  </Link>
                </li>
              ))}
            </ul>
            {convData.total > convData.page_size ? (
              <div
                style={{
                  display: 'flex',
                  gap: '0.75rem',
                  alignItems: 'center',
                  marginTop: '1rem',
                }}
              >
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={convData.page <= 1 || convLoading}
                  onClick={() => setConvPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </button>
                <span aria-live="polite">Page {convData.page}</span>
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={
                    convData.page * convData.page_size >= convData.total ||
                    convLoading
                  }
                  onClick={() => setConvPage((p) => p + 1)}
                >
                  Next
                </button>
              </div>
            ) : null}
          </>
        )}
      </section>

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
