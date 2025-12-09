import { useState } from 'react'
import Header from './Header'
import NavSidebar, { type Page } from './NavSidebar'
import MapPage from '../Map/MapPage'
import { GraphsPage } from '../Graphs'
import { SettingsPage } from '../Settings'

export default function Layout() {
  const [currentPage, setCurrentPage] = useState<Page>('map')

  const renderPage = () => {
    switch (currentPage) {
      case 'map':
        return <MapPage />
      case 'graphs':
        return <GraphsPage />
      case 'settings':
        return <SettingsPage />
      default:
        return <MapPage />
    }
  }

  return (
    <div className="app-layout">
      <NavSidebar currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="main-content">
        <Header />
        <div className="page-content">
          {renderPage()}
        </div>
      </main>
    </div>
  )
}
