import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import DisclaimerBanner from '../components/DisclaimerBanner'
import {
  getDocumentTemplates,
  getDocuments,
} from '../services/documentService'
import type { DocumentDraft, DocumentTemplate, DocumentType } from '../types/document'
import './pages.css'
import './Documents.css'

function TemplateIcon({ children }: { children: ReactNode }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 18 18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  )
}

const templateIcons: Record<DocumentType, ReactNode> = {
  rental: (
    <TemplateIcon>
      <path d="M2.5 8L9 2.5 15.5 8" />
      <path d="M4.5 7v7.5h9V7" />
      <path d="M7.5 14.5v-4h3v4" />
    </TemplateIcon>
  ),
  employment: (
    <TemplateIcon>
      <rect x="2.5" y="5" width="13" height="9" rx="1.5" />
      <path d="M6 5V3.5h6V5" />
      <path d="M2.5 9h13" />
    </TemplateIcon>
  ),
  nda: (
    <TemplateIcon>
      <rect x="3.5" y="7.5" width="11" height="8" rx="1.5" />
      <path d="M6 7.5V5.5a3 3 0 0 1 6 0v2" />
      <circle cx="9" cy="11.5" r="1.2" />
    </TemplateIcon>
  ),
  will: (
    <TemplateIcon>
      <path d="M4.5 1.5h6L14 5v11.5h-9.5v-15z" />
      <path d="M10.5 1.5V5H14" />
      <path d="M7 9h4M7 11.5h4" />
    </TemplateIcon>
  ),
}

function Documents() {
  const [templates, setTemplates] = useState<DocumentTemplate[]>([])
  const [documents, setDocuments] = useState<DocumentDraft[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function loadData() {
      setIsLoading(true)
      setError(null)
      try {
        const [fetchedTemplates, fetchedDocs] = await Promise.all([
          getDocumentTemplates(),
          getDocuments(),
        ])
        if (isMounted) {
          setTemplates(fetchedTemplates)
          setDocuments(fetchedDocs)
        }
      } catch (err) {
        if (isMounted) {
          setError(
            err instanceof Error
              ? err.message
              : 'Failed to load documents from server.',
          )
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void loadData()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="page-container">
      <PageHeader
        title="Document Assistant"
        description="Create structured legal document drafts through a guided process."
      />

      {error ? (
        <div className="alert alert-error" role="alert">
          <p>{error}</p>
        </div>
      ) : null}

      {/* User's Created Documents Section */}
      <section className="user-documents-section" aria-label="Your Documents">
        <h2 className="documents-section-title">Your Documents</h2>
        <p className="documents-section-subtitle">
          Draft documents created and stored in your account.
        </p>

        {isLoading ? (
          <div className="documents-loading-card">
            <p>Loading your documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="documents-empty-state">
            <p className="documents-empty-title">No documents yet.</p>
            <p className="documents-empty-text">
              Select one of the templates below to create your first legal
              document draft.
            </p>
          </div>
        ) : (
          <ul className="user-document-list">
            {documents.map((doc) => (
              <li key={doc.id} className="user-document-item">
                <Card title={doc.title}>
                  <div className="user-document-card-inner">
                    <div className="user-document-meta">
                      <span className="user-document-type">
                        {doc.type.toUpperCase()}
                      </span>
                      <span className="user-document-status">{doc.status}</span>
                      <span className="user-document-date">
                        Created: {doc.createdDate}
                      </span>
                    </div>
                    <div className="user-document-action">
                      <Link
                        className="btn btn-secondary"
                        to={`/app/documents/${doc.id}`}
                      >
                        View Details
                      </Link>
                    </div>
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Template Gallery */}
      <section
        className="document-templates-section"
        aria-label="Available Templates"
      >
        <h2 className="documents-section-title">Choose a document type</h2>
        <p className="documents-section-subtitle">
          Drafts created here are structured prototypes. Review them with a
          qualified legal professional before relying on them.
        </p>

        <ul className="document-template-grid">
          {templates.map((template) => (
            <li key={template.type}>
              <Card title={template.title} description={template.description}>
                <div className="document-template-card-inner">
                  <span className="document-template-icon">
                    {templateIcons[template.type]}
                  </span>
                  <p className="document-template-category">
                    {template.category}
                  </p>
                  <div className="document-template-action">
                    <Link
                      className="btn btn-secondary"
                      to={`/app/documents/create?type=${template.type}`}
                    >
                      Start
                    </Link>
                  </div>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      </section>

      <div className="documents-footer">
        <DisclaimerBanner />
      </div>
    </div>
  )
}

export default Documents
