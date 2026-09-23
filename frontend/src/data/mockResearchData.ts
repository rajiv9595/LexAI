import type { ResearchResult, ResearchSummary } from '../types/research'
import { PROTOTYPE_JURISDICTION } from '../types/research'

/**
 * Frontend prototype data for the Legal Research demo.
 * Clearly labeled demo records only. Nothing here is an authoritative
 * legal source. No backend, no network calls.
 */

export const researchRecordsDemo: ResearchResult[] = [
  {
    id: 'rental-deposit-dispute',
    title: 'Rental Deposit Dispute — Prototype Research Record',
    sourceType: 'case',
    jurisdiction: PROTOTYPE_JURISDICTION,
    date: 'Sep 20, 2026',
    citationLabel: 'Demo case record',
    summary:
      'A demonstration record showing how rental-deposit issues could be organized for legal research.',
    relevanceReason: 'General prototype record.',
    topics: ['Rental housing', 'Security deposit', 'Tenant rights'],
    status: 'Prototype',
  },
  {
    id: 'employment-termination',
    title: 'Employment Termination — Prototype Research Record',
    sourceType: 'precedent',
    jurisdiction: PROTOTYPE_JURISDICTION,
    date: 'Sep 12, 2026',
    citationLabel: 'Prototype reference',
    summary:
      'A demonstration record showing how employment-ending scenarios could be organized for legal research.',
    relevanceReason: 'General prototype record.',
    topics: ['Employment', 'Termination procedures', 'Workplace rights'],
    status: 'Prototype',
  },
  {
    id: 'confidentiality-obligations',
    title: 'Confidentiality Obligations — Prototype Research Record',
    sourceType: 'regulation',
    jurisdiction: PROTOTYPE_JURISDICTION,
    date: 'Aug 28, 2026',
    citationLabel: 'Prototype reference',
    summary:
      'A demonstration record showing how confidentiality duties could be organized for legal research.',
    relevanceReason: 'General prototype record.',
    topics: ['Confidentiality', 'Business agreements', 'Disclosure duties'],
    status: 'Prototype',
  },
  {
    id: 'property-ownership-dispute',
    title: 'Property Ownership Dispute — Prototype Research Record',
    sourceType: 'statute',
    jurisdiction: PROTOTYPE_JURISDICTION,
    date: 'Aug 15, 2026',
    citationLabel: 'General reference',
    summary:
      'A demonstration record showing how property-ownership questions could be organized for legal research.',
    relevanceReason: 'General prototype record.',
    topics: ['Property ownership', 'Title records', 'Boundary questions'],
    status: 'Prototype',
  },
  {
    id: 'contract-signing-checklist',
    title: 'Contract Review Basics — Prototype Research Record',
    sourceType: 'general-reference',
    jurisdiction: PROTOTYPE_JURISDICTION,
    date: 'Jul 30, 2026',
    citationLabel: 'General reference',
    summary:
      'A demonstration record showing how contract-review topics could be organized for legal research.',
    relevanceReason: 'General prototype record.',
    topics: ['Contracts', 'Review checklist', 'Signatures'],
    status: 'Prototype',
  },
  {
    id: 'tenant-repair-duties',
    title: 'Repairs and Maintenance Duties — Prototype Research Record',
    sourceType: 'general-reference',
    jurisdiction: PROTOTYPE_JURISDICTION,
    date: 'Jul 18, 2026',
    citationLabel: 'General reference',
    summary:
      'A demonstration record showing how repair-duty questions could be organized for legal research.',
    relevanceReason: 'General prototype record.',
    topics: ['Rental housing', 'Repairs', 'Tenant rights'],
    status: 'Prototype',
  },
]

export const researchSummariesDemo: ResearchSummary[] = [
  {
    query: 'security deposit dispute',
    issue: 'Prototype classification of a rental-deposit dispute.',
    keyPoints: [
      'Identify the type of dispute.',
      'Gather relevant facts and documents.',
      'Check the applicable jurisdiction.',
      'Verify authoritative sources before relying on the information.',
    ],
    considerations: [
      'Jurisdiction can affect the applicable rules.',
      'Facts and dates may materially change the analysis.',
      'Prototype references require independent verification.',
    ],
    relatedTopics: ['Rental agreements', 'Security deposits', 'Tenant-landlord disputes'],
  },
  {
    query: 'employment termination',
    issue: 'Prototype classification of an employment-ending scenario.',
    keyPoints: [
      'Identify the employment relationship and role.',
      'Gather the employment agreement and related correspondence.',
      'Check the applicable jurisdiction.',
      'Verify authoritative sources before relying on the information.',
    ],
    considerations: [
      'Employment terms and local rules vary widely.',
      'Written records may materially change the analysis.',
      'Prototype references require independent verification.',
    ],
    relatedTopics: ['Employment agreements', 'Workplace procedures', 'Employee rights'],
  },
]
