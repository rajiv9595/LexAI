import type { ResearchSummary as ResearchSummaryData } from '../types/research'
import './ResearchSummary.css'

interface ResearchSummaryProps {
  summary: ResearchSummaryData
  onRelatedTopicClick: (topic: string) => void
}

function ResearchSummary({ summary, onRelatedTopicClick }: ResearchSummaryProps) {
  return (
    <section className="research-summary" aria-label="Research summary">
      <h2 className="research-summary-title">Research Summary</h2>
      <p className="research-summary-topic">
        <strong>Research topic: </strong>
        {summary.query}
      </p>
      <p className="research-result-summary-label">Issue identified</p>
      <p className="research-result-summary">{summary.issue}</p>
      <p className="research-result-summary-label">Key points</p>
      <ul className="research-summary-list">
        {summary.keyPoints.map((point) => (
          <li key={point}>{point}</li>
        ))}
      </ul>
      <p className="research-result-summary-label">Considerations</p>
      <ul className="research-summary-list">
        {summary.considerations.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <p className="research-result-summary-label">Related topics</p>
      <ul className="related-topics-list">
        {summary.relatedTopics.map((topic) => (
          <li key={topic}>
            <button
              type="button"
              className="related-topic-button"
              onClick={() => onRelatedTopicClick(topic)}
            >
              {topic}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default ResearchSummary
