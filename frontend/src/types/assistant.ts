export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  timestamp?: string
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
}

export interface AssistantConversationMessage {
  message_id: string
  role: string
  content: string
}

export interface AssistantConversationResponse {
  conversation_id: string
  messages: AssistantConversationMessage[]
  prototype: boolean
}
