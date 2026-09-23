import type { DocumentTemplate } from '../types/document'
import './DocumentForm.css'

interface DocumentFormProps {
  template: DocumentTemplate
  values: Record<string, string>
  errors: Record<string, string>
  onChange: (name: string, value: string) => void
}

function DocumentForm({ template, values, errors, onChange }: DocumentFormProps) {
  return (
    <div className="document-form-grid document-form">
      {template.fields.map((field) => {
        const fieldId = `doc-field-${field.name}`
        const errorId = `doc-field-error-${field.name}`
        const error = errors[field.name]
        const isFullWidth = field.type === 'textarea'
        return (
          <div
            key={field.name}
            className={`document-form-field${isFullWidth ? ' document-form-field-full' : ''}`}
          >
            <label className="document-form-label" htmlFor={fieldId}>
              {field.label}{' '}
              {field.required ? (
                <span className="required-indicator">(Required)</span>
              ) : (
                <span className="required-indicator">(Optional)</span>
              )}
            </label>
            {field.type === 'textarea' ? (
              <textarea
                id={fieldId}
                className="document-form-textarea"
                value={values[field.name] ?? ''}
                placeholder={field.placeholder}
                aria-required={field.required}
                aria-invalid={Boolean(error)}
                aria-describedby={error ? errorId : undefined}
                onChange={(event) => onChange(field.name, event.target.value)}
              />
            ) : (
              <input
                id={fieldId}
                className="document-form-input"
                type={field.type}
                value={values[field.name] ?? ''}
                placeholder={field.placeholder}
                aria-required={field.required}
                aria-invalid={Boolean(error)}
                aria-describedby={error ? errorId : undefined}
                min={field.type === 'number' ? 0 : undefined}
                onChange={(event) => onChange(field.name, event.target.value)}
              />
            )}
            {error ? (
              <p className="field-error" id={errorId} role="alert">
                {error}
              </p>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}

export default DocumentForm
