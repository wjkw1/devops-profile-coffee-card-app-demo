import { useState } from 'react'
import { api } from '../api'
import CardTile from './CardTile'
import ConfirmModal from './ConfirmModal'
import type { Customer, Card } from '../types'

interface CustomerCardProps extends Customer {
  onUpdate: () => void
}

function CustomerCard({ id, name, cards, onUpdate }: CustomerCardProps) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [showArchived, setShowArchived] = useState(false)
  const [allCards, setAllCards] = useState<Card[] | null>(null)

  const creditsRemaining = cards.reduce(
    (sum, c) => sum + (c.total_credits - c.credits_used),
    0
  )
  const displayCards = showArchived && allCards ? allCards : cards

  const toggleArchived = async () => {
    if (!showArchived && allCards === null) {
      const res = await api(`/api/customers/${id}/cards?include=archived`)
      const data = await res.json()
      setAllCards(data)
    }
    setShowArchived((prev) => !prev)
  }

  const archive = async () => {
    await api(`/api/customers/${id}`, { method: 'DELETE' })
    setShowConfirm(false)
    onUpdate()
  }

  const handleCardUpdate = () => {
    setAllCards(null)
    setShowArchived(false)
    onUpdate()
  }

  const addCard = async () => {
    await api(`/api/customers/${id}/cards`, { method: 'POST' })
    handleCardUpdate()
  }

  return (
    <div className="customer-panel border p-3">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-semibold">{name}</h2>
        <div className="flex items-center gap-3">
          <button
            onClick={toggleArchived}
            className={`text-xs transition-colors ${showArchived ? 'text-[#3C3489]' : 'text-gray-400 hover:text-gray-600'}`}
          >
            {showArchived ? 'Hide archived' : 'Show archived'}
          </button>
          <button
            onClick={() => setShowConfirm(true)}
            className="text-gray-400 hover:text-red-500 transition-colors"
            title="Archive customer"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
              <path d="M10 11v6" />
              <path d="M14 11v6" />
              <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
            </svg>
          </button>
        </div>
      </div>
      <div className="stats flex gap-3 mb-3">
        <div className="stat border p-2">
          Credits Remaining: {creditsRemaining}
        </div>
        <div className="stat border p-2">Total Cards: {cards.length}</div>
      </div>
      <div className="card-grid grid grid-cols-3 gap-3">
        {displayCards.map((card) => (
          <CardTile
            key={card.id}
            card_id={card.id}
            customer_id={id}
            total_credits={card.total_credits}
            credits_used={card.credits_used}
            is_archived={card.is_archived}
            created_at={card.created_at}
            onUpdate={handleCardUpdate}
          />
        ))}
        <button
          onClick={addCard}
          className="border rounded p-3 flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-[#3C3489] hover:border-[#3C3489] transition-colors"
          title="Add new card"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span className="text-xs">New card</span>
        </button>
      </div>
      {showConfirm && (
        <ConfirmModal
          message={`Archive ${name}? They will no longer appear in search results.`}
          onConfirm={archive}
          onCancel={() => setShowConfirm(false)}
        />
      )}
    </div>
  )
}

export default CustomerCard
