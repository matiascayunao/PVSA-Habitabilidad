from axes.handlers.database import AxesDatabaseHandler
from axes.helpers import set_retry_after_header
from django.contrib.auth.forms import AuthenticationForm
from django.http import QueryDict
from django.shortcuts import render


class IntentosLoginHandler(AxesDatabaseHandler):
    def user_login_failed(self, sender, credentials, request=None, **kwargs):
        if request is None:
            return
        original_get = request.__dict__.get("GET")
        original_post = request.POST
        request.GET, request.POST = QueryDict(), QueryDict()
        request.axes_user_agent = ""
        request.axes_http_accept = ""
        try:
            return super().user_login_failed(sender, credentials, request, **kwargs)
        finally:
            if original_get is None:
                request.__dict__.pop("GET", None)
            else:
                request.GET = original_get
            request.POST = original_post


def respuesta_bloqueo(request, response=None, credentials=None):
    response = render(request, "signin.html", {
        "form": AuthenticationForm(request),
        "error": "Acceso temporalmente restringido por intentos repetidos. Espera y vuelve a intentarlo.",
    }, status=429)
    response["Cache-Control"] = "no-store"
    set_retry_after_header(request, response)
    return response
