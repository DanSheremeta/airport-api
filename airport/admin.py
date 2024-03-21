from django.contrib import admin

from .models import (
    Crew,
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Flight,
    Order,
    Ticket,
)

admin.site.register(Crew)
admin.site.register(Airport)
admin.site.register(Route)
admin.site.register(AirplaneType)
admin.site.register(Airplane)
admin.site.register(Flight)
admin.site.register(Order)
admin.site.register(Ticket)
