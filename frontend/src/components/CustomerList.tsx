import CustomerCard from "./CustomerCard"
import type { Customer } from "../types"

interface CustomerListProps {
    customers: Customer[]
    loading: boolean
    query: string
    onUpdate: () => void
}

function CustomerList({ customers, loading, query, onUpdate }: CustomerListProps) {
    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-16 px-8 text-center text-gray-500">
                <div className="text-[32px] opacity-40 mb-4">☕</div>
                <div className="text-sm font-medium mb-1">Searching...</div>
            </div>
        )
    }

    if (!query.trim()) {
        return (
            <div className="flex flex-col items-center justify-center py-16 px-8 text-center text-gray-500">
                <div className="text-[32px] opacity-40 mb-4">☕</div>
                <div className="text-sm font-medium mb-1">No customer selected</div>
                <div className="text-xs text-gray-400">Search or select a customer to view their cards</div>
            </div>
        )
    }

    if (customers.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-16 px-8 text-center text-gray-500">
                <div className="text-[32px] opacity-40 mb-4">☕</div>
                <div className="text-sm font-medium mb-1">No customers found</div>
                <div className="text-xs text-gray-400">Try a different name or register a new customer</div>
            </div>
        )
    }

    return (
        <div className="flex flex-col gap-4">
            {customers.map(customer => (
                <CustomerCard key={customer.id} {...customer} onUpdate={onUpdate} />
            ))}
        </div>
    )
}

export default CustomerList
