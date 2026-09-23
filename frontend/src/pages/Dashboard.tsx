import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import DisclaimerBanner from '../components/DisclaimerBanner'
import './Dashboard.css'

const DEMO_USER_FIRST_NAME = 'Rajeev'

interface QuickAction {
  to: string
  title: string
  description: string
  actionLabel: string
  icon: ReactNode
}

interface WorkspaceStat {
  label: string
  value: string
}

interface ActivityItem {
  title: string
  type: string
  date: string
  to: string
}

function FeatureIcon({ children }: { children: ReactNode }) {
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

const quickActions: QuickAction[] = [
  {
    to: '/app/assistant',
    title: 'Legal Assistant',
    description:
      'Ask questions and receive structured AI-assisted legal information.',
    actionLabel: 'Start a conversation',
    icon: (
      <FeatureIcon>
        <path d="M2 3.5h14v8H9.5L6 14.5v-3H2v-8z" />
        <path d="M5.5 7h7M5.5 9.5h4.5" />
      </FeatureIcon>
    ),
  },
  {
    to: '/app/documents',
    title: 'Document Assistant',
    description:
      'Create structured drafts from guided legal document templates.',
    actionLabel: 'Create a document',
    icon: (
      <FeatureIcon>
        <path d="M4.5 1.5h6L14 5v11.5h-9.5v-15z" />
        <path d="M10.5 1.5V5H14" />
        <path d="M7 9h4M7 11.5h4" />
      </FeatureIcon>
    ),
  },
  {
    to: '/app/research',
    title: 'Legal Research',
    description:
      'Explore legal topics, references, statutes and case-related information.',
    actionLabel: 'Explore research',
    icon: (
      <FeatureIcon>
        <circle cx="8" cy="8" r="5" />
        <path d="M12 12l4 4" />
      </FeatureIcon>
    ),
  },
  {
    to: '/app/history',
    title: 'Case History',
    description:
      'Review your previous legal assistance sessions and saved work.',
    actionLabel: 'View history',
    icon: (
      <FeatureIcon>
        <circle cx="9" cy="9" r="7" />
        <path d="M9 5v4l3 2" />
      </FeatureIcon>
    ),
  },
]

const workspaceStats: WorkspaceStat[] = [
  { label: 'Legal Sessions', value: '12' },
  { label: 'Documents', value: '5' },
  { label: 'Research Topics', value: '8' },
]

const recentActivity: ActivityItem[] = [
  {
    title: 'Employment Agreement Review',
    type: 'Legal Assistant',
    date: 'Today',
    to: '/app/assistant',
  },
  {
    title: 'Rental Agreement Draft',
    type: 'Document Assistant',
    date: 'Yesterday',
    to: '/app/documents',
  },
  {
    title: 'Property Law Research',
    type: 'Legal Research',
    date: 'Sep 20',
    to: '/app/research',
  },
  {
    title: 'Consumer Rights Question',
    type: 'Legal Assistant',
    date: 'Sep 18',
    to: '/app/assistant',
  },
]

const gettingStartedSteps: string[] = [
  'Describe your legal question',
  'Review structured AI assistance',
  'Explore relevant documents and references',
]

function Dashboard() {
  return (
    <div className="page-container">
      <div className="dashboard">
        <PageHeader
          title={`Welcome back, ${DEMO_USER_FIRST_NAME}`}
          description="Access your legal assistance workspace from one place."
        />

        <section className="dashboard-section" aria-label="Quick actions">
          <ul className="quick-action-grid">
            {quickActions.map((action) => (
              <li key={action.to} className="quick-action-card">
                <span className="quick-action-icon">{action.icon}</span>
                <h2 className="quick-action-title">{action.title}</h2>
                <p className="quick-action-description">{action.description}</p>
                <Link className="quick-action-link" to={action.to}>
                  {action.actionLabel}
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="dashboard-section" aria-label="Workspace overview">
          <h2 className="dashboard-section-title">Workspace overview</h2>
          <p className="dashboard-section-subtitle">
            A summary of your workspace activity in this prototype.
          </p>
          <ul className="stats-grid">
            {workspaceStats.map((stat) => (
              <li key={stat.label} className="stat-card">
                <p className="stat-value">{stat.value}</p>
                <p className="stat-label">{stat.label}</p>
              </li>
            ))}
          </ul>
        </section>

        <section className="dashboard-section" aria-label="Recent activity">
          <h2 className="dashboard-section-title">Recent activity</h2>
          <p className="dashboard-section-subtitle">
            Your latest sessions across assistance, documents and research.
          </p>
          <div className="activity-panel">
            <ul className="activity-list">
              {recentActivity.map((item) => (
                <li key={item.title} className="activity-row">
                  <div className="activity-main">
                    <p className="activity-title">{item.title}</p>
                    <p className="activity-meta">{item.type}</p>
                  </div>
                  <span className="activity-date">{item.date}</span>
                  <Link className="activity-open" to={item.to}>
                    Open
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="dashboard-section" aria-label="Getting started">
          <h2 className="dashboard-section-title">Getting started</h2>
          <p className="dashboard-section-subtitle">
            How to work with LexAssist.
          </p>
          <ol className="steps-list">
            {gettingStartedSteps.map((step, index) => (
              <li key={step} className="step-card">
                <span className="step-number" aria-hidden="true">
                  {index + 1}
                </span>
                <p className="step-title">{step}</p>
              </li>
            ))}
          </ol>
        </section>

        <DisclaimerBanner />
      </div>
    </div>
  )
}

export default Dashboard
