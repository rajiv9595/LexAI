import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import DisclaimerBanner from '../components/DisclaimerBanner'
import CaseContext from '../components/CaseContext'
import {
  getConversation,
  getSuggestedPrompts,
  listConversations,
  resolveSendError,
  sendMessage,
} from '../services/chatService'
import type { ResolvedSendError } from '../services/chatService'
import type {
  AssistantConversationListItem,
  ChatMessage,
} from '../types/assistant'
import './Assistant.css'

/** STEP 25: recent-list page size. History stays the full-list destination. */
const RECENT_PAGE_SIZE = 5

/**
 * STEP 27: mirrors the backend AssistantMessageRequest max_length (4000).
 * The send contract transmits the trimmed message, so the counter and the
 * limit gate measure the trimmed draft — the exact string the backend
 * validates. Single source of truth; no second maximum exists.
 */
const MESSAGE_MAX_LENGTH = 4000

function Assistant() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialConversationId = searchParams.get('conversationId')

  const [conversationId, setConversationId] = useState<string | null>(
    initialConversationId,
  )
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<ResolvedSendError | null>(null)
  // STEP 31: browser connectivity only — NOT backend health. Initialized
  // from navigator.onLine so an already-offline mount renders correctly.
  const [isOffline, setIsOffline] = useState<boolean>(
    typeof navigator !== 'undefined' && !navigator.onLine,
  )

  // STEP 25: lightweight recent conversations from the existing STEP 24
  // list endpoint. Independent from the chat flow; never blocks sending.
  const [recent, setRecent] = useState<AssistantConversationListItem[]>([])
  const [isLoadingRecent, setIsLoadingRecent] = useState(false)
  const [recentError, setRecentError] = useState<string | null>(null)
  // Smallest safe stale-response guard: only the latest request applies.
  const recentRequestRef = useRef(0)

  const messagesEndRef = useRef<HTMLLIElement | null>(null)
  const suggestedPrompts = getSuggestedPrompts()

  async function loadRecent() {
    const requestId = recentRequestRef.current + 1
    recentRequestRef.current = requestId
    setIsLoadingRecent(true)
    setRecentError(null)
    try {
      const res = await listConversations(1, RECENT_PAGE_SIZE)
      if (recentRequestRef.current === requestId) {
        setRecent(res.items ?? [])
      }
    } catch (err) {
      if (recentRequestRef.current === requestId) {
        setRecentError(
          err instanceof Error
            ? err.message
            : 'Failed to load recent conversations.',
        )
      }
    } finally {
      if (recentRequestRef.current === requestId) {
        setIsLoadingRecent(false)
      }
    }
  }

  // Load recent conversations once on mount; refreshed after each
  // successful send. Failures stay local to this section.
  useEffect(() => {
    let isMounted = true
    const requestId = recentRequestRef.current + 1
    recentRequestRef.current = requestId
    setIsLoadingRecent(true)
    listConversations(1, RECENT_PAGE_SIZE)
      .then((res) => {
        if (isMounted && recentRequestRef.current === requestId) {
          setRecent(res.items ?? [])
        }
      })
      .catch((err: unknown) => {
        if (isMounted && recentRequestRef.current === requestId) {
          setRecentError(
            err instanceof Error
              ? err.message
              : 'Failed to load recent conversations.',
          )
        }
      })
      .finally(() => {
        if (isMounted && recentRequestRef.current === requestId) {
          setIsLoadingRecent(false)
        }
      })
    return () => {
      isMounted = false
    }
  }, [])

  // If conversationId is supplied in URL, fetch past conversation
  useEffect(() => {
    let isMounted = true
    if (initialConversationId) {
      setIsLoadingHistory(true)
      setError(null)
      getConversation(initialConversationId)
        .then((res) => {
          if (isMounted) {
            setConversationId(res.conversation_id)
            setMessages(
              res.messages.map((msg) => ({
                id: msg.message_id,
                role: msg.role === 'user' ? 'user' : 'assistant',
                content: msg.content,
                // STEP 23: persisted generation-time snapshots reload with
                // the message; pre-STEP-23 and sourceless messages yield [].
                references: msg.references ?? [],
              })),
            )
          }
        })
        .catch((err: unknown) => {
          if (isMounted) {
            // Conversation-load failures are not send retries.
            setError({
              message:
                err instanceof Error
                  ? err.message
                  : 'Failed to load conversation.',
              retryable: false,
            })
          }
        })
        .finally(() => {
          if (isMounted) {
            setIsLoadingHistory(false)
          }
        })
    }
    return () => {
      isMounted = false
    }
  }, [initialConversationId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: 'nearest' })
  }, [messages.length])

  // STEP 31: browser online/offline events with cleanup on unmount. No
  // polling, no persistence, no automatic retry — reconnect only lifts
  // the send restriction; the user still retries explicitly.
  useEffect(() => {
    function handleOnline() {
      setIsOffline(false)
    }
    function handleOffline() {
      setIsOffline(true)
    }
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // STEP 27: length measured on the trimmed draft — the string the send
  // handler transmits and the backend validates. At exactly 4000 the
  // message stays valid; whitespace-only input is still rejected by the
  // existing non-empty rule.
  const trimmedLength = draft.trim().length
  const isOverLimit = trimmedLength > MESSAGE_MAX_LENGTH
  // STEP 31: offline is one more conjunct — all existing rules preserved.
  const canSend =
    trimmedLength > 0 && !isOverLimit && !isSending && !isOffline

  async function handleSend(textToSend?: string) {
    // STEP 31: never issue an API request while the browser reports
    // offline. Covers Send, Ctrl+Enter, suggested prompts, and Retry.
    // Draft, messages, and error state are left untouched.
    if (isOffline) {
      return
    }
    const messageText = (textToSend ?? draft).trim()
    if (!messageText || isSending) {
      return
    }
    // Defense-in-depth: the Send button is already disabled over the
    // limit, but never let an over-limit payload reach the API. The
    // user's input is left untouched — nothing is truncated or deleted.
    if (messageText.length > MESSAGE_MAX_LENGTH) {
      setError({
        message: `Message exceeds the ${MESSAGE_MAX_LENGTH}-character limit. Shorten it before sending.`,
        retryable: false,
      })
      return
    }

    const tempUserMsg: ChatMessage = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: 'Just now',
    }

    setMessages((prev) => [...prev, tempUserMsg])
    setIsSending(true)
    setError(null)

    try {
      const response = await sendMessage(
        messageText,
        conversationId || undefined,
      )
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id)
        setSearchParams({ conversationId: response.conversation_id })
      }

      const assistantMsg: ChatMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.content,
        timestamp: 'Just now',
        references: response.references ?? [],
      }
      setMessages((prev) => [...prev, assistantMsg])
      // STEP 28: clear the composer only after the API succeeds. A failed
      // send leaves the draft intact for correction/retry, and
      // conversation navigation never touches it (component state only).
      setDraft('')
      // STEP 25: refresh from the authoritative server ordering so the
      // current conversation moves per backend updated_at DESC. Only on
      // success — a failed send must not fabricate recency.
      void loadRecent()
    } catch (err) {
      setError(resolveSendError(err))
    } finally {
      setIsSending(false)
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && event.ctrlKey) {
      event.preventDefault()
      void handleSend()
    }
  }

  function handleSuggestionClick(label: string) {
    void handleSend(label)
  }

  return (
    <div className="page-container">
      <PageHeader
        title="Legal Assistant"
        description="Describe your legal concern in your own words and receive structured legal information."
      />
      <p className="assistant-subnote">
        LexAssist provides general legal information. It does not replace advice
        from a qualified legal professional.
      </p>

      {error ? (
        <div className="alert alert-error" role="alert" style={{ marginBottom: '1rem' }}>
          <p>{error.message}</p>
          {/* STEP 29: explicit retry of the preserved current draft.
              Reuses handleSend (single attempt, no timers/queues) and
              canSend (empty, over-limit, and isSending guards). Success
              follows the existing path (draft clears, recents refresh);
              failure replaces the error and keeps draft + Retry.
              STEP 30: shown only for retryable failures. */}
          {error.retryable ? (
            <button
              type="button"
              className="btn btn-secondary"
              disabled={!canSend}
              onClick={() => void handleSend()}
            >
              Retry
            </button>
          ) : null}
        </div>
      ) : null}

      <div className="assistant-layout">
        <section className="conversation-panel" aria-label="Conversation">
          {isLoadingHistory ? (
            <div className="empty-state">
              <p>Loading conversation...</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="empty-state">
              <h2 className="empty-state-title">How can we help?</h2>
              <p className="empty-state-text">
                Describe your legal situation in your own words.
              </p>
              <ul className="suggestion-list">
                {suggestedPrompts.map((prompt) => (
                  <li key={prompt.id}>
                    <button
                      type="button"
                      className="suggestion-button"
                      disabled={isSending}
                      onClick={() => handleSuggestionClick(prompt.label)}
                    >
                      {prompt.label}
                    </button>
                  </li>
                ))}
              </ul>
              {/* STEP 26: onboarding pointer, shown only when no
                  conversation is open AND the recent list loaded
                  successfully with zero items. Never during loading
                  (avoids flashing) and never on load error (the app
                  does not know the list is empty then). */}
              {conversationId === null &&
              !isLoadingRecent &&
              recentError === null &&
              recent.length === 0 ? (
                <p className="empty-state-text">
                  Past conversations live under{' '}
                  <Link to="/app/history">Case History</Link>.
                </p>
              ) : null}
            </div>
          ) : (
            <ul className="message-list">
              {messages.map((message) => (
                <li
                  key={message.id}
                  className={
                    message.role === 'user'
                      ? 'message-row message-row-user'
                      : 'message-row message-row-assistant'
                  }
                >
                  <div className="message-bubble">{message.content}</div>
                  {message.role === 'assistant' &&
                  message.references &&
                  message.references.length > 0 ? (
                    <section
                      className="message-references"
                      aria-label="Relevant references"
                    >
                      <h4 className="message-references-label">
                        Relevant references
                      </h4>
                      <ul className="message-references-list">
                        {message.references.map((reference) => (
                          <li
                            key={reference.source_id}
                            className="message-reference"
                          >
                            <p className="message-reference-title">
                              {reference.title}
                            </p>
                            <p className="message-reference-meta">
                              {reference.citation_label} · {reference.source_type}
                              {reference.jurisdiction
                                ? ` · ${reference.jurisdiction}`
                                : ''}
                            </p>
                            {reference.prototype ? (
                              <span className="prototype-badge">
                                Prototype research
                              </span>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    </section>
                  ) : null}
                  {message.timestamp ? (
                    <p className="message-timestamp">{message.timestamp}</p>
                  ) : null}
                </li>
              ))}
              {isSending ? (
                <li className="message-row message-row-assistant">
                  <div className="message-bubble" style={{ opacity: 0.7 }}>
                    Preparing response...
                  </div>
                </li>
              ) : null}
              <li ref={messagesEndRef} aria-hidden="true" />
            </ul>
          )}

          <form
            className="chat-input-area"
            onSubmit={(event) => {
              event.preventDefault()
              void handleSend()
            }}
          >
            <label className="chat-input-label sr-only" htmlFor="assistant-input">
              Describe your legal concern
            </label>
            <textarea
              id="assistant-input"
              className="chat-textarea"
              rows={3}
              value={draft}
              disabled={isSending}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your legal concern..."
              aria-describedby="assistant-char-count"
              aria-invalid={isOverLimit ? 'true' : undefined}
            />
            {/* STEP 32: discoverability for the existing Ctrl+Enter send
                shortcut (see handleKeyDown — unchanged). Ordinary muted
                text; shares the generic composer-hint style. */}
            <p className="composer-hint">Ctrl + Enter to send</p>
            {/* STEP 31: compact connectivity hint. Plain muted text (not
                color-only, no live region, no banner). Textarea stays
                editable; only submission is blocked. */}
            {isOffline ? (
              <p className="composer-hint">You appear to be offline.</p>
            ) : null}
            <div className="chat-input-actions">
              <span
                id="assistant-char-count"
                className={
                  isOverLimit ? 'char-counter char-counter-over' : 'char-counter'
                }
              >
                {trimmedLength} / {MESSAGE_MAX_LENGTH}
                {isOverLimit ? ' — shorten to send' : null}
              </span>
              <button
                type="button"
                className="voice-button"
                disabled
                title="Voice input will be added in a later step."
                aria-label="Voice input (not available yet)"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                  focusable="false"
                >
                  <rect x="5" y="1.5" width="4" height="7" rx="2" />
                  <path d="M2.5 6.5a4.5 4.5 0 0 0 9 0M7 11v1.5" />
                </svg>
                <span>Voice</span>
              </button>
              <button
                type="submit"
                className="send-button"
                disabled={!canSend}
              >
                {isSending ? 'Sending...' : 'Send'}
              </button>
            </div>
          </form>
        </section>

        <aside className="assistant-context-column" aria-label="Session context">
          <CaseContext
            conversationId={conversationId}
            messageCount={messages.length}
            status={conversationId ? 'Active Conversation' : 'Ready'}
          />
          <section
            className="recent-conversations"
            aria-label="Recent conversations"
          >
            <h2 className="recent-conversations-title">
              Recent conversations
            </h2>
            {isLoadingRecent && recent.length === 0 ? (
              <p className="recent-conversations-note">
                Loading recent conversations...
              </p>
            ) : recentError ? (
              <p className="recent-conversations-note" role="alert">
                {recentError}
              </p>
            ) : recent.length === 0 ? (
              <p className="recent-conversations-note">
                No recent conversations.
              </p>
            ) : (
              <ul className="recent-conversations-list">
                {recent.map((item) => {
                  const isCurrent =
                    conversationId !== null &&
                    item.conversation_id === conversationId
                  return (
                    <li
                      key={item.conversation_id}
                      className="recent-conversation-item"
                    >
                      <Link
                        className="recent-conversation-link"
                        to={`/app/assistant?conversationId=${encodeURIComponent(item.conversation_id)}`}
                        aria-label={`Open conversation: ${item.first_user_message_preview ?? 'Conversation'}`}
                        aria-current={isCurrent ? 'true' : undefined}
                      >
                        <span className="recent-conversation-preview">
                          {item.first_user_message_preview ?? 'Conversation'}
                        </span>
                        <span className="recent-conversation-meta">
                          {item.updated_at} · {item.message_count}{' '}
                          {item.message_count === 1 ? 'message' : 'messages'}
                        </span>
                      </Link>
                      {isCurrent ? (
                        <span className="prototype-badge">Current</span>
                      ) : null}
                    </li>
                  )
                })}
              </ul>
            )}
            <Link className="recent-conversations-more" to="/app/history">
              View all conversations
            </Link>
          </section>
        </aside>
      </div>

      <div className="assistant-disclaimer">
        <DisclaimerBanner />
      </div>
    </div>
  )
}

export default Assistant
