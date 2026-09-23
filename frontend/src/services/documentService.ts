/**
 * Document service communicating with the authenticated FastAPI backend.
 */

import { apiRequest } from './apiClient'
import {
  TEMPLATE_FORM_SCHEMAS,
  type DocumentDraft,
  type DocumentDraftRequest,
  type DocumentDraftResponse,
  type DocumentTemplate,
  type DocumentTemplateResponse,
  type DocumentType,
} from '../types/document'

function mapDocumentResponse(dto: DocumentDraftResponse): DocumentDraft {
  return {
    id: dto.document_id,
    type: dto.type,
    title: dto.title,
    createdDate: dto.created_date,
    status: dto.status,
    values: dto.details || {},
  }
}

const DEFAULT_TEMPLATES_FALLBACK: Record<
  DocumentType,
  { title: string; description: string; category: string }
> = {
  rental: {
    title: 'Rental Agreement',
    description:
      'Create a structured rental agreement draft from property and tenancy details.',
    category: 'Tenancy',
  },
  employment: {
    title: 'Employment Agreement',
    description:
      'Prepare a structured employment agreement draft from role and employment details.',
    category: 'Employment',
  },
  nda: {
    title: 'Non-Disclosure Agreement',
    description:
      'Create a structured NDA draft from the parties and confidentiality requirements.',
    category: 'Confidentiality',
  },
  will: {
    title: 'Will / Testament',
    description: 'Organize basic information for a will or testament draft.',
    category: 'Estate',
  },
}

export async function getDocumentTemplates(): Promise<DocumentTemplate[]> {
  try {
    const dtos = await apiRequest<DocumentTemplateResponse[]>(
      '/documents/templates',
    )
    return dtos.map((dto) => {
      const schema = TEMPLATE_FORM_SCHEMAS[dto.type] || {
        fields: [],
        sections: [],
      }
      return {
        type: dto.type,
        title: dto.title,
        description: dto.description,
        category: dto.category,
        fields: schema.fields,
        sections: schema.sections,
      }
    })
  } catch {
    return (['rental', 'employment', 'nda', 'will'] as DocumentType[]).map(
      (type) => getDocumentTemplate(type),
    )
  }
}

export function getDocumentTemplate(
  type: DocumentType,
  templates?: DocumentTemplate[],
): DocumentTemplate {
  if (templates && templates.length > 0) {
    const match = templates.find((item) => item.type === type)
    if (match) return match
  }
  const fallback = DEFAULT_TEMPLATES_FALLBACK[type]
  const schema = TEMPLATE_FORM_SCHEMAS[type] || { fields: [], sections: [] }
  return {
    type,
    title: fallback ? fallback.title : type,
    description: fallback ? fallback.description : '',
    category: fallback ? fallback.category : '',
    fields: schema.fields,
    sections: schema.sections,
  }
}

export async function getDocuments(): Promise<DocumentDraft[]> {
  const dtos = await apiRequest<DocumentDraftResponse[]>('/documents')
  return dtos.map(mapDocumentResponse)
}

export async function getDocument(id: string): Promise<DocumentDraft> {
  const dto = await apiRequest<DocumentDraftResponse>(`/documents/${id}`)
  return mapDocumentResponse(dto)
}

export async function createDraft(
  type: DocumentType,
  values: Record<string, string>,
): Promise<DocumentDraft> {
  const payload: DocumentDraftRequest = {
    type,
    details: values,
  }
  const dto = await apiRequest<DocumentDraftResponse>('/documents', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  return mapDocumentResponse(dto)
}
