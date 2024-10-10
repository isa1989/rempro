from celery import shared_task
from django.utils import timezone
from .models import Service, Flat, Payment, Charge


@shared_task
def process_service_invoices():
    today = timezone.now().day
    services = Service.objects.filter(invoice_day=today, is_active=True)

    for service in services:
        for flat in service.flats.all():

            amount = service.price * flat.square_metres

            if flat.balance >= amount:
                flat.balance -= amount
                flat.save()
                Payment.objects.create(
                    building=flat.building,
                    flat=flat,
                    amount=amount,
                    charge=None,
                    user=flat.user,
                    date=timezone.now().date(),
                )
            else:
                charge_amount = amount - flat.balance
                Charge.objects.create(
                    flat=flat, service=service, amount=charge_amount, is_paid=False
                )
                if flat.balance != 0:
                    Payment.objects.create(
                        building=flat.building,
                        flat=flat,
                        amount=flat.balance,
                        charge=None,
                        user=flat.resident,
                        date=timezone.now().date(),
                    )

                flat.balance = 0
                flat.save()

    return "Process completed"
