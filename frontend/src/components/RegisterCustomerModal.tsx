import { useState } from 'react'
import { api } from '../api'

interface RegisterCustomerModalProps {
    onClose: () => void
    onRegistered: () => void
}

function RegisterCustomerModal({ onClose, onRegistered }: RegisterCustomerModalProps) {
    const [name, setName] = useState('')
    const [email, setEmail] = useState('')
    const [error, setError] = useState<string | null>(null)
    const [submitting, setSubmitting] = useState(false)

    const submit = async () => {
        if (!name.trim()) { setError('Name is required.'); return }
        setSubmitting(true)
        setError(null)
        try {
            const res = await api('/api/customers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.trim(), email: email.trim() || null }),
            })
            if (!res.ok) {
                const data = await res.json()
                setError(data.detail ?? 'Failed to register customer.')
                return
            }
            onRegistered()
            onClose()
        } catch {
            setError('Could not reach the API.')
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6 flex flex-col gap-4">
                <h2 className="text-base font-semibold text-gray-900">Register Customer</h2>

                <div className="flex flex-col gap-1">
                    <label className="text-xs text-gray-600">Name <span className="text-red-500">*</span></label>
                    <input
                        type="text"
                        value={name}
                        onChange={e => setName(e.target.value)}
                        placeholder="Jane Smith"
                        className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[#3C3489]"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label className="text-xs text-gray-600">Email <span className="text-gray-400">(optional)</span></label>
                    <input
                        type="email"
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                        placeholder="jane@example.com"
                        className="border rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[#3C3489]"
                    />
                </div>

                {error && <p className="text-xs text-red-500">{error}</p>}

                <div className="flex gap-2 mt-1">
                    <button
                        onClick={onClose}
                        className="flex-1 border rounded py-1.5 text-sm hover:bg-gray-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={submit}
                        disabled={submitting}
                        className="flex-1 bg-[#3C3489] text-white rounded py-1.5 text-sm disabled:opacity-50 hover:opacity-90"
                    >
                        {submitting ? 'Registering...' : 'Register'}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default RegisterCustomerModal
