import type { HistoryItem } from '../types/history'

/**
 * Frontend prototype data for the Case History workspace.
 * Sample records only. Nothing here represents real persistent activity.
 * No backend, no network calls.
 */

export const historyRecordsDemo: HistoryItem[] = [
  {
    id: 'history-rental-deposit-session',
    type: 'assistant',
    title: 'Rental Deposit Question',
    description:
      'Prototype assistant session demonstrating structured legal issue analysis.',
    createdAt: 'Sep 21, 2026',
    updatedAt: 'Sep 21, 2026',
    status: 'completed',
    relatedRoute: '/app/assistant',
    category: 'Rental / Housing',
    metadata: {
      kind: 'assistant',
      sessionTopic: 'Security deposit return',
      messageCount: 4,
    },
  },
  {
    id: 'history-rental-agreement-draft',
    type: 'document',
    title: 'Rental Agreement Draft',
    description:
      'Prototype document draft demonstrating the guided document workflow.',
    createdAt: 'Sep 20, 2026',
    updatedAt: 'Sep 20, 2026',
    status: 'draft',
    relatedRoute: '/app/documents/rental-agreement-demo',
    category: 'Tenancy',
    metadata: {
      kind: 'document',
      documentType: 'Rental Agreement',
      targetRoute: '/app/documents/rental-agreement-demo',
    },
  },
  {
    id: 'history-security-deposit-research',
    type: 'research',
    title: 'Security Deposit Dispute Research',
    description:
      'Prototype research activity demonstrating organized legal references.',
    createdAt: 'Sep 20, 2026',
    updatedAt: 'Sep 19, 2026',
    status: 'prototype',
    relatedRoute: '/app/research',
    category: 'Rental / Housing',
    metadata: {
      kind: 'research',
      topics: ['Security deposits', 'Tenant rights'],
      resultCount: 3,
    },
  },
  {
    id: 'history-employment-termination-session',
    type: 'assistant',
    title: 'Employment Termination Question',
    description:
      'Prototype assistant session demonstrating structured legal issue analysis.',
    createdAt: 'Sep 18, 2026',
    updatedAt: 'Sep 18, 2026',
    status: 'completed',
    relatedRoute: '/app/assistant',
    category: 'Employment',
    metadata: {
      kind: 'assistant',
      sessionTopic: 'Employment ending',
      messageCount: 6,
    },
  },
  {
    id: 'history-employment-agreement-draft',
    type: 'document',
    title: 'Employment Agreement Draft',
    description:
      'Prototype document draft demonstrating the guided document workflow.',
    createdAt: 'Sep 17, 2026',
    updatedAt: 'Sep 17, 2026',
    status: 'draft',
    relatedRoute: '/app/documents',
    category: 'Employment',
    metadata: {
      kind: 'document',
      documentType: 'Employment Agreement',
      targetRoute: '/app/documents',
    },
  },
  {
    id: 'history-employment-termination-research',
    type: 'research',
    title: 'Employment Termination Research',
    description:
      'Prototype research activity demonstrating organized legal references.',
    createdAt: 'Sep 16, 2026',
    updatedAt: 'Sep 16, 2026',
    status: 'prototype',
    relatedRoute: '/app/research',
    category: 'Employment',
    metadata: {
      kind: 'research',
      topics: ['Employment', 'Workplace procedures'],
      resultCount: 2,
    },
  },
  {
    id: 'history-consumer-rights-session',
    type: 'assistant',
    title: 'Consumer Rights Question',
    description:
      'Prototype assistant session demonstrating structured legal issue analysis.',
    createdAt: 'Sep 14, 2026',
    updatedAt: 'Sep 14, 2026',
    status: 'completed',
    relatedRoute: '/app/assistant',
    category: 'Consumer',
    metadata: {
      kind: 'assistant',
      sessionTopic: 'Faulty product refund',
      messageCount: 3,
    },
  },
  {
    id: 'history-nda-draft',
    type: 'document',
    title: 'Non-Disclosure Agreement Draft',
    description:
      'Prototype document draft demonstrating the guided document workflow.',
    createdAt: 'Sep 12, 2026',
    updatedAt: 'Sep 12, 2026',
    status: 'draft',
    relatedRoute: '/app/documents',
    category: 'Confidentiality',
    metadata: {
      kind: 'document',
      documentType: 'Non-Disclosure Agreement',
      targetRoute: '/app/documents',
    },
  },
  {
    id: 'history-confidentiality-research',
    type: 'research',
    title: 'Confidentiality Obligations Research',
    description:
      'Prototype research activity demonstrating organized legal references.',
    createdAt: 'Sep 10, 2026',
    updatedAt: 'Sep 10, 2026',
    status: 'prototype',
    relatedRoute: '/app/research',
    category: 'Confidentiality',
    metadata: {
      kind: 'research',
      topics: ['Confidentiality', 'Business agreements'],
      resultCount: 2,
    },
  },
  {
    id: 'history-will-draft',
    type: 'document',
    title: 'Will / Testament Draft',
    description:
      'Prototype document draft demonstrating the guided document workflow.',
    createdAt: 'Sep 08, 2026',
    updatedAt: 'Sep 08, 2026',
    status: 'draft',
    relatedRoute: '/app/documents',
    category: 'Estate',
    metadata: {
      kind: 'document',
      documentType: 'Will / Testament',
      targetRoute: '/app/documents',
    },
  },
]
