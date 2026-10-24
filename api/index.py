"""Punto de entrada para Vercel (runtime de Python): expone la aplicación WSGI de Django."""
from negocio.wsgi import application

app = application
