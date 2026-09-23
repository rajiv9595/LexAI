import type {
  CaseContextData,
  ChatMessage,
  LegalAssessmentData,
  LegalReference,
  SuggestedPrompt,
} from '../types/assistant'

/**
 * Frontend prototype data for the Legal Assistant demo.
 * Everything here is static mock data. No backend, no network calls.
 */

export const sampleUserQuestionDemo =
  'I rented a house and my landlord is refusing to return my security deposit after I moved out. What should I do?'

export const sampleAssistantReplyDemo =
  "Based on the information you've provided, this appears to involve a rental or tenancy-related dispute. The specific rights and procedures can depend on the applicable jurisdiction and the terms of your rental agreement."

export const demoReferences: LegalReference[] = [
  {
    title: 'Rental / Tenancy Law',
    kind: 'General reference',
    note: 'Jurisdiction-specific rules should be verified before relying on this information.',
  },
  {
    title: 'Security Deposit Provisions',
    kind: 'General reference',
    note: 'Reference information will be connected to the legal knowledge service in a later implementation.',
  },
]

export const sampleLegalAssessmentDemo: LegalAssessmentData = {
  legalArea: 'Rental / Tenancy',
  situationSummary:
    'Your concern involves a security deposit that has not been returned after moving out of a rental property.',
  keyInformation: [
    'Rental agreement',
    'Security deposit amount',
    'Move-out date',
    'Communication with landlord',
  ],
  considerations: [
    'Review the rental agreement for provisions relating to security deposits.',
    'Keep records of payment, property condition and communication.',
    'Check the applicable local rules governing deposits and tenancy disputes.',
  ],
  nextSteps: [
    'Gather your rental agreement and payment records.',
    'Review written communication with the landlord.',
    'Document the condition of the property and move-out date.',
    'Check applicable local legal procedures.',
    'Consider professional legal assistance if the dispute continues.',
  ],
  references: demoReferences,
}

export const sampleCaseContextDemo: CaseContextData = {
  legalArea: 'Rental / Tenancy',
  status: 'Initial Assessment',
  availableItems: [
    'Rental agreement',
    'Security deposit amount',
    'Move-out date',
    'Communication with landlord',
  ],
  suggestedDocuments: [
    'Rental Agreement',
    'Payment Record',
    'Landlord Communication',
  ],
}

export const suggestedPromptsDemo: SuggestedPrompt[] = [
  { id: 'prompt-rental', label: 'Help me understand a rental dispute' },
  { id: 'prompt-contract', label: 'What should I check before signing a contract?' },
  { id: 'prompt-collect', label: 'What information should I collect for a legal issue?' },
]

export const initialMessagesDemo: ChatMessage[] = []
