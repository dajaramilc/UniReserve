from decimal import Decimal
import requests
from django.db import transaction
from django.db.models import Q

from apps.reservations.domain.builders import ReservationBuilder
from apps.reservations.domain.exceptions import (
    InvalidScheduleError,
    PaymentFailedError,
    ReservationAlreadyCancelledError,
    ReservationNotFoundError,
    ResourceNotFoundError,
    ResourceUnavailableError,
    UserNotEligibleError,
    UserNotFoundError,
)
from apps.reservations.models import (
    AccountStatus,
    Reservation,
    ReservationStatus,
    Resource,
    Schedule,
    User,
)


class ReservationPricingService:
    PREMIUM_RESOURCE_PRICE = Decimal("25000.00")

    @classmethod
    def calculate_cost(cls, resource: Resource) -> Decimal:
        if resource.is_premium:
            return cls.PREMIUM_RESOURCE_PRICE
        return Decimal("0.00")


class CreateReservationService:
    def __init__(self, payment_provider: str = "fake") -> None:
        self.payment_provider = payment_provider
        self.payment_service_url = "http://127.0.0.1:5000/api/v2/payments/process"

    @transaction.atomic
    def execute(
        self,
        *,
        user_id: int,
        resource_id: int,
        date,
        start_time,
        end_time,
    ) -> Reservation:
        user = self._get_user(user_id)
        resource = self._get_resource(resource_id)

        self._validate_user(user)
        self._validate_schedule(start_time, end_time)
        self._validate_resource_availability(resource, date, start_time, end_time)

        schedule = Schedule(date=date, start_time=start_time, end_time=end_time)
        schedule.full_clean()
        schedule.save()

        total_cost = ReservationPricingService.calculate_cost(resource)

        reservation = (
            ReservationBuilder()
            .with_user(user)
            .with_resource(resource)
            .with_schedule(schedule)
            .with_status(ReservationStatus.PENDING)
            .with_total_cost(total_cost)
            .build()
        )

        reservation.full_clean()
        reservation.save()

        if resource.is_premium:
            self._process_payment(reservation)

        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=["status"])

        return reservation

    def _get_user(self, user_id: int) -> User:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            raise UserNotFoundError("User not found.") from exc

    def _get_resource(self, resource_id: int) -> Resource:
        try:
            return Resource.objects.get(pk=resource_id)
        except Resource.DoesNotExist as exc:
            raise ResourceNotFoundError("Resource not found.") from exc

    def _validate_user(self, user: User) -> None:
        if user.account_status != AccountStatus.ACTIVE:
            raise UserNotEligibleError("User account is not active.")

    def _validate_schedule(self, start_time, end_time) -> None:
        if start_time >= end_time:
            raise InvalidScheduleError("End time must be greater than start time.")

    def _validate_resource_availability(
        self,
        resource: Resource,
        date,
        start_time,
        end_time,
    ) -> None:
        if not resource.is_active:
            raise ResourceUnavailableError("Resource is inactive.")

        overlap_exists = Reservation.objects.filter(
            resource=resource,
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
            schedule__date=date,
        ).filter(
            Q(schedule__start_time__lt=end_time) &
            Q(schedule__end_time__gt=start_time)
        ).exists()

        if overlap_exists:
            raise ResourceUnavailableError(
                "The resource is not available for the selected schedule."
            )

    def _process_payment(self, reservation: Reservation) -> None:
        """Llama al microservicio Flask para procesar el pago."""
        try:
            response = requests.post(
                self.payment_service_url,
                json={
                    "user_id": reservation.user.pk,
                    "user_email": reservation.user.email,
                    "amount": float(reservation.total_cost),
                    "resource_id": reservation.resource.pk,
                    "payment_provider": self.payment_provider,
                },
                timeout=5,
            )
            response.raise_for_status()
            payment_result = response.json()

            if not payment_result.get("success"):
                raise PaymentFailedError(payment_result.get("message", "Payment failed"))

        except requests.RequestException as exc:
            raise PaymentFailedError(f"Payment service unavailable: {str(exc)}")


class CancelReservationService:
    @transaction.atomic
    def execute(self, *, reservation_id: int) -> Reservation:
        try:
            reservation = Reservation.objects.select_related(
                "resource",
                "user",
                "schedule",
            ).get(pk=reservation_id)
        except Reservation.DoesNotExist as exc:
            raise ReservationNotFoundError("Reservation not found.") from exc

        if reservation.status == ReservationStatus.CANCELLED:
            raise ReservationAlreadyCancelledError(
                "Reservation is already cancelled."
            )

        reservation.status = ReservationStatus.CANCELLED
        reservation.save(update_fields=["status"])
        return reservation


class ListUserReservationHistoryService:
    def execute(self, *, user_id: int):
        if not User.objects.filter(pk=user_id).exists():
            raise UserNotFoundError("User not found.")

        return Reservation.objects.select_related(
            "user",
            "resource",
            "schedule",
        ).filter(user_id=user_id)