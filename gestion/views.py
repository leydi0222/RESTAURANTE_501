from django.shortcuts import render

# Create your views here.
from.models import Cliente,Empleado,Mesa,Orden,Factura, Plato

def inicio(request):
    context={'total_clientes':Cliente.objects.count(),#cuenta objetos de la tabla cliente
            'total_Empleado':Empleado.objects.count(),
            'total_Mesa':Mesa.objects.count(),
            'total_Orden':Orden.objects.count(),
            'total_Factura':Factura.objects.count(),
    }
    
    return render (request,'gestion/inicio.html',context)#pasa la ruta de gestion 

def lista_clientes(request):
    clientes= Cliente.objects.all()
    return render(request,'gestion/clientes.html', {'clientes': clientes})

def lista_empleados(request):
    empleados= Empleado.objects.all()
    return render(request,'gestion/empleados.html', {'empleados': empleados})

def lista_mesas(request):
    mesas= Mesa.objects.all()
    return render(request,'gestion/mesas.html', {'mesas': mesas})

def lista_ordenes(request):
    ordenes= Orden.objects.all()
    return render(request,'gestion/ordenes.html', {'ordenes': ordenes})

def lista_facturas(request):
    facturas= Factura.objects.all()
    return render(request,'gestion/facturas.html', {'facturas': facturas})

def lista_platos(request):
    platos= Plato.objects.all()
    return render(request,'gestion/platos.html', {'platos': platos})

