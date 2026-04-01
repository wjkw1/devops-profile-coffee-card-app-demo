export interface Card {
    id: string
    customer_id: string
    total_credits: number
    credits_used: number
    is_archived: boolean
    created_at: string
}

export interface Customer {
    id: string
    name: string
    email: string | null
    is_archived: boolean
    cards: Card[]
}
