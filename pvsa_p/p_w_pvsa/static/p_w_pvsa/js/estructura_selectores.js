
document.addEventListener("DOMContentLoaded", function () {
  const sectorSel = document.getElementById("id_sector_existente");
  const ubicacionSel = document.getElementById("id_ubicacion_existente");
  const pisoSel = document.getElementById("id_piso_existente");
  const tipoSel = document.getElementById("id_tipo_lugar_existente");
  const lugarSel = document.getElementById("id_lugar_existente");
  const sectorNuevo = document.getElementById("id_sector_nuevo");
  const ubicacionNueva = document.getElementById("id_ubicacion_nueva");
  const pisoNuevo = document.getElementById("id_piso_nuevo");
  const tipoNuevo = document.getElementById("id_tipo_lugar_nuevo");
  const lugarNuevo = document.getElementById("id_lugar_nuevo");
  if (!sectorSel || !ubicacionSel || !pisoSel || !tipoSel || !lugarSel) return;

  let cargaUbicaciones = 0;
  let cargaPisos = 0;
  let cargaLugares = 0;
  const valor = el => String(el?.value || "").trim();
  function limpiar(select) {
    select.innerHTML = '<option value="">---------</option>';
    select.disabled = true;
  }
  function resetLugar() {
    ++cargaLugares;
    limpiar(lugarSel);
  }
  function resetPisoYLugar() {
    ++cargaPisos;
    limpiar(pisoSel);
    resetLugar();
  }
  function resetDescendientesSector() {
    ++cargaUbicaciones;
    limpiar(ubicacionSel);
    resetPisoYLugar();
  }
  function canLoad() {
    return !!(valor(sectorSel) && valor(ubicacionSel) && valor(pisoSel) && valor(tipoSel)) &&
      !valor(sectorNuevo) && !valor(ubicacionNueva) && !valor(pisoNuevo) && !valor(tipoNuevo);
  }
  function ponerOpciones(select, data) {
    data.forEach(item => {
      const opt = document.createElement("option");
      opt.value = String(item.id);
      opt.textContent = item.nombre;
      select.appendChild(opt);
    });
    select.disabled = data.length === 0;
  }
  async function obtener(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error("No se pudieron cargar las opciones.");
    return response.json();
  }
  async function loadLugares() {
    resetLugar();
    if (!canLoad()) return;
    const cargaActual = cargaLugares;
    const pisoId = valor(pisoSel);
    const tipoId = valor(tipoSel);
    try {
      const data = await obtener('/ajax/lugares-por-piso/?piso_id=' + encodeURIComponent(pisoId) +
        '&tipo_lugar_id=' + encodeURIComponent(tipoId));
      if (cargaActual !== cargaLugares || pisoId !== valor(pisoSel) || tipoId !== valor(tipoSel) || !canLoad()) return;
      ponerOpciones(lugarSel, data);
    } catch (err) {
      console.error("Error cargando lugares:", err);
    }
  }
  sectorSel.addEventListener("change", async function () {
    resetDescendientesSector();
    const sectorId = valor(sectorSel);
    if (sectorId && sectorNuevo) sectorNuevo.value = "";
    if (!sectorId) return;
    const cargaActual = cargaUbicaciones;
    try {
      const data = await obtener('/ajax/ubicaciones-por-sector/?sector_id=' + encodeURIComponent(sectorId));
      if (cargaActual !== cargaUbicaciones || sectorId !== valor(sectorSel) || valor(sectorNuevo)) return;
      ponerOpciones(ubicacionSel, data);
    } catch (err) {
      console.error("Error cargando ubicaciones:", err);
    }
  });
  ubicacionSel.addEventListener("change", async function () {
    resetPisoYLugar();
    const ubicacionId = valor(ubicacionSel);
    const sectorId = valor(sectorSel);
    if (ubicacionId && ubicacionNueva) ubicacionNueva.value = "";
    if (!ubicacionId || !sectorId || valor(sectorNuevo)) return;
    const cargaActual = cargaPisos;
    try {
      const data = await obtener('/ajax/pisos-por-ubicacion/?ubicacion_id=' + encodeURIComponent(ubicacionId));
      if (cargaActual !== cargaPisos || ubicacionId !== valor(ubicacionSel) || sectorId !== valor(sectorSel) || valor(ubicacionNueva)) return;
      ponerOpciones(pisoSel, data);
    } catch (err) {
      console.error("Error cargando pisos:", err);
    }
  });
  pisoSel.addEventListener("change", () => {
    if (valor(pisoSel) && pisoNuevo) pisoNuevo.value = "";
    return loadLugares();
  });
  tipoSel.addEventListener("change", () => {
    if (valor(tipoSel) && tipoNuevo) tipoNuevo.value = "";
    return loadLugares();
  });
  if (sectorNuevo) sectorNuevo.addEventListener("input", () => {
    if (valor(sectorNuevo)) sectorSel.value = "";
    resetDescendientesSector();
  });
  if (ubicacionNueva) ubicacionNueva.addEventListener("input", () => {
    if (valor(ubicacionNueva)) ubicacionSel.value = "";
    resetPisoYLugar();
  });
  if (pisoNuevo) pisoNuevo.addEventListener("input", () => {
    if (valor(pisoNuevo)) pisoSel.value = "";
    resetLugar();
  });
  if (tipoNuevo) tipoNuevo.addEventListener("input", () => {
    if (valor(tipoNuevo)) tipoSel.value = "";
    resetLugar();
  });
  if (lugarNuevo) {
    lugarSel.addEventListener("change", () => {
      if (valor(lugarSel)) lugarNuevo.value = "";
    });
    lugarNuevo.addEventListener("input", () => {
      if (valor(lugarNuevo)) lugarSel.value = "";
    });
  }

  // Preserve Django's valid bound POST selections. Never clear object rows here.
  if (!valor(sectorSel) || valor(sectorNuevo)) {
    resetDescendientesSector();
  } else if (!valor(ubicacionSel) || valor(ubicacionNueva)) {
    resetPisoYLugar();
  } else {
    ubicacionSel.disabled = false;
    pisoSel.disabled = !valor(ubicacionSel);
    if (!canLoad()) resetLugar();
    else if (!valor(lugarSel)) loadLugares();
    else lugarSel.disabled = false;
  }
});
