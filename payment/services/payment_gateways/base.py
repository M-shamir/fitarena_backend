from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    @abstractmethod
    def create_payment_intent(self, amount, currency, metadata=None):
        pass
    
    @abstractmethod
    def verify_payment(self, payment_id):
        pass
    
    @abstractmethod
    def refund_payment(self, payment_id, amount=None):
        pass