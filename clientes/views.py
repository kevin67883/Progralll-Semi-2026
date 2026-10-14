from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def hola_mundo(request): 
    return HttpResponse("Hola Mundo Bienvenido a PrograIII")
     
    def saludoNombre(request,nombre, edad): 
    return HttpResponse("Hola"{nombre}, tu edad)

    def index(request):
    return render(request, 'index.html')