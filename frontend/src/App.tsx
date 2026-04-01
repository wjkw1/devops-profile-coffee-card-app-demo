import { useState, useEffect, useCallback } from 'react'
import CustomerList from './components/CustomerList'
import Sidebar from './components/Sidebar'
import type { Customer } from './types'
import { api } from './api'

function App() {
  const [query, setQuery] = useState("")
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(false)

  const fetchCustomers = useCallback(async (q: string, showLoading = true) => {
    if (!q.trim()) { setCustomers([]); return }
    if (showLoading) setLoading(true)
    try {
      const res = await api(`/api/customers?search=${encodeURIComponent(q)}`)
      const data = await res.json()
      setCustomers(data)
    } catch {
      setCustomers([])
    } finally {
      if (showLoading) setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timeout = setTimeout(() => fetchCustomers(query), 500)
    return () => clearTimeout(timeout)
  }, [query, fetchCustomers])

  return (
    <div className="flex h-screen bg-gray-50 items-center">
      <div className="w-1/3 h-full p-6">
        <Sidebar onSearchChange={setQuery} onCustomerRegistered={() => fetchCustomers(query, false)} />
      </div>
      <div className="w-2/3 h-full overflow-y-auto p-6">
        <CustomerList customers={customers} loading={loading} query={query} onUpdate={() => fetchCustomers(query, false)} />
      </div>
    </div>
  )
}

export default App
