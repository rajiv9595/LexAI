import { Link } from 'react-router-dom'
import './CaseContext.css'

interface CaseContextProps {
  conversationId: string | null
  messageCount: number
  status: string
}

function CaseContext({ conversationId, messageCount, status }: CaseContextProps) {
  return (
    <div className="case-context">
      <h2 className="case-context-title">Session Context</h2>

      <div className="case-context-block">
        <p className="case-context-label">Conversation ID</p>
        <p className="case-context-value">
          {conversationId ? conversationId : 'New Session'}
        </p>
      </div>

      <div className="case-context-block">
        <p className="case-context-label">Status</p>
        <p className="case-context-value">{status}</p>
      </div>

      <div className="case-context-block">
        <p className="case-context-label">Messages In Thread</p>
        <p className="case-context-value">{messageCount}</p>
      </div>

      <div className="case-context-block">
        <p className="case-context-label">Related Workspaces</p>
        <ul className="case-context-list">
          <li>
            <Link to="/app/documents">Document Assistant</Link>
          </li>
          <li>
            <Link to="/app/history">Case Activity History</Link>
          </li>
          <li>
            <Link to="/app/research">Legal Research</Link>
          </li>
        </ul>
      </div>
    </div>
  )
}

export default CaseContext
