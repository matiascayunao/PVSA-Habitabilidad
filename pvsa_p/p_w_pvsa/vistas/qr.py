import hashlib
import uuid
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
from ..models import ReporteIncidencia
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

    token_texto = str(token or "").strip()[:256]

    token_huella = hashlib.sha256(
        token_texto.lower().encode("utf-8")
    ).hexdigest()

    try:
        token_uuid = uuid.UUID(token_texto)
    except (AttributeError, TypeError, ValueError):
        token_uuid = None

    lugar = None

    if token_uuid is not None:
        lugar = (
            Lugar.objects
            .filter(qr_token=token_uuid)
            .only(
                "id",
                "nombre_del_lugar",
                "qr_token",
                "qr_activo",
                "visibilidad_qr",
            )
            .first()
        )

    # --------------------------------------------------
    # REGISTRAR ACCESO
    # --------------------------------------------------

    if lugar is None:
        resultado = AccesoQR.Resultado.INVALIDO

    elif not lugar.qr_activo:
        resultado = AccesoQR.Resultado.DESACTIVADO

    else:
        resultado = AccesoQR.Resultado.PERMITIDO

    AccesoQR.objects.create(
        lugar=lugar,
        ip=request.META.get("REMOTE_ADDR") or None,
        user_agent=(
            request.META.get("HTTP_USER_AGENT") or ""
        )[:512],
        token_huella=token_huella,
        resultado=resultado,
    )

    if resultado != AccesoQR.Resultado.PERMITIDO:
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
        if es_jefe_departamento(request.user):
            if lugares_visibles_jefe(request.user).filter(pk=lugar.pk).exists():
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

                    reporte.lugar = lugar
                    reporte.origen = (
                        ReporteIncidencia.Origen.QR_PUBLICO
                    )
                    reporte.reportado_por = None

                    opcion = form.cleaned_data[
                        "elemento_opcion"
                    ]

                    if opcion == "otro":
                        reporte.elemento_reportado = (
                            form.cleaned_data[
                                "otro_elemento"
                            ].strip()
                        )
                    else:
                        reporte.elemento_reportado = opcion

                    # Validación y guardado.
                    reporte.full_clean()
                    reporte.save()

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
