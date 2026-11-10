(function(){
  const dz = document.getElementById("dropzone");
  const input = document.getElementById("id_archivo");
  const filename = document.getElementById("dz-filename");
  const status = document.getElementById("dz-status");
  const btnPick = document.getElementById("btnPick");
  const btnClear = document.getElementById("btnClear");
  const btnUpload = document.getElementById("btnUpload");
  let subiendo = false;
  function setUploadState(){
    const has = input && input.files && input.files.length;
    if (!status) return;
    if (has){
      status.textContent = "Archivo listo para subir";
      if (filename) filename.textContent = input.files[0].name;
      const dot = document.querySelector(".dz-pill-dot");
      if (dot) dot.style.background = "#198754";
      if (btnClear) btnClear.classList.remove("d-none");
      if (btnUpload) btnUpload.disabled = subiendo;
    } else {
      status.textContent = "Sin archivo seleccionado";
      if (filename) filename.textContent = "";
      const dot = document.querySelector(".dz-pill-dot");
      if (dot) dot.style.background = "#adb5bd";
      if (btnClear) btnClear.classList.add("d-none");
      if (btnUpload) btnUpload.disabled = true;
    }
  }
  if (dz && input) {
    const openPicker = () => input.click();
    dz.addEventListener("click", openPicker);
    dz.addEventListener("keydown", (e) => {
      if (e.target !== dz) return;
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        e.stopPropagation();
        openPicker();
      }
    });
    if (btnPick) {
      btnPick.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        openPicker();
      });
    }
    input.addEventListener("change", setUploadState);
    if (btnClear){
      btnClear.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        input.value = "";
        setUploadState();
      });
    }
    dz.addEventListener("dragover", (e) => {
      e.preventDefault();
      dz.classList.add("dragover");
    });
    dz.addEventListener("dragleave", () => dz.classList.remove("dragover"));
    dz.addEventListener("drop", (e) => {
      e.preventDefault();
      dz.classList.remove("dragover");
      if (!e.dataTransfer.files || !e.dataTransfer.files.length) return;
      const dt = new DataTransfer();
      for (const f of e.dataTransfer.files) dt.items.add(f);
      input.files = dt.files;
      setUploadState();
    });
    const formulario = input.form;
    if (formulario) formulario.addEventListener("submit", function (event) {
      if (subiendo) {
        event.preventDefault();
        return;
      }
      if (event.defaultPrevented || !formulario.checkValidity()) return;
      subiendo = true;
      if (btnUpload) btnUpload.disabled = true;
    });
    window.addEventListener("pageshow", function () {
      subiendo = false;
      setUploadState();
    });
    setUploadState();
  }
})();
