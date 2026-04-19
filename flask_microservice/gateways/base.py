from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: float, user_email: str) -> dict:
        raise NotImplementedError