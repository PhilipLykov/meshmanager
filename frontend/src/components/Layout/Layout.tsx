import Header from './Header'
import Sidebar from './Sidebar'
import MapContainer from '../Map/MapContainer'

export default function Layout() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Header />
        <MapContainer />
      </main>
    </div>
  )
}
