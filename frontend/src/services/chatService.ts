/**
 * Legal Assistant chat service communicating with the authenticated FastAPI backend.
 */

import { ApiError, apiRequest } from './apiClient'
import type {
  AssistantConversationListResponse,
  AssistantConversationResponse,
  AssistantMessageRequest,
  AssistantMessageResponse,
  SuggestedPrompt,
} from '../types/assistant'

const SUGGESTED_PROMPTS: SuggestedPrompt[] = [
  {
    id: 'prompt-lease',
    label: 'What key clauses should I check in a residential lease agreement?',
  },
  {
    id: 'prompt-nda',
    label: 'What is standard confidentiality duration in a commercial NDA?',
  },
  {
    id: 'prompt-employment',
    label: 'How are notice period terms typically structured in employment contracts?',
  },
  {
    id: 'prompt-will',
    label: 'What is the role of an executor when creating a will?',
  },
]

export function getSuggestedPrompts(): SuggestedPrompt[] {
  return SUGGESTED_PROMPTS
}

export async function sendMessage(
  message: string,
  conversationId?: string,
): Promise<AssistantMessageResponse> {
  const payload: AssistantMessageRequest = {
    message: message.trim(),
    conversation_id: conversationId || undefined,
  }

  const response = await apiRequest<AssistantMessageResponse>(
    '/assistant/messages',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  )

  // The Assistant API is the source of truth for displayed references.
  // Normalize a missing field to [] and never fabricate metadata here.
  return {
    ...response,
    references: response.references ?? [],
  }
}

export async function getConversation(
  conversationId: string,
): Promise<AssistantConversationResponse> {
  return apiRequest<AssistantConversationResponse>(
    `/assistant/conversations/${conversationId}`,
  )
}

/**
 * STEP 24: lightweight paginated conversation list for the History UX.
 * Uses the shared authenticated client; never attaches tokens manually.
 */
export async function listConversations(
  page = 1,
  pageSize = 20,
): Promise<AssistantConversationListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  return apiRequest<AssistantConversationListResponse>(
    `/assistant/conversations?${params.toString()}`,
  )
}

export const AI_RATE_LIMITED_CODE = 'AI_PROVIDER_RATE_LIMITED'

export const AI_RATE_LIMITED_MESSAGE =
  'AI usage is temporarily limited. Please try again later.'

/** Recognize a provider rate-limit/429 failure without exposing internals. */
export function isAiRateLimited(error: unknown): boolean {
  if (!(error instanceof ApiError)) {
    return false
  }
  if (error.status === 429) {
    return true
  }
  const raw = error.rawErrors
  return (
    typeof raw === 'object' &&
    raw !== null &&
    (raw as { code?: unknown }).code === AI_RATE_LIMITED_CODE
  )
}

/** User-facing message for send failures; rate limits get a specific message. */
export function resolveSendErrorMessage(error: unknown): string {
  if (isAiRateLimited(error)) {
    return AI_RATE_LIMITED_MESSAGE
  }
  return error instanceof Error
    ? error.message
    : 'Failed to send message. Please try again.'
}

/**
 * STEP 30: classified send failure — the existing human-readable message
 * plus whether repeating the unchanged request may succeed.
 */
export interface ResolvedSendError {
  message: string
  retryable: boolean
}

/**
 * Statuses where a retry of the identical request may succeed.
 * 0 is the apiClient network-failure status (fetch threw before any
 * response). The client exposes no separate timeout signal, so no
 * timeout category is fabricated. Everything else — including unknown
 * shapes — defaults to non-retryable.
 */
const RETRYABLE_SEND_STATUS_CODES: ReadonlySet<number> = new Set([
  0, 429, 500, 502, 503, 504,
])

/** Classify a send failure without changing its human-readable message. */
export function resolveSendError(error: unknown): ResolvedSendError {
  return {
    message: resolveSendErrorMessage(error),
    retryable:
      error instanceof ApiError &&
      RETRYABLE_SEND_STATUS_CODES.has(error.status),
  }
}
