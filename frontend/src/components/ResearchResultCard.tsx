import type { ResearchResult } from '../types/research'
import './ResearchResultCard.css'

const SOURCE_TYPE_LABELS: Record<ResearchResult['sourceType'], string> = {
  statute: 'Statute',
  case: 'Case',
  precedent: 'Precedent',
  regulation: 'Regulation',
  'general-reference': 'General Reference',
}

interface ResearchResultCardProps {
  result: ResearchResult
  selected: boolean
  onSelect: (id: string) => void
}

function ResearchResultCard({ result, selected, onSelect }: ResearchResultCardProps) {
  return (
    <article
      className={
        selected
          ? 'research-result-card research-result-card-selected'
          : 'research-result-card'
      }
      aria-current={selected ? 'true' : undefined}
      aria-label={`${result.title} (prototype record)`}
    >
      <div className="research-result-meta">
        <span className="source-type-label">
          {SOURCE_TYPE_LABELS[result.sourceType]}
        </span>
        <span className="prototype-label">Prototype</span>
      </div>
      <h3 className="research-result-title">{result.title}</h3>
      <p className="research-result-facts">
        {result.jurisdiction} · {result.date} · {result.citationLabel}
      </p>
      <p className="research-result-summary-label">Summary</p>
      <p className="research-result-summary">{result.summary}</p>
      <p className="research-result-topics-label">Topics</p>
      <ul className="research-result-topics">
        {result.topics.map((topic) => (
          <li key={topic}>{topic}</li>
        ))}
      </ul>
      <p className="research-result-relevance-label">Relevance</p>
      <p className="research-result-relevance">{result.relevanceReason}</p>
      <div className="research-result-action">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onSelect(result.id)}
        >
          {selected ? 'Selected — View Details' : 'View Details'}
        </button>
      </div>
    </article>
  )
}

export default ResearchResultCard
