import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import Button from '../components/Button'
import DisclaimerBanner from '../components/DisclaimerBanner'
import DocumentForm from '../components/DocumentForm'
import { createDraft, getDocumentTemplate } from '../services/documentService'
import { isDocumentType } from '../types/document'
import type { DocumentDraft, DocumentTemplate } from '../types/document'
import './pages.css'
import './CreateDocument.css'

type WorkflowStep = 'info' | 'review' | 'draft'

const steps: { id: WorkflowStep; label: string }[] = [
  { id: 'info', label: 'Information' },
  { id: 'review', label: 'Review' },
  { id: 'draft', label: 'Draft Preview' },
]

function validateValues(template: DocumentTemplate, values: Record<string, string>): Record<string, string> {
  const errors: Record<string, string> = {}
  for (const field of template.fields) {
    const raw = values[field.name] ?? ''
    const value = raw.trim()
    if (field.required && value.length === 0) {
      errors[field.name] = `${field.label} is required.`
      continue
    }
    if (value.length === 0) {
      continue
    }
    if (field.type === 'number') {
      const numeric = Number(value)
      if (!Number.isFinite(numeric) || numeric < 0) {
        errors[field.name] = 'Enter a valid non-negative number.'
      }
    }
    if (field.type === 'date' && Number.isNaN(Date.parse(value))) {
      errors[field.name] = 'Enter a valid date.'
    }
  }
  const startField = template.fields.find((field) => field.name === 'startDate')
  const endField = template.fields.find((field) => field.name === 'endDate')
  if (startField && endField && !errors.startDate && !errors.endDate) {
    const startRaw = (values.startDate ?? '').trim()
    const endRaw = (values.endDate ?? '').trim()
    if (startRaw && endRaw && Date.parse(endRaw) < Date.parse(startRaw)) {
      errors.endDate = 'End date should be after the start date.'
    }
  }
  return errors
}

