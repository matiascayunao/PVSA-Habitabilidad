def entero_identificador(valor):
    texto = str(valor).strip() if valor is not None else ""
    if not texto or len(texto) > 20:
        raise ValueError("Identificador inválido.")
    digitos = texto[1:] if texto.startswith(("+", "-")) else texto
    if not digitos.isdecimal():
        raise ValueError("Identificador inválido.")
    numero = int(texto)
    if not -9223372036854775808 <= numero <= 9223372036854775807:
        raise ValueError("Identificador fuera de rango.")
    return numero
