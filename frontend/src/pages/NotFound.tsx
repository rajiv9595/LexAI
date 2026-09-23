import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import './pages.css'

function NotFound() {
  return (
    <div className="page-container">
      <PageHeader
        title="Page not found"
        description="The page you requested does not exist."
        action={
          <Link className="btn btn-primary" to="/app/dashboard">
            Back to dashboard
          </Link>
        }
      />
      <Card title="404" description="Check the address and try again.">
        <p>The requested page could not be found.</p>
      </Card>
    </div>
  )
}

export default NotFound
