from django.contrib import admin

from.models import Cliente, Empleado, Mesa, Plato, Orden, DetalleOrden, Factura

admin.site.register(Cliente)
admin.site.register(Empleado)
admin.site.register(Mesa)
admin.site.register(Plato)
admin.site.register(Orden)
admin.site.register(DetalleOrden)
admin.site.register(Factura)

