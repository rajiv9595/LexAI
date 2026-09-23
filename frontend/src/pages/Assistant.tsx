import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import DisclaimerBanner from '../components/DisclaimerBanner'
import CaseContext from '../components/CaseContext'
import {
  getConversation,
  getSuggestedPrompts,
  sendMessage,
} from '../services/chatService'
import type { ChatMessage } from '../types/assistant'
import './Assistant.css'

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
  const [error, setError] = useState<string | null>(null)

  const messagesEndRef = useRef<HTMLLIElement | null>(null)
  const suggestedPrompts = getSuggestedPrompts()

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
              })),
            )
          }
        })
        .catch((err) => {
          if (isMounted) {
            setError(
              err instanceof Error
                ? err.message
                : 'Failed to load conversation.',
            )
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

  const canSend = draft.trim().length > 0 && !isSending

  async function handleSend(textToSend?: string) {
    const messageText = (textToSend ?? draft).trim()
    if (!messageText || isSending) {
      return
    }

    const tempUserMsg: ChatMessage = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: 'Just now',
    }

    setMessages((prev) => [...prev, tempUserMsg])
    setDraft('')
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
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to send message. Please try again.',
      )
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
          <p>{error}</p>
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
                  {message.timestamp ? (
                    <p className="message-timestamp">{message.timestamp}</p>
                  ) : null}
                </li>
              ))}
              {isSending ? (
                <li className="message-row message-row-assistant">
                  <div className="message-bubble" style={{ opacity: 0.7 }}>
                    Consulting knowledge base...
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
            />
            <div className="chat-input-actions">
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
        </aside>
      </div>

      <div className="assistant-disclaimer">
        <DisclaimerBanner />
      </div>
    </div>
  )
}

export default Assistant
