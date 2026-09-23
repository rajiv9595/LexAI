export type DocumentType = 'rental' | 'employment' | 'nda' | 'will'

export type DocumentStatus = 'Prototype Draft' | string

export type DocumentFieldType = 'text' | 'textarea' | 'date' | 'number'

export interface DocumentField {
  name: string
  label: string
  type: DocumentFieldType
  required: boolean
  placeholder?: string
  description?: string
}

export interface DocumentSection {
  title: string
  fields: string[]
}

export interface DocumentTemplate {
  type: DocumentType
  title: string
  description: string
  category: string
  fields: DocumentField[]
  sections: DocumentSection[]
}

export interface DocumentDraft {
  id: string
  type: DocumentType
  title: string
  createdDate: string
  status: DocumentStatus
  values: Record<string, string>
}

/** Backend API DTOs */
export interface DocumentDraftResponse {
  document_id: string
  type: DocumentType
  title: string
  status: string
  created_date: string
  details: Record<string, string>
  prototype: boolean
}

export interface DocumentTemplateResponse {
  type: DocumentType
  title: string
  description: string
  category: string
}

export interface DocumentDraftRequest {
  type: DocumentType
  details: Record<string, string>
}

export function isDocumentType(value: string | null): value is DocumentType {
  return (
    value === 'rental' ||
    value === 'employment' ||
    value === 'nda' ||
    value === 'will'
  )
}

/** Form layout definitions for the guided draft forms */
export const TEMPLATE_FORM_SCHEMAS: Record<
  DocumentType,
  { fields: DocumentField[]; sections: DocumentSection[] }
> = {
  rental: {
    fields: [
      { name: 'landlordName', label: 'Landlord Full Name', type: 'text', required: true, placeholder: 'Landlord Name' },
      { name: 'tenantName', label: 'Tenant Full Name', type: 'text', required: true, placeholder: 'Tenant Name' },
      { name: 'propertyAddress', label: 'Property Address', type: 'text', required: true, placeholder: 'Property Address' },
      { name: 'monthlyRent', label: 'Monthly Rent', type: 'number', required: true, placeholder: '15000' },
      { name: 'securityDeposit', label: 'Security Deposit', type: 'number', required: true, placeholder: '30000' },
      { name: 'startDate', label: 'Agreement Start Date', type: 'date', required: true },
      { name: 'endDate', label: 'Agreement End Date', type: 'date', required: true },
      { name: 'additionalTerms', label: 'Additional Terms', type: 'textarea', required: false, placeholder: 'Any additional terms (optional)' },
    ],
    sections: [
      { title: 'Parties', fields: ['landlordName', 'tenantName'] },
      { title: 'Property', fields: ['propertyAddress'] },
      { title: 'Term', fields: ['startDate', 'endDate'] },
      { title: 'Financial Details', fields: ['monthlyRent', 'securityDeposit'] },
      { title: 'Additional Terms', fields: ['additionalTerms'] },
    ],
  },
  employment: {
    fields: [
      { name: 'employerName', label: 'Employer Name', type: 'text', required: true, placeholder: 'Company Name' },
      { name: 'employeeName', label: 'Employee Name', type: 'text', required: true, placeholder: 'Employee Name' },
      { name: 'jobTitle', label: 'Job Title', type: 'text', required: true, placeholder: 'Role Title' },
      { name: 'startDate', label: 'Employment Start Date', type: 'date', required: true },
      { name: 'workLocation', label: 'Work Location', type: 'text', required: true, placeholder: 'Location' },
      { name: 'salary', label: 'Salary / Compensation', type: 'text', required: true, placeholder: 'Compensation details' },
      { name: 'additionalTerms', label: 'Additional Terms', type: 'textarea', required: false, placeholder: 'Any additional terms (optional)' },
    ],
    sections: [
      { title: 'Parties', fields: ['employerName', 'employeeName'] },
      { title: 'Role', fields: ['jobTitle', 'workLocation'] },
      { title: 'Term and Compensation', fields: ['startDate', 'salary'] },
      { title: 'Additional Terms', fields: ['additionalTerms'] },
    ],
  },
  nda: {
    fields: [
      { name: 'disclosingParty', label: 'Disclosing Party', type: 'text', required: true, placeholder: 'Disclosing Party' },
      { name: 'receivingParty', label: 'Receiving Party', type: 'text', required: true, placeholder: 'Receiving Party' },
      { name: 'purpose', label: 'Purpose of Agreement', type: 'text', required: true, placeholder: 'Purpose description' },
      { name: 'confidentialInfo', label: 'Confidential Information Description', type: 'textarea', required: true, placeholder: 'Describe confidential information' },
      { name: 'effectiveDate', label: 'Effective Date', type: 'date', required: true },
      { name: 'additionalTerms', label: 'Additional Terms', type: 'textarea', required: false, placeholder: 'Any additional terms (optional)' },
    ],
    sections: [
      { title: 'Parties', fields: ['disclosingParty', 'receivingParty'] },
      { title: 'Agreement Details', fields: ['purpose', 'confidentialInfo', 'effectiveDate'] },
      { title: 'Additional Terms', fields: ['additionalTerms'] },
    ],
  },
  will: {
    fields: [
      { name: 'testatorName', label: 'Testator Full Name', type: 'text', required: true, placeholder: 'Testator Name' },
      { name: 'dateOfBirth', label: 'Date of Birth', type: 'date', required: true },
      { name: 'beneficiary', label: 'Primary Beneficiary', type: 'text', required: true, placeholder: 'Beneficiary Name' },
      { name: 'executor', label: 'Executor Name', type: 'text', required: true, placeholder: 'Executor Name' },
      { name: 'additionalInstructions', label: 'Additional Instructions', type: 'textarea', required: false, placeholder: 'Any additional instructions (optional)' },
    ],
    sections: [
      { title: 'Testator', fields: ['testatorName', 'dateOfBirth'] },
      { title: 'Key Persons', fields: ['beneficiary', 'executor'] },
      { title: 'Additional Instructions', fields: ['additionalInstructions'] },
    ],
  },
}
