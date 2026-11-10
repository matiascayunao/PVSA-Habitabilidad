
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".password-toggle").forEach(function (button) {
    button.addEventListener("click", function () {
      const input = document.getElementById(button.dataset.target);
      const icon = button.querySelector("i");

      if (!input) return;

      const mostrar = input.type === "password";
      input.type = mostrar ? "text" : "password";

      if (icon) {
        icon.className = mostrar ? "bi bi-eye-slash" : "bi bi-eye";
      }

      button.setAttribute(
        "aria-label",
        mostrar ? "Ocultar contraseña" : "Mostrar contraseña"
      );
    });
  });
});
