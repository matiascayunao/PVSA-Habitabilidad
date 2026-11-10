

document.addEventListener("DOMContentLoaded", function () {
  const { normalizar, parecido } = window.pvsaNombres;


  function leerJson(id, fallback) {

    const el = document.getElementById(id);

    if (!el) return fallback;

    try {

      return JSON.parse(el.textContent);

    } catch (e) {

      return fallback;

    }

  }

  const sectores = leerJson("estructura-sectores-data", []);

  const ubicaciones = leerJson("estructura-ubicaciones-data", []);

  const pisos = leerJson("estructura-pisos-data", []);

  const tiposLugar = leerJson("estructura-tipos-lugar-data", []);

  const lugares = leerJson("estructura-lugares-data", []);

  const categorias = leerJson("estructura-categorias-data", []);

  const objetos = leerJson("estructura-objetos-data", []);




  function mostrarAviso(input, exacto, similares, extraExacto) {

    if (!input) return;

    let box = input.parentElement.querySelector(".name-warning");

    if (!box) {

      box = document.createElement("div");

      box.className = "name-warning d-none";

      input.insertAdjacentElement("afterend", box);

    }

    if (exacto) {

      box.className = "name-warning name-warning-exact";

      box.innerHTML =

        '<i class="bi bi-x-circle-fill me-1"></i>' +

        (extraExacto || "Ya existe un registro con este nombre. Usa el existente.");

      return;

    }

    if (similares && similares.length) {

      box.className = "name-warning name-warning-similar";

      box.innerHTML =

        '<div class="fw-semibold">' +

        '<i class="bi bi-exclamation-triangle-fill me-1"></i>' +

        'Revisa el nombre antes de continuar.</div>' +

        '<div class="mt-1">Ya existe algo muy parecido: <strong>' +

        similares.slice(0, 2).map(pvsaEscapeHtml).join("</strong>, <strong>") +

        '</strong>.</div>';

      return;

    }

    box.className = "name-warning d-none";

    box.innerHTML = "";

  }

  function validarNombreSimple(input, lista) {

    if (!input) return;

    const valor = normalizar(input.value);

    if (!valor) {

      mostrarAviso(input, null, []);

      return;

    }

    const exacto = lista.find(function (nombre) {

      return normalizar(nombre) === valor;

    });

    const similares = lista

      .filter(function (nombre) {

        return parecido(valor, nombre);

      })

      .slice(0, 2);

    mostrarAviso(input, exacto, similares);

  }

  const sectorNuevo = document.getElementById("id_sector_nuevo");

  const ubicacionNueva = document.getElementById("id_ubicacion_nueva");

  const pisoNuevo = document.getElementById("id_piso_nuevo");

  const ubicacionExistente = document.getElementById("id_ubicacion_existente");

  const tipoLugarNuevo = document.getElementById("id_tipo_lugar_nuevo");

  const lugarNuevo = document.getElementById("id_lugar_nuevo");

  const pisoExistente = document.getElementById("id_piso_existente");

  if (sectorNuevo) {

    sectorNuevo.addEventListener("input", function () {

      validarNombreSimple(sectorNuevo, sectores);

    });

    validarNombreSimple(sectorNuevo, sectores);

  }

  function validarUbicacionNueva() {

      const valor = normalizar(ubicacionNueva.value);

      const exacto = ubicaciones.find(function (item) {

        return normalizar(item.ubicacion) === valor;

      });

      const similares = ubicaciones

        .filter(function (item) {

          return parecido(valor, item.ubicacion);

        })

        .slice(0, 2)

        .map(function (item) {

          return item.ubicacion + " · " + item.sector__sector;

        });

      mostrarAviso(

        ubicacionNueva,

        exacto,

        similares,

        exacto

          ? "Ya existe <strong>" + pvsaEscapeHtml(exacto.ubicacion) +

            "</strong> en <strong>" + pvsaEscapeHtml(exacto.sector__sector) +

            "</strong>. Selecciona esa ubicación en vez de crearla de nuevo."

          : ""

      );

  }

  if (ubicacionNueva) {
    ubicacionNueva.addEventListener("input", validarUbicacionNueva);
    // Solo muestra la advertencia inicial: NO dispara eventos sobre los selectores.
    validarUbicacionNueva();
  }

  function validarPiso() {

    if (!pisoNuevo) return;

    const valor = String(pisoNuevo.value || "").trim();

    const ubicacionId = Number(ubicacionExistente?.value || 0);

    if (!valor || !ubicacionId) {

      mostrarAviso(pisoNuevo, null, []);

      return;

    }

    const exacto = pisos.find(function (item) {

      return Number(item.ubicacion_id) === ubicacionId &&

        String(item.piso) === valor;

    });

    mostrarAviso(

      pisoNuevo,

      exacto,

      [],

      exacto

        ? "Ese piso ya existe en la ubicación seleccionada. Usa el piso existente."

        : ""

    );

  }

  if (pisoNuevo) pisoNuevo.addEventListener("input", validarPiso);

  if (ubicacionExistente) ubicacionExistente.addEventListener("change", validarPiso);

  validarPiso();

  if (tipoLugarNuevo) {

    tipoLugarNuevo.addEventListener("input", function () {

      validarNombreSimple(tipoLugarNuevo, tiposLugar);

    });

    validarNombreSimple(tipoLugarNuevo, tiposLugar);

  }

  function validarLugar() {

    if (!lugarNuevo) return;

    const valor = normalizar(lugarNuevo.value);

    const pisoId = Number(pisoExistente?.value || 0);

    if (!valor || !pisoId) {

      mostrarAviso(lugarNuevo, null, []);

      return;

    }

    const candidatos = lugares.filter(function (item) {

      return Number(item.piso_id) === pisoId;

    });

    const exacto = candidatos.find(function (item) {

      return normalizar(item.nombre_del_lugar) === valor;

    });

    const similares = candidatos

      .filter(function (item) {

        return parecido(valor, item.nombre_del_lugar);

      })

      .slice(0, 2)

      .map(function (item) {

        return item.nombre_del_lugar;

      });

    mostrarAviso(

      lugarNuevo,

      exacto,

      similares,

      exacto

        ? "Ya existe <strong>" + pvsaEscapeHtml(exacto.nombre_del_lugar) +

          "</strong> en este piso. Selecciona ese lugar en vez de crear otro."

        : ""

    );

  }

  if (lugarNuevo) lugarNuevo.addEventListener("input", validarLugar);

  if (pisoExistente) pisoExistente.addEventListener("change", validarLugar);

  validarLugar();

  const container = document.getElementById("objetos-container");

  function validarFila(input) {

    if (!input) return;

    if (input.name && input.name.endsWith("-categoria_nueva")) {

      validarNombreSimple(input, categorias);

      return;

    }

    if (input.name && input.name.endsWith("-objeto_nuevo")) {

      const valor = normalizar(input.value);

      const exacto = objetos.find(function (item) {

        return normalizar(item.nombre_del_objeto) === valor;

      });

      const similares = objetos

        .filter(function (item) {

          return parecido(valor, item.nombre_del_objeto);

        })

        .slice(0, 2)

        .map(function (item) {

          return item.nombre_del_objeto +

            " · " + item.objeto_categoria__nombre_de_categoria;

        });

      mostrarAviso(

        input,

        exacto,

        similares,

        exacto

          ? "Ya existe <strong>" + pvsaEscapeHtml(exacto.nombre_del_objeto) +

            "</strong> en <strong>" +

            pvsaEscapeHtml(exacto.objeto_categoria__nombre_de_categoria) +

            "</strong>. Selecciónalo como objeto existente."

          : ""

      );

    }

  }

  if (container) {

    container.addEventListener("input", function (e) {

      validarFila(e.target);

    });

    container.querySelectorAll(

      'input[name$="-categoria_nueva"], input[name$="-objeto_nuevo"]'

    ).forEach(validarFila);

  }

});

