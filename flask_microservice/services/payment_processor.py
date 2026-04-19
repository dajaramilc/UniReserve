from factories.payment_gateway_factory import PaymentGatewayFactory


class PaymentProcessorService:
    @staticmethod
    def process_payment(user_id: int, user_email: str, amount: float, resource_id: int, payment_provider: str) -> dict:
        gateway = PaymentGatewayFactory.create(payment_provider)
        result = gateway.charge(amount, user_email)
        return result