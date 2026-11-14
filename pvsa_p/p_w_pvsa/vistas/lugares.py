from ..servicios.estructura import guardar_sin_duplicados
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from ..forms import CrearLugar
from ..forms import EditarLugar
from ..models import Ubicacion
from ..models import Piso
from ..models import Lugar
from ..models import ObjetoLugar
from .eliminacion import _confirm_delete


@login_required
def lista_lugares(request):
    ubicacion_id = request.GET.get("ubicacion", "").strip()
    piso_id = request.GET.get("piso", "").strip()
    lugares_qs = Lugar.objects.select_related(
        "piso",
        "piso__ubicacion",
        "piso__ubicacion__sector",
    ).all()

    if ubicacion_id:
        try:
            u_id = int(ubicacion_id)
            lugares_qs = lugares_qs.filter(piso__ubicacion_id=u_id)
        except ValueError:
            ubicacion_id = ""

    if piso_id:
        try:
            p_id = int(piso_id)
            lugares_qs = lugares_qs.filter(piso_id=p_id)
        except ValueError:
            piso_id = ""

    lugares = lugares_qs.order_by(
        "piso__ubicacion__ubicacion",
        "piso__piso",
        "nombre_del_lugar",
    )
    ubicaciones = Ubicacion.objects.select_related("sector").all().order_by("ubicacion")
    pisos = Piso.objects.select_related("ubicacion").all().order_by(
        "ubicacion__ubicacion",
        "piso",
    )

    return render(
        request,
        "lugar/lugares.html",
        {
            "lugares": lugares,
            "ubicaciones": ubicaciones,
            "pisos": pisos,
            "ubicacion_actual": ubicacion_id,
            "piso_actual": piso_id,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def detalle_lugar(request, lugar_id):
    from django.core.exceptions import PermissionDenied

    lugar = get_object_or_404(Lugar, pk=lugar_id)

    # --------------------------------------------------
    # CONFIGURACIÓN DEL QR
    # --------------------------------------------------

    if request.method == "POST":

        # Esta página solo procesa el formulario de QR.
        if request.POST.get("accion") != "configurar_qr":
            return HttpResponse(
                "Acción no válida.",
                status=400,
            )

        # Solo Superadmin y Mini-Admin.
        puede_configurar_qr = (
            request.user.is_superuser
            or request.user.groups.filter(
                name="Administrador"
            ).exists()
        )

        if not puede_configurar_qr:
            raise PermissionDenied(
                "No tienes permisos para configurar este QR."
            )

        # Validar los valores recibidos.
        visibilidad = request.POST.get(
            "visibilidad_qr", ""
        )

        if visibilidad not in ("publico", "privado"):
            return HttpResponse(
                "Visibilidad QR no válida.",
                status=400,
            )

        qr_activo_valor = request.POST.get("qr_activo")

        if qr_activo_valor not in (None, "1"):
            return HttpResponse(
                "Estado QR no válido.",
                status=400,
            )

        # Guardar únicamente la configuración del QR.
        lugar.qr_activo = qr_activo_valor == "1"
        lugar.visibilidad_qr = visibilidad

        lugar.save(
            update_fields=[
                "qr_activo",
                "visibilidad_qr",
            ]
        )

        messages.success(
            request,
            "La configuración del QR se guardó correctamente."
        )

        return redirect(
            "detalle_lugar",
            lugar_id=lugar.id,
        )

    # --------------------------------------------------
    # DETALLE NORMAL DEL LUGAR
    # --------------------------------------------------

    objetos = (
        ObjetoLugar.objects.select_related(
            "tipo_de_objeto",
            "tipo_de_objeto__objeto",
        )
        .filter(lugar=lugar)
        .order_by("-fecha")
    )

    return render(
        request,
        "lugar/detalle_lugar.html",
        {
            "lugar": lugar,
            "objetos": objetos,
        },
    )


@login_required
def crear_lugar(request):
    initial = {}
    piso_preseleccionado = None

    piso_id = request.GET.get("piso", "").strip()

    if piso_id:
        try:
            piso_preseleccionado = (
                Piso.objects
                .select_related(
                    "ubicacion",
                    "ubicacion__sector",
                )
                .get(pk=int(piso_id))
            )
            initial["piso"] = piso_preseleccionado
        except (ValueError, Piso.DoesNotExist):
            piso_preseleccionado = None

    form = CrearLugar(
        request.POST or None,
        initial=initial if request.method == "GET" else None,
    )

    lugares_existentes = list(
        Lugar.objects
        .select_related(
            "piso",
            "piso__ubicacion",
            "piso__ubicacion__sector",
            "lugar_tipo_lugar",
        )
        .order_by(
            "piso__ubicacion__sector__sector",
            "piso__ubicacion__ubicacion",
            "piso__piso",
            "nombre_del_lugar",
        )
        .values(
            "nombre_del_lugar",
            "piso_id",
            "piso__piso",
            "piso__ubicacion__ubicacion",
            "piso__ubicacion__sector__sector",
            "lugar_tipo_lugar__tipo_de_lugar",
        )
    )

    contexto = {
        "form": form,
        "piso_preseleccionado": piso_preseleccionado,
        "lugares_existentes": lugares_existentes,
    }

    if request.method == "POST" and form.is_valid():
        lugar = guardar_sin_duplicados(form)
        if lugar is not None:
            return redirect(
                "detalle_lugar",
                lugar_id=lugar.id,
            )

    return render(
        request,
        "lugar/crear_lugar.html",
        contexto,
    )


@login_required
def editar_lugar(request, lugar_id):
    lugar = get_object_or_404(Lugar, pk=lugar_id)

    cancel_url = reverse(
        "detalle_lugar",
        kwargs={"lugar_id": lugar.id},
    )

    # Solo Superadmin y Mini-Admin pueden clasificar
    # lugares y cambiar indirectamente sus QR.
    puede_clasificar = (
        request.user.is_superuser
        or request.user.groups.filter(
            name="Administrador"
        ).exists()
    )

    if request.method == "POST":
        form = EditarLugar(request.POST, instance=lugar)
    else:
        form = EditarLugar(instance=lugar)

    # Los demás usuarios no pueden modificar
    # la clasificación, ni siquiera enviando
    # el campo manualmente desde el navegador.
    if not puede_clasificar:
        form.fields.pop("es_area_comun", None)

    if request.method == "POST" and form.is_valid():

        lugar_actualizado = form.save(commit=False)

        if guardar_sin_duplicados(form, lugar_actualizado.save) is not None:
            return redirect(
                "detalle_lugar",
                lugar_id=lugar_actualizado.id,
            )

    return render(
        request,
        "editar_generico.html",
        {
            "titulo": "Editar lugar",
            "form": form,
            "cancel_url": cancel_url,
        },
    )


@login_required
def borrar_lugar(request, lugar_id):
    lugar = get_object_or_404(Lugar, pk=lugar_id)
    return _confirm_delete(
        request, lugar, "detalle_lugar", {"lugar_id": lugar.id}, "lista_lugares"
    )
