

document.addEventListener("DOMContentLoaded", function () {

  const objetosContainer = document.getElementById("objetos-container");

  if (objetosContainer) {
    function quitarReferencia(event) {
      const target = event.target;
      if (!target.name || !/-(categoria_existente|categoria_nueva|objeto_existente|objeto_nuevo|tipo_objeto_existente|marca|material)$/.test(target.name)) return;
      const card = target.closest(".objeto-form");
      const referencia = card?.querySelector('input[name$="-sugerencia_habitual"]');
      if (referencia) referencia.value = "";
    }
    objetosContainer.addEventListener("input", quitarReferencia);
    objetosContainer.addEventListener("change", quitarReferencia);


    objetosContainer.addEventListener("change", function (e) {

      const target = e.target;

      if (!target.name) return;

      if (target.name.endsWith("-categoria_existente")) {

        const card = target.closest(".objeto-form");

        if (!card) return;

        const objetoSelect = card.querySelector('select[name$="-objeto_existente"]');

        const tipoSelect = card.querySelector('select[name$="-tipo_objeto_existente"]');

        if (objetoSelect) {

          objetoSelect.innerHTML = '<option value="">---------</option>';

        }

        if (tipoSelect) {

          tipoSelect.innerHTML = '<option value="">---------</option>';

        }

        const categoriaId = target.value || "";
        const token = Number(card.dataset.cargaObjetos || 0) + 1;
        card.dataset.cargaObjetos = String(token);
        // Al cambiar la categoría se invalida también una carga previa de variantes.
        card.dataset.cargaVariantes = String(Number(card.dataset.cargaVariantes || 0) + 1);

        if (!categoriaId || !objetoSelect) return;

        fetch(`/ajax/objetos-por-categoria/?categoria_id=${encodeURIComponent(categoriaId)}`)
          .then(r => {
            if (!r.ok) throw new Error("No se pudieron cargar los objetos.");
            return r.json();
          })
          .then(data => {
            if (!card.isConnected || token !== Number(card.dataset.cargaObjetos) ||
                String(target.value) !== String(categoriaId)) return;
            data.forEach(item => {
              const opt = document.createElement("option");
              opt.value = item.id;
              opt.textContent = item.nombre;
              objetoSelect.appendChild(opt);
            });
          })
          .catch(err => console.error("Error cargando objetos:", err));

      }

      if (target.name.endsWith("-objeto_existente")) {

        const card = target.closest(".objeto-form");

        if (!card) return;

        const tipoSelect = card.querySelector('select[name$="-tipo_objeto_existente"]');

        if (!tipoSelect) return;

        tipoSelect.innerHTML = '<option value="">---------</option>';

        const objetoId = target.value || "";
        const token = Number(card.dataset.cargaVariantes || 0) + 1;
        card.dataset.cargaVariantes = String(token);

        if (!objetoId) return;

        fetch(`/ajax/tipos-por-objeto/?objeto_id=${encodeURIComponent(objetoId)}`)
          .then(r => {
            if (!r.ok) throw new Error("No se pudieron cargar las variantes.");
            return r.json();
          })
          .then(data => {
            if (!card.isConnected || token !== Number(card.dataset.cargaVariantes) ||
                String(target.value) !== String(objetoId)) return;
            data.forEach(item => {
              const opt = document.createElement("option");
              opt.value = item.id;
              opt.textContent = item.nombre;
              tipoSelect.appendChild(opt);
            });
          })
          .catch(err => console.error("Error cargando tipos de objeto:", err));

      }

    });

  }

});

