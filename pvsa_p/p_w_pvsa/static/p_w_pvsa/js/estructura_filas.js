
document.addEventListener("DOMContentLoaded", function () {
    const addBtn = document.getElementById("add-obj-btn");
    const secondaryAddBtn = document.getElementById("add-obj-btn-bottom");
    const container = document.getElementById("objetos-container");
    const totalFormsInput = document.getElementById("id_obj-TOTAL_FORMS");
    const emptyFormDiv = document.getElementById("empty-form");
    if (!addBtn || !container || !totalFormsInput || !emptyFormDiv) return;

    let bloqueado = false;

    function renumerarTitulos() {
        container.querySelectorAll(".objeto-form").forEach(function (card, idx) {
            const numero = idx + 1;
            const titulo = card.querySelector(".objeto-title");
            const distintivo = card.querySelector(".object-number");
            if (titulo) titulo.textContent = "Objeto " + numero;
            if (distintivo) distintivo.textContent = String(numero);
        });
    }

    function reindexForms() {
        const forms = container.querySelectorAll(".objeto-form");
        forms.forEach(function (formElem, index) {
            const campos = formElem.querySelectorAll("input, select, textarea, label");
            campos.forEach(function (el) {
                if (el.name && el.name.indexOf("obj-") === 0) {
                    el.name = el.name.replace(/obj-(\d+)-/, "obj-" + index + "-");
                }
                if (el.id && el.id.indexOf("id_obj-") === 0) {
                    el.id = el.id.replace(/id_obj-(\d+)-/, "id_obj-" + index + "-");
                }
                if (el.htmlFor && el.htmlFor.indexOf("id_obj-") === 0) {
                    el.htmlFor = el.htmlFor.replace(/id_obj-(\d+)-/, "id_obj-" + index + "-");
                }
            });
        });
        totalFormsInput.value = forms.length;
        renumerarTitulos();
    }

    // Evita que una inserción o eliminación manual cambie índices mientras
    // los objetos habituales esperan la carga AJAX de objeto y variante.
    function bloquearFilas(estado) {
        bloqueado = Boolean(estado);
        addBtn.disabled = bloqueado;
        if (secondaryAddBtn) secondaryAddBtn.disabled = bloqueado;
        container.querySelectorAll(".remove-obj-btn").forEach(function (btn) {
            btn.disabled = bloqueado;
        });
    }

    function agregarFila(desdeHabituales = false) {
        if (bloqueado && !desdeHabituales) return { idx: null, card: null };
        const newIndex = parseInt(totalFormsInput.value, 10) || 0;
        const templateHtml = emptyFormDiv.innerHTML.replace(/__prefix__/g, newIndex);
        const tempContainer = document.createElement("div");
        tempContainer.innerHTML = templateHtml.trim();
        const newForm = tempContainer.firstElementChild;
        if (!newForm) return { idx: null, card: null };
        container.appendChild(newForm);
        reindexForms();
        bloquearFilas(bloqueado);
        return { idx: newIndex, card: newForm };
    }

    // La inserción manual y la de objetos habituales comparten exactamente
    // la misma lógica de nombres, identificadores y numeración visible.
    window.pvsaEstructuraFilas = {
        agregar: agregarFila,
        sincronizar: reindexForms,
        bloquear: bloquearFilas
    };

    addBtn.addEventListener("click", function (e) {
        e.preventDefault();
        agregarFila();
    });

    container.addEventListener("click", function (e) {
        const btn = e.target.closest(".remove-obj-btn");
        if (!btn || bloqueado) return;
        e.preventDefault();
        const card = btn.closest(".objeto-form");
        if (card) {
            card.remove();
            reindexForms();
        }
    });

    reindexForms();
});
