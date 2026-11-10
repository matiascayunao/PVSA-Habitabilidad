(function(){
  const tabla = document.getElementById("tablaObjetosLugar");
  const filter = document.getElementById("tableFilter");
  const rowsShown = document.getElementById("rowsShown");
  const filterStatus = document.getElementById("filterStatus");
  function paintEstado(select){
    if (!select) return;
    select.classList.remove("estado-good", "estado-pend", "estado-bad");
    const v = (select.value || "").trim();
    if (v === "B") select.classList.add("estado-good");
    if (v === "P") select.classList.add("estado-pend");
    if (v === "M") select.classList.add("estado-bad");
  }
  function leerEntero(el, predeterminado = NaN){
    if (!el) return predeterminado;
    if (el.validity && (el.validity.badInput || el.validity.stepMismatch ||
        el.validity.rangeUnderflow || el.validity.rangeOverflow)) return NaN;
    const texto = String(el.value ?? "").trim();
    if (!texto) return predeterminado;
    if (!/^-?\d+$/.test(texto)) return NaN;
    const numero = Number(texto);
    return Number.isSafeInteger(numero) && numero <= 2147483647 && numero >= -2147483648
      ? numero : NaN;
  }
  function recalcularEstadoFila(tr){
    if (!tr) return;
    const total = leerEntero(tr.querySelector('[data-k="cantidad"]'));
    const malas = leerEntero(tr.querySelector('[data-k="cantidad_mala"]'));
    const pendientes = leerEntero(tr.querySelector('[data-k="cantidad_pendiente"]'));
    const minimo = leerEntero(tr.querySelector('[data-k="minimo_operativo"]'));
    const estadoEl = tr.querySelector('[data-k="estado"]');
    const valido = Number.isSafeInteger(total) && total > 0 &&
      Number.isSafeInteger(malas) && malas >= 0 &&
      Number.isSafeInteger(pendientes) && pendientes >= 0 &&
      Number.isSafeInteger(minimo) && minimo >= 1 && minimo <= total &&
      malas + pendientes <= total;
    tr.classList.toggle("row-invalid", !valido);
    if (!estadoEl) return;
    if (!valido){
      estadoEl.selectedIndex = -1;
    } else {
      estadoEl.value = malas > 0 ? "M" : (pendientes > 0 ? "P" : "B");
    }
    paintEstado(estadoEl);
  }
  function countVisibleRows(){
    if (!tabla) return 0;
    const trs = tabla.querySelectorAll("tbody tr");
    let visible = 0;
    trs.forEach(tr => {
      if (tr.style.display !== "none") visible++;
    });
    return visible;
  }
  function setRowsShown(n){
    if (!rowsShown) return;
    rowsShown.textContent = String(n);
  }
  if (tabla){
    tabla.querySelectorAll("tbody tr").forEach(tr => {
      recalcularEstadoFila(tr);
    });
    tabla.querySelectorAll("select.estadoSel").forEach(sel => {
      paintEstado(sel);
      sel.addEventListener("change", () => paintEstado(sel));
    });
    tabla.addEventListener("input", function(e){
      if (
        e.target.matches('[data-k="cantidad"]') ||
        e.target.matches('[data-k="cantidad_mala"]') ||
        e.target.matches('[data-k="cantidad_pendiente"]') ||
        e.target.matches('[data-k="minimo_operativo"]')
      ) {
        const tr = e.target.closest("tr");
        recalcularEstadoFila(tr);
      }
    });
    setRowsShown(countVisibleRows());
  }
  const tbodyRows = tabla ? Array.from(tabla.querySelectorAll("tbody tr")) : [];
  let lastQuery = "";
  let indexBuilt = false;
  let pendingRAF = 0;
  function showFilterStatus(msg){
    if (!filterStatus) return;
    filterStatus.textContent = msg || "Filtrando...";
    filterStatus.classList.remove("d-none");
  }
  function hideFilterStatus(){
    if (!filterStatus) return;
    filterStatus.classList.add("d-none");
  }
  function debounce(fn, ms){
    let t = 0;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }
  function buildRowSearch(tr){
    const parts = [];
    tr.querySelectorAll("[data-k]").forEach(el => {
      const v = el.value ?? "";
      parts.push(String(v));
    });
    tr.dataset.search = parts.join(" ").toLowerCase();
  }
  function buildIndex(done){
    if (!tabla || indexBuilt) {
      if (done) done();
      return;
    }
    showFilterStatus("Indexando...");
    let i = 0;
    const CHUNK = 200;
    function step(){
      const end = Math.min(i + CHUNK, tbodyRows.length);
      for (; i < end; i++){
        buildRowSearch(tbodyRows[i]);
      }
      if (i < tbodyRows.length){
        requestAnimationFrame(step);
      } else {
        indexBuilt = true;
        hideFilterStatus();
        if (done) done();
      }
    }
    step();
  }
  if (tabla){
    const onEdit = (e) => {
      const tr = e.target.closest("tr");
      if (!tr || !tr.classList.contains("rowedit")) return;
      if (!indexBuilt) return;
      buildRowSearch(tr);
    };
    tabla.addEventListener("input", onEdit, true);
    tabla.addEventListener("change", onEdit, true);
  }
  function applyFilter(query){
    if (!tabla) return;
    const q = (query || "").trim().toLowerCase();
    if (q === lastQuery) return;
    if (pendingRAF) cancelAnimationFrame(pendingRAF);
    pendingRAF = 0;
    lastQuery = q;
    showFilterStatus("Filtrando...");
    let i = 0;
    let visible = 0;
    const CHUNK = 250;
    function step(){
      const end = Math.min(i + CHUNK, tbodyRows.length);
      for (; i < end; i++){
        const tr = tbodyRows[i];
        const hay = tr.dataset.search || "";
        const show = (!q || hay.includes(q));
        tr.style.display = show ? "" : "none";
        if (show) visible++;
      }
      if (i < tbodyRows.length){
        pendingRAF = requestAnimationFrame(step);
      } else {
        pendingRAF = 0;
        setRowsShown(visible);
        hideFilterStatus();
      }
    }
    step();
  }
  const onFilterInput = debounce(() => {
    buildIndex(() => applyFilter(filter.value));
  }, 200);
  if (tabla && filter){
    filter.addEventListener("input", onFilterInput);
  }
  const colsList = document.getElementById("colsList");
  const btnShowAll = document.getElementById("colsShowAll");
  const COLS_KEY = "pvsa_carga_masiva_cols_v2";
  const COLS = [
    {k:"sector", label:"Sector"},
    {k:"ubicacion", label:"Ubicación"},
    {k:"piso", label:"Piso"},
    {k:"tipo_de_lugar", label:"Tipo de lugar"},
    {k:"lugar", label:"Lugar"},
    {k:"categoria", label:"Categoría"},
    {k:"objeto", label:"Objeto"},
    {k:"marca", label:"Marca"},
    {k:"material", label:"Material"},
    {k:"cantidad", label:"Total"},
    {k:"cantidad_mala", label:"Con falla"},
    {k:"cantidad_pendiente", label:"Por revisar"},
    {k:"minimo_operativo", label:"Mínimo operativo"},
    {k:"importancia", label:"Importancia"},
    {k:"estado", label:"Estado"},
    {k:"detalle", label:"Observación"},
  ];
  function loadColsState(){
    try{
      const raw = localStorage.getItem(COLS_KEY);
      if (!raw) return null;
      const obj = JSON.parse(raw);
      return (obj && typeof obj === "object") ? obj : null;
    } catch(e) {
      return null;
    }
  }
  function saveColsState(state){
    try {
      localStorage.setItem(COLS_KEY, JSON.stringify(state));
    } catch(e) {}
  }
  function setColVisible(colKey, visible){
    if (!tabla) return;
    tabla.querySelectorAll(`[data-col="${colKey}"]`).forEach(el => {
      el.classList.toggle("col-hidden", !visible);
    });
  }
  function applyCols(state){
    COLS.forEach(c => {
      const v = (state[c.k] !== undefined) ? !!state[c.k] : true;
      setColVisible(c.k, v);
      const cb = document.getElementById("cbcol_" + c.k);
      if (cb) cb.checked = v;
    });
  }
  if (tabla && colsList){
    const saved = loadColsState() || {};
    COLS.forEach(c => {
      if (saved[c.k] === undefined) saved[c.k] = true;
    });
    colsList.innerHTML = "";
    COLS.forEach(c => {
      const wrap = document.createElement("div");
      wrap.className = "form-check";
      wrap.innerHTML = `
        <input class="form-check-input" type="checkbox" id="cbcol_${c.k}">
        <label class="form-check-label" for="cbcol_${c.k}">${c.label}</label>
      `;
      colsList.appendChild(wrap);
      const cb = wrap.querySelector("input");
      cb.checked = !!saved[c.k];
      cb.addEventListener("change", () => {
        saved[c.k] = cb.checked;
        setColVisible(c.k, cb.checked);
        saveColsState(saved);
      });
    });
    if (btnShowAll){
      btnShowAll.addEventListener("click", () => {
        COLS.forEach(c => saved[c.k] = true);
        applyCols(saved);
        saveColsState(saved);
      });
    }
    applyCols(saved);
  }
  const btnGuardar = document.getElementById("btnGuardar");
  const payloadInput = document.getElementById("payload_json");
  const form = document.getElementById("importForm");
  const spinner = document.getElementById("saveSpinner");
  const btnLabel = btnGuardar ? btnGuardar.querySelector(".btnLabel") : null;
  if (btnGuardar && tabla && payloadInput && form) {
    btnGuardar.addEventListener("click", () => {
      const trs = Array.from(tabla.querySelectorAll("tbody tr"));
      const validationAlert = document.getElementById("previewValidationAlert");
      let filasInvalidas = 0;
      trs.forEach(tr => {
        tr.classList.remove("row-invalid");
        const sector = (tr.querySelector('[data-k="sector"]')?.value || "").trim();
        const ubicacion = (tr.querySelector('[data-k="ubicacion"]')?.value || "").trim();
        const lugar = (tr.querySelector('[data-k="lugar"]')?.value || "").trim();
        const objeto = (tr.querySelector('[data-k="objeto"]')?.value || "").trim();
        const total = leerEntero(tr.querySelector('[data-k="cantidad"]'));
        const falla = leerEntero(tr.querySelector('[data-k="cantidad_mala"]'));
        const revisar = leerEntero(tr.querySelector('[data-k="cantidad_pendiente"]'));
        const minimo = leerEntero(tr.querySelector('[data-k="minimo_operativo"]'));
        const importancia = (tr.querySelector('[data-k="importancia"]')?.value || "").trim();
        const invalida =
          !sector ||
          !ubicacion ||
          !lugar ||
          !objeto ||
          !Number.isSafeInteger(total) || total <= 0 ||
          !Number.isSafeInteger(falla) || falla < 0 ||
          !Number.isSafeInteger(revisar) || revisar < 0 ||
          !Number.isSafeInteger(minimo) || minimo < 1 ||
          !["1", "2", "3"].includes(importancia) ||
          falla + revisar > total || minimo > total;
        if (invalida) {
          filasInvalidas += 1;
          tr.classList.add("row-invalid");
        }
      });
      if (filasInvalidas) {
        if (validationAlert) {
          validationAlert.innerHTML =
            '<i class="bi bi-exclamation-circle-fill me-1"></i>' +
            'Hay <strong>' + filasInvalidas + '</strong> fila(s) que necesitan revisión. ' +
            'Comprueba Sector, Ubicación, Lugar, Objeto, Cantidad total, Con falla, Por revisar, Mínimo operativo e Importancia. Los campos numéricos no pueden estar vacíos.';
          validationAlert.classList.remove("d-none");
          validationAlert.scrollIntoView({behavior:"smooth", block:"center"});
        }
        return;
      }
      if (validationAlert) {
        validationAlert.classList.add("d-none");
        validationAlert.innerHTML = "";
      }
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      if (!window.confirm("Se importarán " + trs.length + " filas. Los inventarios que ya existan se actualizarán, reemplazando cantidades, importancia y observaciones. ¿Continuar?")) {
        return;
      }
      btnGuardar.disabled = true;
      if (spinner) spinner.classList.remove("d-none");
      if (btnLabel) btnLabel.textContent = "Importando...";
      const rows = [];
      trs.forEach(tr => {
        recalcularEstadoFila(tr);
        const obj = {};
        tr.querySelectorAll("[data-k]").forEach(el => {
          const k = el.getAttribute("data-k");
          let v = (el.value ?? "").trim();
          if (
            k === "cantidad" ||
            k === "cantidad_mala" ||
            k === "cantidad_pendiente" ||
            k === "minimo_operativo" ||
            k === "importancia"
          ) {
            // Un campo vacío NO equivale a 0 ni a 1: el servidor exige
            // que los cuatro valores operativos se indiquen expresamente.
            v = v === "" ? null : Number(v);
          }
          obj[k] = v;
        });
        rows.push(obj);
      });
      payloadInput.value = JSON.stringify({ objetos_lugar: rows });
      form.requestSubmit();
    });
  }
})();
