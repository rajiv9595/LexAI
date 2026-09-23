import type { LegalAssessmentData } from '../types/assistant'
import './LegalAssessment.css'

interface LegalAssessmentProps {
  assessment: LegalAssessmentData
}

function LegalAssessment({ assessment }: LegalAssessmentProps) {
  return (
    <section className="legal-assessment" aria-label="Understanding your concern">
      <div className="legal-assessment-header">
        <h3 className="legal-assessment-title">Understanding your concern</h3>
      </div>
      <div className="legal-assessment-body">
        <div className="legal-assessment-block">
          <p className="legal-assessment-label">Legal area</p>
          <p className="legal-assessment-text">{assessment.legalArea}</p>
        </div>

        <div className="legal-assessment-block">
          <p className="legal-assessment-label">Situation summary</p>
          <p className="legal-assessment-text">{assessment.situationSummary}</p>
        </div>

        <div className="legal-assessment-block">
          <p className="legal-assessment-label">Key information</p>
          <ul className="legal-assessment-list">
            {assessment.keyInformation.map((item) => (
              <li key={item} className="legal-assessment-list-item">
                <svg
                  className="legal-assessment-check"
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                  focusable="false"
                >
                  <path d="M2.5 7.5l3 3 6-7" />
                </svg>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="legal-assessment-block">
          <p className="legal-assessment-label">Potential considerations</p>
          <ul className="legal-assessment-list">
            {assessment.considerations.map((item) => (
              <li key={item} className="legal-assessment-list-item">
                <span aria-hidden="true">–</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="legal-assessment-block">
          <p className="legal-assessment-label">Suggested next steps</p>
          <ol className="legal-assessment-steps">
            {assessment.nextSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>

        <div className="legal-assessment-block">
          <p className="legal-assessment-label">Relevant references</p>
          {assessment.references.map((reference) => (
            <div key={reference.title} className="legal-assessment-reference">
              <p className="legal-assessment-reference-title">{reference.title}</p>
              <p className="legal-assessment-reference-kind">{reference.kind}</p>
              <p className="legal-assessment-reference-note">{reference.note}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default LegalAssessment
