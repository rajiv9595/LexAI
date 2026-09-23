import type { DocumentDraft, DocumentTemplate } from '../types/document'

/**
 * Frontend prototype data for the Document Assistant demo.
 * Static mock data only. No backend, no network calls.
 * Drafts shown here are illustrative prototypes, not legally valid documents.
 */

export const documentTemplatesDemo: DocumentTemplate[] = [
  {
    type: 'rental',
    title: 'Rental Agreement',
    description:
      'Create a structured rental agreement draft from property and tenancy details.',
    category: 'Tenancy',
    fields: [
      { name: 'landlordName', label: 'Landlord Full Name', type: 'text', required: true, placeholder: 'Rajiv Reddy' },
      { name: 'tenantName', label: 'Tenant Full Name', type: 'text', required: true, placeholder: 'Example Tenant' },
      { name: 'propertyAddress', label: 'Property Address', type: 'text', required: true, placeholder: 'Example Address' },
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
  {
    type: 'employment',
    title: 'Employment Agreement',
    description:
      'Prepare a structured employment agreement draft from role and employment details.',
    category: 'Employment',
    fields: [
      { name: 'employerName', label: 'Employer Name', type: 'text', required: true, placeholder: 'Example Company' },
      { name: 'employeeName', label: 'Employee Name', type: 'text', required: true, placeholder: 'Example Employee' },
      { name: 'jobTitle', label: 'Job Title', type: 'text', required: true, placeholder: 'Example Role' },
      { name: 'startDate', label: 'Employment Start Date', type: 'date', required: true },
      { name: 'workLocation', label: 'Work Location', type: 'text', required: true, placeholder: 'Example City' },
      { name: 'salary', label: 'Salary / Compensation', type: 'text', required: true, placeholder: 'Example compensation' },
      { name: 'additionalTerms', label: 'Additional Terms', type: 'textarea', required: false, placeholder: 'Any additional terms (optional)' },
    ],
    sections: [
      { title: 'Parties', fields: ['employerName', 'employeeName'] },
      { title: 'Role', fields: ['jobTitle', 'workLocation'] },
      { title: 'Term and Compensation', fields: ['startDate', 'salary'] },
      { title: 'Additional Terms', fields: ['additionalTerms'] },
    ],
  },
  {
    type: 'nda',
    title: 'Non-Disclosure Agreement',
    description:
      'Create a structured NDA draft from the parties and confidentiality requirements.',
    category: 'Confidentiality',
    fields: [
      { name: 'disclosingParty', label: 'Disclosing Party', type: 'text', required: true, placeholder: 'Example Party A' },
      { name: 'receivingParty', label: 'Receiving Party', type: 'text', required: true, placeholder: 'Example Party B' },
      { name: 'purpose', label: 'Purpose of Agreement', type: 'text', required: true, placeholder: 'Example purpose' },
      { name: 'confidentialInfo', label: 'Confidential Information Description', type: 'textarea', required: true, placeholder: 'Describe the confidential information' },
      { name: 'effectiveDate', label: 'Effective Date', type: 'date', required: true },
      { name: 'additionalTerms', label: 'Additional Terms', type: 'textarea', required: false, placeholder: 'Any additional terms (optional)' },
    ],
    sections: [
      { title: 'Parties', fields: ['disclosingParty', 'receivingParty'] },
      { title: 'Agreement Details', fields: ['purpose', 'confidentialInfo', 'effectiveDate'] },
      { title: 'Additional Terms', fields: ['additionalTerms'] },
    ],
  },
  {
    type: 'will',
    title: 'Will / Testament',
    description: 'Organize basic information for a will or testament draft.',
    category: 'Estate',
    fields: [
      { name: 'testatorName', label: 'Testator Full Name', type: 'text', required: true, placeholder: 'Example Name' },
      { name: 'dateOfBirth', label: 'Date of Birth', type: 'date', required: true },
      { name: 'beneficiary', label: 'Primary Beneficiary', type: 'text', required: true, placeholder: 'Example Beneficiary' },
      { name: 'executor', label: 'Executor Name', type: 'text', required: true, placeholder: 'Example Executor' },
      { name: 'additionalInstructions', label: 'Additional Instructions', type: 'textarea', required: false, placeholder: 'Any additional instructions (optional)' },
    ],
    sections: [
      { title: 'Testator', fields: ['testatorName', 'dateOfBirth'] },
      { title: 'Key Persons', fields: ['beneficiary', 'executor'] },
      { title: 'Additional Instructions', fields: ['additionalInstructions'] },
    ],
  },
]

export const examplePrototypeDocumentDemo: DocumentDraft = {
  id: 'rental-agreement-demo',
  type: 'rental',
  title: 'Rental Agreement Draft',
  createdDate: 'Sep 20, 2026',
  status: 'Prototype Draft',
  values: {
    landlordName: 'Rajiv Reddy',
    tenantName: 'Example Tenant',
    propertyAddress: 'Example Address',
    monthlyRent: '15000',
    securityDeposit: '30000',
    startDate: '2026-10-01',
    endDate: '2027-09-30',
    additionalTerms: '',
  },
}
