from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from ..models import Sector
from ..models import Ubicacion


@login_required(login_url="signin")
@require_http_methods(["GET", "POST"])
def signup(request):
    """
    Solo los superusuarios pueden crear cuentas.

    Al crear un usuario nuevo, se conserva
    la sesión del administrador actual.
    """

    from django.core.exceptions import PermissionDenied

    if not request.user.is_superuser:
        raise PermissionDenied(
            "No tienes permisos para crear usuarios."
        )

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            nuevo_usuario = form.save()

            messages.success(
                request,
                f"El usuario '{nuevo_usuario.username}' "
                "fue creado correctamente."
            )

            return redirect("signup")

    else:
        form = UserCreationForm()

    return render(
        request,
        "signup.html",
        {
            "form": form,
        },
    )


@csrf_protect
def signin(request):
    from django.utils.http import url_has_allowed_host_and_scheme

    if request.method == "GET":
        return render(
            request,
            "signin.html",
            {"form": AuthenticationForm},
        )

    user = authenticate(
        request,
        username=request.POST.get("username", ""),
        password=request.POST.get("password", ""),
    )

    if user is None:
        return render(
            request,
            "signin.html",
            {
                "form": AuthenticationForm,
                "error": "Nombre o contraseña incorrectos",
            },
        )

    login(request, user)

    # Si el usuario llegó desde un QR privado,
    # devolverlo a ese QR después de iniciar sesión.
    destino_qr = request.session.pop(
        "pvsa_qr_volver_despues_login",
        None,
    )

    if destino_qr and url_has_allowed_host_and_scheme(
        destino_qr,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(destino_qr)

    destino = request.POST.get("next") or request.GET.get("next")
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(destino)

    return redirect("home")


@login_required
@require_POST
@csrf_protect
def signout(request):
    logout(request)
    return redirect("signin")


@login_required
def home(request):
    vista_actual = request.GET.get("vista", "sectores")
    sectores = Sector.objects.order_by("sector")
    ubicaciones = Ubicacion.objects.select_related("sector").order_by("sector__sector", "ubicacion")

    return render(
        request,
        "home.html",
        {
            "sectores": sectores,
            "ubicaciones": ubicaciones,
            "vista_actual": vista_actual,
        },
    )
