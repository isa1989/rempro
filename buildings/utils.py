import environ
import requests
from django.utils import timezone
from django.db import transaction
from django.shortcuts import render
from buildings.models import Service, Branch, Flat, Payment, Charge


def get_weather_data(city_id):
    env = environ.Env()
    environ.Env.read_env()
    ow_api_key = env("OPENWEATHER_API_KEY")

    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "id": city_id,
        "appid": ow_api_key,
        "units": "metric",  # For temperature in Celsius
        "lang": "az",  # Set language to Azerbaijani
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    return data


def process_payments(request):
    today = timezone.now().date()
    services = Service.objects.filter(invoice_day=today.day, is_active=True)
    for service in services:
        branch = service.branch
        flats = branch.flat_set.all()
        for flat in flats:
            balance = flat.balance
            if balance > 0:
                payment_amount = min(balance, service.price * flat.square_metres)
                flat.balance -= payment_amount
                flat.save()
                Payment.objects.create(
                    building=flat.building,
                    flat=flat,
                    amount=payment_amount,
                    service=service,
                    user=request.user,
                    date=today,
                )
                if payment_amount < service.price * flat.square_metres:
                    charge_amount = service.price * flat.square_metres - payment_amount
                    Charge.objects.create(
                        flat=flat,
                        service=service,
                        amount=charge_amount,
                    )
            else:
                Charge.objects.create(
                    flat=flat,
                    service=service,
                    amount=service.price * flat.square_metres,
                )
    return True
