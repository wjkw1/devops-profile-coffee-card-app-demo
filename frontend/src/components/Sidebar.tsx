// Sidebar — search bar filters customers live, "Register customer" opens a modal form, health indicator at the bottom polls /health every 30 seconds and shows API version + status.

import { useState, useEffect } from 'react'
import { api } from '../api'
import RegisterCustomerModal from './RegisterCustomerModal'

interface HealthStatus {
  version: string
  uptime_seconds: number
  database: "ok" | "error"
}

interface SidebarProps {
  onSearchChange: (query: string) => void
  onCustomerRegistered: () => void
}

function Sidebar({ onSearchChange, onCustomerRegistered }: SidebarProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await api('/api/health')
        const data = await res.json()
        setHealth(data)
      } catch {
        setHealth(null)
      }
    }

    fetchHealth()
    const interval = setInterval(fetchHealth, 30_000)
    return () => clearInterval(interval)
  }, [])
  return (
    <div className="sidebar border p-3">
      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-8 h-8 bg-[#3C3489] rounded-lg flex items-center justify-center shrink-0">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#EEEDFE" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8h1a4 4 0 0 1 0 8h-1"/>
            <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/>
            <line x1="6" y1="1" x2="6" y2="4"/>
            <line x1="10" y1="1" x2="10" y2="4"/>
            <line x1="14" y1="1" x2="14" y2="4"/>
          </svg>
        </div>
        <div>
          <div className="text-[15px] font-medium text-gray-900">Coffee Card</div>
          <div className="text-[11px] text-gray-500 mt-px">Salesperson dashboard</div>
        </div>
      </div>
      <input
        type="text"
        placeholder="Search customers..."
        className="border p-1 mb-3 w-full"
        onChange={e => onSearchChange(e.target.value)}
      />
      <button onClick={() => setShowModal(true)} className="border py-2 px-3 w-full mb-3">
        Register Customer
      </button>
      {showModal && (
        <RegisterCustomerModal
          onClose={() => setShowModal(false)}
          onRegistered={() => { setShowModal(false); onCustomerRegistered() }}
        />
      )}
      <div className="flex items-center gap-2 mt-auto pt-3">
        <span className={`w-2 h-2 rounded-full shrink-0 ${health ? 'bg-[#3B6D11]' : 'bg-[#A32D2D]'}`} />
        <span className="text-xs text-gray-500">
          {health ? `API v${health.version} · online` : 'API offline'}
        </span>
      </div>
    </div>
  )
}
export default Sidebar
