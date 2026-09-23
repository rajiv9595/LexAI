/**
 * Legal Assistant chat service communicating with the authenticated FastAPI backend.
 */

import { apiRequest } from './apiClient'
import type {
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

  return apiRequest<AssistantMessageResponse>('/assistant/messages', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getConversation(
  conversationId: string,
): Promise<AssistantConversationResponse> {
  return apiRequest<AssistantConversationResponse>(
    `/assistant/conversations/${conversationId}`,
  )
}
