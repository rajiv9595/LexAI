import { Link } from 'react-router-dom'
import type { HistoryItem } from '../types/history'
import './HistoryList.css'

const TYPE_LABELS: Record<HistoryItem['type'], string> = {
  assistant: 'Legal Assistant',
  document: 'Document',
  research: 'Research',
}

const STATUS_LABELS: Record<HistoryItem['status'], string> = {
  prototype: 'Prototype',
  draft: 'Draft',
  completed: 'Completed',
}

interface HistoryListProps {
  items: HistoryItem[]
}

function HistoryList({ items }: HistoryListProps) {
  return (
    <ul className="history-list">
      {items.map((item) => (
        <li key={item.id} className="history-item">
          <div className="history-item-top">
            <span className="history-item-type">{TYPE_LABELS[item.type]}</span>
            <span className="history-item-status">
              Status: {STATUS_LABELS[item.status]}
            </span>
          </div>
          <h3 className="history-item-title">{item.title}</h3>
          <p className="history-item-description">{item.description}</p>
          <p className="history-item-facts">
            <span>
              <strong>Category: </strong>
              {item.category}
            </span>
            <span>
              <strong>Date: </strong>
              {item.updatedAt}
            </span>
          </p>
          <Link
            className="btn btn-secondary"
            to={item.relatedRoute}
            aria-label={`Open ${item.title}`}
          >
            Open
          </Link>
        </li>
      ))}
    </ul>
  )
}

export default HistoryList