function CreateDocument() {
  const [searchParams] = useSearchParams()
  const typeParam = searchParams.get('type')

  const [step, setStep] = useState<WorkflowStep>('info')
  const [values, setValues] = useState<Record<string, string>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [draft, setDraft] = useState<DocumentDraft | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [savedNote, setSavedNote] = useState('')

  useEffect(() => {
    setStep('info')
    setValues({})
    setErrors({})
    setDraft(null)
    setIsSubmitting(false)
    setSubmitError(null)
    setSavedNote('')
  }, [typeParam])

  if (typeParam === null) {
    return (
      <div className="page-container">
        <PageHeader
          title="Create Document"
          description="Start a new legal document draft."
        />
        <Card
          title="Choose a document type"
          description="Select a template to begin the guided process."
        >
          <Link className="btn btn-primary" to="/app/documents">
            Browse document types
          </Link>
        </Card>
      </div>
    )
  }

  if (!isDocumentType(typeParam)) {
    return (
      <div className="page-container">
        <PageHeader
          title="Create Document"
          description="Start a new legal document draft."
        />
        <Card
          title="Unknown document type"
          description={`“${typeParam}” is not a supported document type.`}
        >
          <Link className="btn btn-secondary" to="/app/documents">
            Back to Documents
          </Link>
        </Card>
      </div>
    )
  }

  const template = getDocumentTemplate(typeParam)
  const fieldLabels = new Map(template.fields.map((field) => [field.name, field.label]))

  function handleChange(name: string, value: string) {
    setValues((previous) => ({ ...previous, [name]: value }))
    setErrors((previous) => {
      if (!previous[name]) {
        return previous
      }
      const next = { ...previous }
      delete next[name]
      return next
    })
  }

  function handleReview() {
    const validationErrors = validateValues(template, values)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length === 0) {
      setSubmitError(null)
      setStep('review')
    }
  }

  async function handleGenerate() {
    setIsSubmitting(true)
    setSubmitError(null)
    try {
      const created = await createDraft(template.type, values)
      setDraft(created)
      setSavedNote('Draft successfully created and saved to your account.')
      setStep('draft')
    } catch (err) {
      setSubmitError(
        err instanceof Error
          ? err.message
          : 'Failed to create document draft. Please try again.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  const currentStepIndex = steps.findIndex((item) => item.id === step)

  return (
    <div className="page-container">
      <PageHeader
        title="Create Document"
        description={`Create a structured ${template.title.toLowerCase()} draft through guided steps.`}
      />
      <div className="create-stack">
        <ol className="step-indicator" aria-label="Document creation steps">
          {steps.map((item, index) => (
            <li
              key={item.id}
              aria-current={item.id === step ? 'step' : undefined}
              className={
                item.id === step
                  ? 'step-indicator-item step-indicator-item-current'
                  : index < currentStepIndex
                    ? 'step-indicator-item step-indicator-item-done'
                    : 'step-indicator-item'
              }
            >
              <span className="step-indicator-number">{index + 1}</span>
              <span>{item.label}</span>
              {index < steps.length - 1 ? (
                <span className="step-indicator-separator" aria-hidden="true" />
              ) : null}
            </li>
          ))}
        </ol>

        {submitError ? (
          <div className="alert alert-error" role="alert">
            <p>{submitError}</p>
          </div>
        ) : null}

        {step === 'info' ? (
          <Card
            title={`${template.title} — Information`}
            description="Enter the details below. Required fields are marked."
          >
            <DocumentForm
              template={template}
              values={values}
              errors={errors}
              onChange={handleChange}
            />
            <div className="form-actions">
              <Link className="btn btn-ghost" to="/app/documents">
                Back
              </Link>
              <Button onClick={handleReview}>Review Information</Button>
            </div>
          </Card>
        ) : null}

        {step === 'review' ? (
          <Card
            title="Review your information"
            description="Check the details below before generating and saving the draft."
          >
            <dl className="review-list">
              {template.fields.map((field) => {
                const value = (values[field.name] ?? '').trim()
                return (
                  <div key={field.name} className="review-row">
                    <dt className="review-term">{field.label}</dt>
                    <dd className="review-value">
                      {value ? (
                        value
                      ) : (
                        <span className="review-value-empty">Not provided</span>
                      )}
                    </dd>
                  </div>
                )
              })}
            </dl>
            <div className="form-actions">
              <Button
                variant="secondary"
                disabled={isSubmitting}
                onClick={() => setStep('info')}
              >
                Edit Information
              </Button>
              <Button disabled={isSubmitting} onClick={handleGenerate}>
                {isSubmitting ? 'Saving Draft...' : 'Generate Draft'}
              </Button>
            </div>
          </Card>
        ) : null}

        {step === 'draft' && draft ? (
          <>
            <div className="draft-paper">
              <p className="draft-paper-brand">LEXASSIST</p>
              <h2 className="draft-paper-title">{draft.title}</h2>
              <span className="draft-paper-status">{draft.status}</span>
              <p className="draft-paper-meta">Created: {draft.createdDate}</p>
              {template.sections.map((section) => (
                <section key={section.title} className="draft-section">
                  <h3 className="draft-section-title">{section.title}</h3>
                  {section.fields.map((fieldName) => {
                    const value = (draft.values[fieldName] ?? '').trim()
                    return (
                      <p key={fieldName} className="draft-section-row">
                        <span className="draft-field-label">
                          {fieldLabels.get(fieldName) ?? fieldName}:
                        </span>{' '}
                        {value ? (
                          value
                        ) : (
                          <span className="draft-field-empty">Not provided</span>
                        )}
                      </p>
                    )
                  })}
                </section>
              ))}
            </div>
            <p className="draft-disclaimer">
              This is a prototype draft for demonstration purposes. It may be
              incomplete or unsuitable for your specific legal circumstances.
              Review the document with a qualified legal professional before
              relying on it.
            </p>
            <DisclaimerBanner />
            <div className="draft-actions">
              <Link
                className="btn btn-primary"
                to={`/app/documents/${draft.id}`}
              >
                View in Documents
              </Link>
              <Link className="btn btn-secondary" to="/app/documents">
                Back to Documents
              </Link>
            </div>
            {savedNote ? <p className="saved-note">{savedNote}</p> : null}
          </>
        ) : null}

        {step !== 'draft' ? <DisclaimerBanner /> : null}
      </div>
    </div>
  )
}

export default CreateDocument
