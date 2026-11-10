(function () {
  function ejecutar(metodo, clave, valor) {
    try {
      return localStorage[metodo](clave, valor);
    } catch (error) {
      return null;
    }
  }
  window.pvsaStorage = {
    getItem: clave => ejecutar("getItem", clave),
    setItem: (clave, valor) => ejecutar("setItem", clave, valor),
    removeItem: clave => ejecutar("removeItem", clave)
  };
})();
