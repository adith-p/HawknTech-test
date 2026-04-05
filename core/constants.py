class StockTransferStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    choices = ["PENDING", "APPROVED", "REJECTED"]


stock_transfer_status = [
    (StockTransferStatus.PENDING, "pending"),
    (StockTransferStatus.APPROVED, "approved"),
    (StockTransferStatus.REJECTED, "rejected"),
]


class TransferType:
    REQUEST = "REQUEST"
    OFFER = "OFFER"

    choices = ["REQUEST", "OFFER"]


transfer_type_choice = [
    (TransferType.REQUEST, "request"),
    (TransferType.OFFER, "offer"),
]
