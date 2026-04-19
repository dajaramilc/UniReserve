from .base import PaymentGateway


class FakePaymentGateway(PaymentGateway):
    def charge(self, amount: float, user_email: str) -> dict:
        return {
            "success": True,
            "transaction_id": "TXN-FAKE-001",
            "amount": amount,
            "user_email": user_email,
            "message": "Payment approved.",
        }