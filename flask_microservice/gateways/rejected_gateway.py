from .base import PaymentGateway


class RejectedPaymentGateway(PaymentGateway):
    def charge(self, amount: float, user_email: str) -> dict:
        return {
            "success": False,
            "transaction_id": None,
            "amount": amount,
            "user_email": user_email,
            "message": "Payment rejected by provider.",
        }