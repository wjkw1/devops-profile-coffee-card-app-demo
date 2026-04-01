interface ConfirmModalProps {
    message: string
    onConfirm: () => void
    onCancel: () => void
}

function ConfirmModal({ message, onConfirm, onCancel }: ConfirmModalProps) {
    return (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6 flex flex-col gap-4">
                <p className="text-sm text-gray-700">{message}</p>
                <div className="flex gap-2">
                    <button
                        onClick={onCancel}
                        className="flex-1 border rounded py-1.5 text-sm hover:bg-gray-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        className="flex-1 bg-red-500 text-white rounded py-1.5 text-sm hover:bg-red-600"
                    >
                        Confirm
                    </button>
                </div>
            </div>
        </div>
    )
}

export default ConfirmModal
