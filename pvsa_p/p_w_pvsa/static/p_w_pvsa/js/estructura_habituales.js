

(() => {

  if (window.__TIPICOS_MODAL_INSTALLED__) return;

  window.__TIPICOS_MODAL_INSTALLED__ = true;

  const $ = (sel, root = document) => root.querySelector(sel);

  function ensureModal() {

    let modalEl =

      document.getElementById("modalObjetosTipicos") ||

      document.getElementById("modal-objetos-tipicos");

    if (modalEl) return modalEl;

    const wrap = document.createElement("div");

    wrap.innerHTML = `

<div class="modal fade" id="modalObjetosTipicos" tabindex="-1" aria-hidden="true">

  <div class="modal-dialog modal-lg modal-dialog-scrollable">

    <div class="modal-content">

      <div class="modal-header">

        <h5 class="modal-title">Objetos habituales del tipo de lugar</h5>

        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>

      </div>

      <div class="modal-body">

        <p class="text-muted mb-2">Marca los objetos que quieres agregar al lugar.</p>

        <div id="lista-objetos-tipicos" class="d-flex flex-column gap-2"></div>

        <div id="tipicos-vacio" class="text-muted small mt-2" style="display:none;">

          Este tipo de lugar no tiene objetos habituales configurados.

        </div>

      </div>

      <div class="modal-footer">

        <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancelar</button>

        <button type="button" class="btn btn-primary" id="btnAgregarTipicos">Agregar objetos</button>

      </div>

    </div>

  </div>

</div>`;

    document.body.appendChild(wrap.firstElementChild);

    return document.getElementById("modalObjetosTipicos");

  }

  function getTotalFormsInput() {

    return document.querySelector('input[name$="-TOTAL_FORMS"]');

  }

  function getPrefix() {

    const inp = getTotalFormsInput();

    return inp ? inp.name.replace("-TOTAL_FORMS", "") : "form";

  }

  function addNewRowAndGetIndex() {
    const gestor = window.pvsaEstructuraFilas;
    return gestor ? gestor.agregar(true) : { idx: null, card: null };
  }

  function findByName(name, root = document) {

    return root.querySelector(`[name="${CSS.escape(name)}"]`);

  }

  function dispatchChange(el) {

    if (!el) return;

    el.dispatchEvent(new Event("change", { bubbles: true }));

  }

  function clearText(name, root = document) {

    const el = findByName(name, root);

    if (el) el.value = "";

  }

  function setValueByName(name, value, root = document) {

    const el = findByName(name, root);

    if (!el) return null;

    el.value = String(value);

    return el;

  }

  async function waitForOption(selectEl, value, timeoutMs = 2500) {

    if (!selectEl) return false;

    const target = String(value);

    const start = Date.now();

    while (Date.now() - start < timeoutMs) {

      const has = Array.from(selectEl.options).some(o => String(o.value) === target);

      if (has) return true;

      await new Promise(r => setTimeout(r, 50));

    }

    return false;

  }

  function aplicarSugerencia(prefix, idx, item, cardRoot) {
    const campos = [
      ["categoria_existente", item.categoria_id, item.categoria_nombre],
      ["objeto_existente", item.objeto_id, item.objeto_nombre],
      ["tipo_objeto_existente", item.tipo_objeto_id, "---------"]
    ];
    for (const [campo, valor, texto] of campos) {
      const select = findByName(`${prefix}-${idx}-${campo}`, cardRoot);
      if (!select) return false;
      if (!Array.from(select.options).some(option => String(option.value) === String(valor || ""))) {
        const option = document.createElement("option");
        option.value = valor || "";
        option.textContent = texto;
        select.appendChild(option);
      }
      select.value = String(valor || "");
      if (!valor && select.options[select.selectedIndex]) select.options[select.selectedIndex].textContent = texto;
    }
    setValueByName(`${prefix}-${idx}-categoria_nueva`, item.categoria_id ? "" : item.categoria_nombre, cardRoot);
    setValueByName(`${prefix}-${idx}-objeto_nuevo`, item.objeto_id ? "" : item.objeto_nombre, cardRoot);
    return Boolean(setValueByName(`${prefix}-${idx}-sugerencia_habitual`, item.referencia, cardRoot));
  }

  async function setCascadeSelects(prefix, idx, item, cardRoot) {
    if (item.referencia) {
      if (!aplicarSugerencia(prefix, idx, item, cardRoot)) return false;
    } else {

    const categoriaName = `${prefix}-${idx}-categoria_existente`;

    const objetoName = `${prefix}-${idx}-objeto_existente`;

    const tipoName = `${prefix}-${idx}-tipo_objeto_existente`;

    const categoriaSel = setValueByName(categoriaName, item.categoria_id, cardRoot);
    if (!categoriaSel || String(categoriaSel.value) !== String(item.categoria_id)) return false;
    dispatchChange(categoriaSel);

    const objetoSel = findByName(objetoName, cardRoot);
    if (!objetoSel || !await waitForOption(objetoSel, item.objeto_id)) return false;
    objetoSel.value = String(item.objeto_id);
    dispatchChange(objetoSel);

    const tipoSel = findByName(tipoName, cardRoot);
    if (!tipoSel || !await waitForOption(tipoSel, item.tipo_objeto_id)) return false;
    tipoSel.value = String(item.tipo_objeto_id);
    dispatchChange(tipoSel);

    }
    const cantName = `${prefix}-${idx}-cantidad`;

    const malaName = `${prefix}-${idx}-cantidad_mala`;

    const pendienteName = `${prefix}-${idx}-cantidad_pendiente`;

    const importanciaName = `${prefix}-${idx}-importancia`;

    const minimoName = `${prefix}-${idx}-minimo_operativo`;

    const cantEl = findByName(cantName, cardRoot) || findByName(cantName);

    if (cantEl && (cantEl.value === "" || cantEl.value == null)) {

      cantEl.value = 1;

    }

    const malaEl = findByName(malaName, cardRoot) || findByName(malaName);

    if (malaEl && (malaEl.value === "" || malaEl.value == null)) {

      malaEl.value = 0;

    }

    const pendienteEl = findByName(pendienteName, cardRoot) || findByName(pendienteName);

    if (pendienteEl && (pendienteEl.value === "" || pendienteEl.value == null)) {

      pendienteEl.value = 0;

    }

    const importanciaEl = findByName(importanciaName, cardRoot) || findByName(importanciaName);

    if (importanciaEl && (importanciaEl.value === "" || importanciaEl.value == null)) {

      importanciaEl.value = 1;

    }

    const minimoEl = findByName(minimoName, cardRoot) || findByName(minimoName);

    if (minimoEl && (minimoEl.value === "" || minimoEl.value == null)) {

      minimoEl.value = 1;

    }

    return true;
  }

  function closeModalHard(modalEl) {

    if (!modalEl) return;

    try {

      if (typeof bootstrap !== "undefined") {

        const inst = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);

        inst.hide();

      }

    } catch (e) {}

    setTimeout(() => {

      modalEl.classList.remove("show");

      modalEl.style.display = "none";

      modalEl.setAttribute("aria-hidden", "true");

      modalEl.removeAttribute("aria-modal");

      document.body.classList.remove("modal-open");

      document.querySelectorAll(".modal-backdrop").forEach(b => b.remove());

      document.body.style.removeProperty("padding-right");

      document.body.style.removeProperty("overflow");

    }, 50);

  }

  document.addEventListener("DOMContentLoaded", () => {

    const tipoLugarSelect = document.getElementById("id_tipo_lugar_existente");

    if (!tipoLugarSelect) return;

    const modalEl = ensureModal();

    const lista =

      document.getElementById("lista-objetos-tipicos") ||

      document.getElementById("listaObjetosTipicos");

    const vacio = document.getElementById("tipicos-vacio");

    const btnAgregar = document.getElementById("btnAgregarTipicos");

    if (!modalEl || !lista || !btnAgregar || typeof bootstrap === "undefined") return;

    const modal = new bootstrap.Modal(modalEl);
    let solicitudTipicos = 0;
    let agregandoTipicos = false;

    async function loadTipicosAndShow(tipoLugarPk) {
      const solicitud = ++solicitudTipicos;
      lista.innerHTML = "";

      if (vacio) vacio.style.display = "none";

      const r = await fetch(`/api/objetos-tipicos/${tipoLugarPk}/`, {

        headers: { "X-Requested-With": "XMLHttpRequest" }

      });

      if (!r.ok) throw new Error("No se pudieron cargar los objetos habituales.");
      const data = await r.json();
      if (solicitud !== solicitudTipicos || String(tipoLugarSelect.value) !== String(tipoLugarPk)) return;
      const items = Array.isArray(data) ? data : (data.objetos || data.items || []);

      if (!items.length) {

        if (vacio) vacio.style.display = "block";

        modal.show();

        return;

      }

      items.forEach((it, index) => {

        const item = {

          categoria_id: it.categoria_id ?? it.categoria ?? it.categoriaId,

          objeto_id: it.objeto_id ?? it.objeto ?? it.objetoId,

          tipo_objeto_id: it.tipo_objeto_id ?? it.tipo ?? it.tipoId ?? it.tipo_objeto ?? it.tipo_objetoId,

          label: it.label ?? it.nombre ?? it.texto ?? "",
          referencia: it.referencia || "",
          categoria_nombre: it.categoria_nombre || "",
          objeto_nombre: it.objeto_nombre || ""

        };

        const checkboxId = item.referencia ? `chk_tipico_virtual_${index}` : `chk_tipico_${item.tipo_objeto_id}_${item.objeto_id}`;
        const row = document.createElement("div");

        row.className = "form-check";

        row.innerHTML = `

          <input class="form-check-input" type="checkbox" checked

                 data-categoria="${item.categoria_id}"

                 data-objeto="${item.objeto_id}"

                 data-tipo="${item.tipo_objeto_id}"

                 id="${checkboxId}">

          <label class="form-check-label" for="${checkboxId}">

            ${pvsaEscapeHtml(item.label || `ID ${item.tipo_objeto_id}`)}

          </label>

        `;

        const checkbox = row.querySelector("input");
        if (checkbox) checkbox.pvsaSugerencia = item;
        lista.appendChild(row);

      });

      modal.show();

    }

    tipoLugarSelect.addEventListener("change", async function () {

      const tipoLugarPk = this.value;
      if (!tipoLugarPk) {
        ++solicitudTipicos;
        lista.innerHTML = "";
        return;
      }

      try {

        await loadTipicosAndShow(tipoLugarPk);

      } catch (e) {

        console.error(e);

      }

    });

    btnAgregar.addEventListener("click", async function () {
      if (agregandoTipicos) return;
      const gestor = window.pvsaEstructuraFilas;
      if (!gestor) return;
      const prefix = getPrefix();
      const checks = Array.from(lista.querySelectorAll('input[type="checkbox"]:checked'));
      if (!checks.length) {
        closeModalHard(modalEl);
        return;
      }

      agregandoTipicos = true;
      btnAgregar.disabled = true;
      gestor.bloquear(true);
      let fallidos = 0;
      try {
        for (const chk of checks) {
          const item = chk.pvsaSugerencia || {
            categoria_id: chk.dataset.categoria,
            objeto_id: chk.dataset.objeto,
            tipo_objeto_id: chk.dataset.tipo
          };
          const repetido = (item.referencia && Array.from(document.querySelectorAll(
            '#objetos-container input[name$="-sugerencia_habitual"]'
          )).some(input => input.value === item.referencia)) || (item.tipo_objeto_id && Array.from(document.querySelectorAll(
            '#objetos-container select[name$="-tipo_objeto_existente"]'
          )).some(select => String(select.value) === String(item.tipo_objeto_id)));
          if (repetido) continue;

          const { idx, card } = addNewRowAndGetIndex();
          if (idx === null || !card) {
            ++fallidos;
            continue;
          }
          clearText(`${prefix}-${idx}-categoria_nueva`, card);
          clearText(`${prefix}-${idx}-objeto_nuevo`, card);
          clearText(`${prefix}-${idx}-marca`, card);
          clearText(`${prefix}-${idx}-material`, card);

          let completado = false;
          try {
            completado = await setCascadeSelects(prefix, idx, item, card);
          } catch (err) {
            console.error("Error agregando objeto habitual:", err);
          }
          if (!completado) {
            card.remove();
            gestor.sincronizar();
            ++fallidos;
          }
        }
      } finally {
        gestor.bloquear(false);
        btnAgregar.disabled = false;
        agregandoTipicos = false;
        closeModalHard(modalEl);
      }
      if (fallidos) {
        window.alert("No se pudieron cargar " + fallidos +
          " objeto(s) habitual(es). Comprueba la configuración y vuelve a intentarlo.");
      }
    });

  });

})();

