import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import './pages.css'

function Settings() {
  return (
    <div className="page-container">
      <PageHeader
        title="Settings"
        description="Manage application preferences and privacy settings."
      />
      <div className="placeholder-stack">
        <Card
          title="Preferences"
          description="Settings controls will be built in a later step."
        >
          <p>Adjust your application preferences here.</p>
        </Card>
      </div>
    </div>
  )
}

export default Settings
