(function () {
  function normalizar(valor) {

    return String(valor || "")

      .normalize("NFD")

      .replace(/[\u0300-\u036f]/g, "")

      .trim()

      .replace(/\s+/g, " ")

      .toLocaleLowerCase("es");

  }
  function distancia(a, b) {

    a = normalizar(a);

    b = normalizar(b);

    const filas = a.length + 1;

    const columnas = b.length + 1;

    const matriz = Array.from({ length: filas }, function () {

      return Array(columnas).fill(0);

    });

    for (let i = 0; i < filas; i++) matriz[i][0] = i;

    for (let j = 0; j < columnas; j++) matriz[0][j] = j;

    for (let i = 1; i < filas; i++) {

      for (let j = 1; j < columnas; j++) {

        const costo = a[i - 1] === b[j - 1] ? 0 : 1;

        matriz[i][j] = Math.min(

          matriz[i - 1][j] + 1,

          matriz[i][j - 1] + 1,

          matriz[i - 1][j - 1] + costo

        );

      }

    }

    return matriz[a.length][b.length];

  }
  function parecido(a, b, minimo = 4, corto = 8, medio = 16) {

    const x = normalizar(a);

    const y = normalizar(b);

    if (!x || !y || x === y) return false;

    if (Math.min(x.length, y.length) < minimo) return false;

    const d = distancia(x, y);

    const largo = Math.max(x.length, y.length);

    if (largo <= corto) return d === 1;

    if (largo <= medio) return d <= 2;

    if (d <= 3) return true;

    return Math.abs(x.length - y.length) <= 2 &&

      (x.includes(y) || y.includes(x));

  }
  window.pvsaNombres = { normalizar, distancia, parecido };
})();
