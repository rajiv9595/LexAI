export type ChatRole = 'user' | 'assistant'

/**
 * Backend-validated research reference (STEP 21).
 * The Assistant API is the source of truth: the frontend never fabricates
 * citation metadata, prototype status, or source URLs.
 */
export interface ValidatedAssistantReference {
  source_id: string
  title: string
  citation_label: string
  source_type: string
  jurisdiction: string | null
  prototype: boolean
}

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  timestamp?: string
  references?: ValidatedAssistantReference[]
}

export interface SuggestedPrompt {
  id: string
  label: string
}

export interface LegalReference {
  title: string
  kind: string
  note: string
}

export interface LegalAssessmentData {
  legalArea: string
  situationSummary: string
  keyInformation: string[]
  considerations: string[]
  nextSteps: string[]
  references: LegalReference[]
}

export interface CaseContextData {
  legalArea: string
  status: string
  availableItems: string[]
  suggestedDocuments: string[]
}

export interface SessionContextData {
  conversationId: string | null
  status: string
  messageCount: number
  notice: string
}

/** Backend API DTOs */
export interface AssistantMessageRequest {
  message: string
  conversation_id?: string
}

export interface AssistantMessageResponse {
  conversation_id: string
  message_id: string
  role: string
  content: string
  prototype: boolean
  references?: ValidatedAssistantReference[]
}

export interface AssistantConversationMessage {
  message_id: string
  role: string
  content: string
  references?: ValidatedAssistantReference[]
}

export interface AssistantConversationResponse {
  conversation_id: string
  messages: AssistantConversationMessage[]
  prototype: boolean
}

/**
 * STEP 24 lightweight discovery item. No messages, references, prompts,
 * or provider data — full provenance loads via the detail endpoint only.
 */
export interface AssistantConversationListItem {
  conversation_id: string
  updated_at: string
  message_count: number
  first_user_message_preview: string | null
}

export interface AssistantConversationListResponse {
  items: AssistantConversationListItem[]
  page: number
  page_size: number
  total: number
}
