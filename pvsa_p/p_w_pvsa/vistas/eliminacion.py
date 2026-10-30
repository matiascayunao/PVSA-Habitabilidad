from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
try:
    from django.db.models.deletion import ProtectedError, RestrictedError
except Exception:
    from django.db.models.deletion import ProtectedError
    RestrictedError = ProtectedError


def _confirm_delete(request, obj, cancel_url_name, cancel_kwargs, success_url_name):
    cancel_url = reverse(cancel_url_name, kwargs=cancel_kwargs)

    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, "Registro eliminado correctamente.")
            return redirect(success_url_name)

        except (ProtectedError, RestrictedError) as e:
            related_preview = []
            related_qs = getattr(e, "protected_objects", None) or getattr(e, "restricted_objects", None)

            try:
                if related_qs is not None:
                    related_preview = [str(x) for x in list(related_qs[:8])]
            except Exception:
                related_preview = []

            return render(
                request,
                "confirm_delete.html",
                {
                    "obj": obj,
                    "cancel_url": cancel_url,
                    "delete_error": "No se puede eliminar porque este registro tiene elementos asociados.",
                    "related_preview": related_preview,
                },
            )

        except IntegrityError:
            return render(
                request,
                "confirm_delete.html",
                {
                    "obj": obj,
                    "cancel_url": cancel_url,
                    "delete_error": "No se puede eliminar por restricciones de integridad en la base de datos.",
                    "related_preview": [],
                },
            )
    return render(request, "confirm_delete.html", {"obj": obj, "cancel_url": cancel_url})
