import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import './pages.css'

function Profile() {
  return (
    <div className="page-container">
      <PageHeader
        title="Profile"
        description="Manage your account information."
      />
      <div className="placeholder-stack">
        <Card
          title="Account information"
          description="Profile management will be built in a later step."
        >
          <p>Your account details are shown here.</p>
        </Card>
      </div>
    </div>
  )
}

export default Profile
