from django.contrib import admin

from airport.models import (
    Country,
    City,
    Airport,
    Airplane,
    AirplaneType,
    Crew,
    Route,
    Flight,
    Order,
    Ticket,
)


class TicketInLine(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = (TicketInLine,)


admin.site.register(Country)
admin.site.register(City)
admin.site.register(Airport)
admin.site.register(Airplane)
admin.site.register(AirplaneType)
admin.site.register(Crew)
admin.site.register(Route)
admin.site.register(Flight)
