import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import DisclaimerBanner from '../components/DisclaimerBanner'
import { getDocument, getDocumentTemplate } from '../services/documentService'
import type { DocumentDraft } from '../types/document'
import { ApiError } from '../services/apiClient'
import './pages.css'
import './CreateDocument.css'
import './DocumentDetails.css'

function DocumentDetails() {
  const { id } = useParams<{ id: string }>()
  const [document, setDocument] = useState<DocumentDraft | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorStatus, setErrorStatus] = useState<number | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    if (!id) {
      setIsLoading(false)
      setErrorStatus(404)
      return
    }

    async function fetchDoc() {
      setIsLoading(true)
      setErrorStatus(null)
      setErrorMessage(null)
      try {
        const data = await getDocument(id!)
        if (isMounted) {
          setDocument(data)
        }
      } catch (err) {
        if (isMounted) {
          if (err instanceof ApiError) {
            setErrorStatus(err.status)
            setErrorMessage(err.detail)
          } else {
            setErrorStatus(500)
            setErrorMessage('An unexpected error occurred.')
          }
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void fetchDoc()

    return () => {
      isMounted = false
    }
  }, [id])

  if (isLoading) {
    return (
      <div className="page-container">
        <PageHeader
          title="Document Details"
          description="Loading document draft..."
        />
        <Card title="Loading document" description="Retrieving details from server...">
          <p>Please wait...</p>
        </Card>
      </div>
    )
  }

  if (errorStatus === 404 || !document) {
    return (
      <div className="page-container">
        <PageHeader
          title="Document Details"
          description="View a legal document draft."
        />
        <Card
          title="Document not found"
          description="The requested document does not exist or belongs to another account."
        >
          <div className="detail-actions">
            <Link className="btn btn-secondary" to="/app/documents">
              Back to Documents
            </Link>
          </div>
        </Card>
      </div>
    )
  }

  if (errorMessage && errorStatus !== 404) {
    return (
      <div className="page-container">
        <PageHeader
          title="Document Details"
          description="View a legal document draft."
        />
        <Card
          title="Unable to load document"
          description={errorMessage}
        >
          <div className="detail-actions">
            <Link className="btn btn-secondary" to="/app/documents">
              Back to Documents
            </Link>
          </div>
        </Card>
      </div>
    )
  }

  const template = getDocumentTemplate(document.type)
  const fieldLabels = new Map(
    template.fields.map((field) => [field.name, field.label]),
  )

  return (
    <div className="page-container">
      <PageHeader
        title={document.title}
        description="View your saved legal document draft."
      />
      <div className="detail-stack">
        <Card
          title="Draft information"
          description="Stored in your account. Review details below."
        >
          <div className="detail-meta">
            <div>
              <p className="detail-meta-label">Document type</p>
              <p className="detail-meta-value">{template.title}</p>
            </div>
            <div>
              <p className="detail-meta-label">Created</p>
              <p className="detail-meta-value">{document.createdDate}</p>
            </div>
            <div>
              <p className="detail-meta-label">Status</p>
              <p className="detail-meta-value">{document.status}</p>
            </div>
          </div>
        </Card>

        <Card title="Structured sections" description="Information captured in this draft.">
          {template.sections.map((section) => (
            <section key={section.title} className="draft-section">
              <h3 className="draft-section-title">{section.title}</h3>
              {section.fields.map((fieldName) => {
                const value = (document.values[fieldName] ?? '').trim()
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
        </Card>

        <div className="detail-actions">
          <Link
            className="btn btn-primary"
            to={`/app/documents/create?type=${document.type}`}
          >
            Create Similar Draft
          </Link>
          <Link className="btn btn-secondary" to="/app/documents">
            Back to Documents
          </Link>
        </div>
        <p className="prototype-note">
          Prototype draft for demonstration purposes. Not a legally binding contract.
        </p>
        <DisclaimerBanner />
      </div>
    </div>
  )
}

export default DocumentDetails
