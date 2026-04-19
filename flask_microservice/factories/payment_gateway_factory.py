from gateways.fake_gateway import FakePaymentGateway
from gateways.rejected_gateway import RejectedPaymentGateway


class PaymentGatewayFactory:
    @staticmethod
    def create(provider: str):
        normalized_provider = provider.lower()

        if normalized_provider == "fake":
            return FakePaymentGateway()

        if normalized_provider == "rejected":
            return RejectedPaymentGateway()

        raise ValueError(f"Unsupported payment provider: {provider}")