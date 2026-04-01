import { api } from '../api'
import ConfirmModal from './ConfirmModal'
import { useState } from 'react'

interface CardTileProps {
  card_id: string
  customer_id: string
  total_credits: number
  credits_used: number
  is_archived: boolean
  created_at: string
  onUpdate: () => void
}

function CardTile({
  card_id,
  customer_id,
  total_credits,
  credits_used,
  is_archived,
  created_at,
  onUpdate,
}: CardTileProps) {
  const isFullyRedeemed = credits_used >= total_credits
  const hasNoCreditsUsed = credits_used <= 0
  const [showConfirm, setShowConfirm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async (action: () => Promise<void>) => {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await action()
      onUpdate()
    } catch {
      setError('Action failed. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  const archive = () => run(() =>
    api(`/api/customers/${customer_id}/cards/${card_id}`, { method: 'DELETE' }).then(() => {})
  )

  const restore = () => run(() =>
    api(`/api/customers/${customer_id}/cards/${card_id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_archived: false }),
    }).then(() => {})
  )

  const redeem = () => run(() =>
    api(`/api/customers/${customer_id}/cards/${card_id}/redeem`, { method: 'POST' }).then(() => {})
  )

  const refund = () => run(() =>
    api(`/api/customers/${customer_id}/cards/${card_id}/refund`, { method: 'POST' }).then(() => {})
  )

  const formattedDate = new Date(created_at).toLocaleDateString('en-AU', {
    day: 'numeric', month: 'short', year: 'numeric',
  })

  if (is_archived) {
    return (
      <div className="border rounded p-3 flex flex-col gap-2 bg-gray-50 opacity-60">
        <div className="flex flex-wrap gap-1">
          {Array.from({ length: total_credits }).map((_, i) => (
            <span key={i} className={`w-4 h-4 rounded-full border ${i < credits_used ? 'bg-gray-400 border-gray-400' : 'bg-white border-gray-300'}`} />
          ))}
        </div>
        <p className="text-xs text-gray-400">{credits_used}/{total_credits} used</p>
        <button
          onClick={restore}
          className="text-xs py-1 px-2 border rounded hover:bg-white transition-colors text-gray-500"
        >
          Restore
        </button>
        {error && <p className="text-[10px] text-red-500">{error}</p>}
        <p className="text-[10px] italic text-gray-400">{formattedDate}</p>
      </div>
    )
  }

  return (
    <div className={`border rounded p-3 flex flex-col gap-2 ${isFullyRedeemed ? 'bg-green-50' : 'bg-white'}`}>
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-1">
          {Array.from({ length: total_credits }).map((_, i) => (
            <span key={i} className={`w-4 h-4 rounded-full border ${i < credits_used ? 'bg-[#3C3489] border-[#3C3489]' : 'bg-white border-gray-300'}`} />
          ))}
        </div>
        <button
          onClick={() => setShowConfirm(true)}
          className="text-gray-400 hover:text-red-500 transition-colors ml-2 shrink-0"
          title="Archive card"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            <path d="M10 11v6" />
            <path d="M14 11v6" />
            <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
          </svg>
        </button>
      </div>
      <p className="text-xs text-gray-500">{credits_used}/{total_credits} used</p>
      <div className="flex gap-2 mt-1">
        <button
          onClick={redeem}
          disabled={isFullyRedeemed}
          className="flex-1 text-xs py-1 px-2 border rounded disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          Redeem
        </button>
        <button
          onClick={refund}
          disabled={hasNoCreditsUsed}
          className="flex-1 text-xs py-1 px-2 border rounded disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
        >
          Refund
        </button>
      </div>
      {error && <p className="text-[10px] text-red-500">{error}</p>}
      <p className="text-[10px] italic text-gray-400">{formattedDate}</p>
      {showConfirm && (
        <ConfirmModal
          message="Archive this card? It will no longer appear in search results."
          onConfirm={archive}
          onCancel={() => setShowConfirm(false)}
        />
      )}
    </div>
  )
}

export default CardTile
