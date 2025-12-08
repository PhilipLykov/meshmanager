import { AuthProvider } from './contexts/AuthContext'
import { DataProvider } from './contexts/DataContext'
import Layout from './components/Layout/Layout'

function App() {
  return (
    <AuthProvider>
      <DataProvider>
        <Layout />
      </DataProvider>
    </AuthProvider>
  )
}

export default App
