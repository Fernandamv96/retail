"""Integración con Webpay Plus (Transbank).

En el ambiente de integración se usan las credenciales públicas de prueba de Transbank,
así que no se necesita cuenta. Para cobrar de verdad se definen WEBPAY_AMBIENTE=produccion,
WEBPAY_CODIGO_COMERCIO y WEBPAY_API_KEY con los datos que entrega Transbank.
"""
from django.conf import settings
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction


def _transaccion():
    if settings.WEBPAY_AMBIENTE == 'produccion':
        opciones = WebpayOptions(settings.WEBPAY_CODIGO_COMERCIO, settings.WEBPAY_API_KEY, IntegrationType.LIVE, timeout=30)
    else:
        opciones = WebpayOptions(IntegrationCommerceCodes.WEBPAY_PLUS, IntegrationApiKeys.WEBPAY, IntegrationType.TEST, timeout=30)
    return Transaction(opciones)


def iniciar_pago(orden, url_retorno):
    """Crea la transacción en Webpay. Devuelve la URL de pago y el token."""
    respuesta = _transaccion().create(orden.orden_compra, f'sesion-{orden.id}', orden.monto, url_retorno)
    return respuesta['url'], respuesta['token']


def confirmar_pago(token):
    """Confirma la transacción cuando el cliente vuelve de Webpay."""
    return _transaccion().commit(token)
