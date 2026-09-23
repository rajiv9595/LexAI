import type { ResearchResult } from '../types/research'
import './ResearchDetail.css'

interface ResearchDetailProps {
  result: ResearchResult
  onUseAsStartingPoint: (result: ResearchResult) => void
  onClose: () => void
}

function ResearchDetail({ result, onUseAsStartingPoint, onClose }: ResearchDetailProps) {
  return (
    <section className="research-detail" aria-label="Selected research record">
      <div className="research-result-meta">
        <span className="source-type-label">{result.sourceType}</span>
        <span className="prototype-label">Prototype</span>
      </div>
      <h3 className="research-detail-title">{result.title}</h3>
      <p className="research-detail-facts">
        {result.jurisdiction} · {result.date} · {result.citationLabel}
      </p>
      <p className="research-result-summary-label">Summary</p>
      <p className="research-result-summary">{result.summary}</p>
      <p className="research-result-relevance-label">Why this result is relevant</p>
      <p className="research-result-relevance">{result.relevanceReason}</p>
      <p className="research-result-topics-label">Topics</p>
      <ul className="research-result-topics">
        {result.topics.map((topic) => (
          <li key={topic}>{topic}</li>
        ))}
      </ul>
      <p className="research-detail-note">
        <strong>Prototype Research Note: </strong>
        Reference information shown here is part of the LexAssist prototype
        dataset and should not be treated as authoritative legal research.
      </p>
      <div className="research-result-action">
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => onUseAsStartingPoint(result)}
        >
          Use as research starting point
        </button>{' '}
        <button type="button" className="btn btn-ghost" onClick={onClose}>
          Close
        </button>
      </div>
    </section>
  )
}

export default ResearchDetail
