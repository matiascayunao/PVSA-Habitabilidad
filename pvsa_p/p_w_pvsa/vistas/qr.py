import hashlib
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from ..models import Lugar
from ..models import AccesoQR
from ..servicios.incidencias import guardar_reporte_publico
from ..servicios.qr import identificar_y_registrar_acceso_qr, marcar_acceso_permitido
from ..pvsa_permisos import es_jefe_departamento, lugares_visibles_jefe


@login_required
def qr_lugar(request, lugar_id):
    import qrcode
    from io import BytesIO

    lugar = get_object_or_404(Lugar, pk=lugar_id)

    # El QR enlaza a la consulta publica, no al detalle interno protegido.
    url = request.build_absolute_uri(
        reverse("consulta_qr", kwargs={"token": str(lugar.qr_token)})
    )

    img = qrcode.make(url)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    filename = f"QR_LUGAR_{lugar.id}.png"

    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


@require_http_methods(["GET", "POST"])
def consulta_qr(request, token):
    """
    Acceso mediante QR.

    Privado:
        Requiere iniciar sesión y tener autorización.

    Público:
        Permite enviar reportes sin cuenta.
        No muestra información interna del inventario.
    """

    from django.core.cache import cache
    from django.http import HttpResponseNotAllowed
    from django.utils import timezone
    from zoneinfo import ZoneInfo

    from ..formularios.reporte_forms import ReportePublicoForm

    # --------------------------------------------------
    # IDENTIFICAR QR
    # --------------------------------------------------

    lugar, acceso = identificar_y_registrar_acceso_qr(
        token,
        request.META.get("REMOTE_ADDR"),
        request.META.get("HTTP_USER_AGENT"),
    )

    if acceso.resultado in (AccesoQR.Resultado.INVALIDO, AccesoQR.Resultado.DESACTIVADO):
        return HttpResponse(
            "Este código QR no está disponible.",
            status=404,
            content_type="text/plain; charset=utf-8",
        )

    # --------------------------------------------------
    # QR PRIVADO
    # --------------------------------------------------

    if lugar.visibilidad_qr == "privado":

        if request.method != "GET":
            return HttpResponseNotAllowed(["GET"])

        if not request.user.is_authenticated:

            request.session[
                "pvsa_qr_volver_despues_login"
            ] = request.path

            return redirect("signin")

        # Use the same object scope as the jefe panel; QR visibility grants no
        # additional inventory permissions. Common areas remain read/report only.
        if not request.user.is_superuser:
            grupos = set(request.user.groups.values_list("name", flat=True))
            if "Jefe de departamento" in grupos and grupos.intersection({"Administrador", "Operador"}):
                return HttpResponse(
                    "No tienes permisos para consultar este lugar.",
                    status=403,
                    content_type="text/plain; charset=utf-8",
                )

        if es_jefe_departamento(request.user):
            if lugares_visibles_jefe(request.user).filter(pk=lugar.pk).exists():
                marcar_acceso_permitido(acceso)
                return redirect("detalle_lugar_jefe", lugar_id=lugar.pk)
            return HttpResponse(
                "No tienes permisos para consultar este lugar.",
                status=403,
                content_type="text/plain; charset=utf-8",
            )

        puede_acceder = (
            request.user.is_superuser
            or request.user.groups.filter(
                name="Administrador"
            ).exists()
        )

        if not puede_acceder:
            return HttpResponse(
                "No tienes permisos para consultar este lugar.",
                status=403,
                content_type="text/plain; charset=utf-8",
            )

        marcar_acceso_permitido(acceso)
        return redirect(
            "detalle_lugar",
            lugar_id=lugar.pk,
        )

    # --------------------------------------------------
    # VISIBILIDAD DESCONOCIDA
    # --------------------------------------------------

    if lugar.visibilidad_qr != "publico":
        return HttpResponse(
            "Este código QR no está disponible.",
            status=404,
            content_type="text/plain; charset=utf-8",
        )

    # --------------------------------------------------
    # QR PÚBLICO: PROCESAR REPORTE
    # --------------------------------------------------

    marcar_acceso_permitido(acceso)

    if request.method == "POST":

        form = ReportePublicoForm(
            request.POST,
            request.FILES,
        )

        # Campo trampa para envíos automáticos.
        if request.POST.get("sitio_web", "").strip():
            return HttpResponse(
                "Solicitud no válida.",
                status=400,
            )

        if form.is_valid():

            # Límite básico para evitar envíos repetidos.
            origen_ip = request.META.get(
                "REMOTE_ADDR", ""
            )

            llave = "pvsa_qr_reporte_" + hashlib.sha256(
                f"{lugar.pk}|{origen_ip}".encode("utf-8")
            ).hexdigest()

            if not cache.add(
                llave,
                "1",
                timeout=30,
            ):
                form.add_error(
                    None,
                    "Espera unos segundos antes de enviar "
                    "otro reporte.",
                )

            else:

                try:
                    reporte = form.save(commit=False)

                    guardar_reporte_publico(reporte, lugar, form.cleaned_data)

                except Exception:
                    cache.delete(llave)
                    raise

                # Mostrar la recepción en horario chileno.
                fecha_chile = timezone.localtime(
                    reporte.fecha_reporte,
                    ZoneInfo("America/Santiago"),
                ).strftime("%d/%m/%Y a las %H:%M:%S")

                messages.success(
                    request,
                    f"Reporte #{reporte.pk} recibido "
                    f"el {fecha_chile} (hora de Chile).",
                )

                return redirect(
                    "consulta_qr",
                    token=str(lugar.qr_token),
                )

    else:
        form = ReportePublicoForm()

    # --------------------------------------------------
    # MOSTRAR FORMULARIO PÚBLICO
    # --------------------------------------------------

    return render(
        request,
        "consulta_qr.html",
        {
            "nombre_lugar": lugar.nombre_del_lugar,
            "form": form,
        },
    )
