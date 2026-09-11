from __future__ import annotations

import argparse
import sys


class ErrorEntrada(Exception):
    """Error de formato de entrada (dígitos incorrectos, caracteres no numéricos)."""


PESOS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]


def parsear_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida un CUIT/CUIL argentino de 11 dígitos con el algoritmo de "
        "dígito verificador Módulo 11."
    )
    parser.add_argument(
        "--cuit",
        type=str,
        default=None,
        help="CUIT/CUIL a validar (11 dígitos, con o sin guiones). "
        "Si se omite, se solicita por teclado.",
    )
    return parser.parse_args(argv)


def limpiar_cuit(texto: str) -> str:
    """Quita guiones/espacios; exige que queden exactamente 11 dígitos."""
    limpio = texto.replace("-", "").replace(" ", "")
    if not limpio.isdigit():
        raise ErrorEntrada(
            f"El CUIT/CUIL debe contener solo dígitos (y opcionalmente guiones): {texto!r}"
        )
    if len(limpio) != 11:
        raise ErrorEntrada(
            f"El CUIT/CUIL debe tener 11 dígitos, se recibieron {len(limpio)}: {texto!r}"
        )
    return limpio


def formatear_cuit(cuit_11: str) -> str:
    return f"{cuit_11[0:2]}-{cuit_11[2:10]}-{cuit_11[10]}"


def calcular_digito_verificador(primeros_10: str) -> tuple[int, list[int]]:
    """Modulo 11: peso_i * digito_i, sumar, resto = suma % 11, verificador = 11 - resto
    (casos especiales 11->0, 10->9)."""
    digitos = [int(c) for c in primeros_10]
    productos = [d * p for d, p in zip(digitos, PESOS)]
    suma = sum(productos)
    resto = suma % 11
    verificador = 11 - resto
    if verificador == 11:
        verificador = 0
    elif verificador == 10:
        verificador = 9
    return verificador, productos


def validar_cuit(cuit_11: str) -> tuple[bool, int, int]:
    """Devuelve (es_valido, digito_esperado, digito_ingresado)."""
    primeros_10 = cuit_11[:10]
    digito_ingresado = int(cuit_11[10])
    digito_esperado, _ = calcular_digito_verificador(primeros_10)
    return digito_esperado == digito_ingresado, digito_esperado, digito_ingresado


def imprimir_calculo(cuit_11: str) -> None:
    """Tabla dígito/peso/producto -- demuestra el algoritmo paso a paso (punto d)."""
    primeros_10 = cuit_11[:10]
    digitos = [int(c) for c in primeros_10]
    digito_esperado, productos = calcular_digito_verificador(primeros_10)
    suma = sum(productos)
    resto = suma % 11
    print("      Dígito   " + " ".join(f"{d:>3}" for d in digitos))
    print("      Peso     " + " ".join(f"{p:>3}" for p in PESOS))
    print("      Producto " + " ".join(f"{x:>3}" for x in productos))
    print(f"      Suma de productos: {suma}")
    print(f"      {suma} mod 11 = {resto}")
    print(
        f"      Dígito verificador esperado: 11 - {resto} = {digito_esperado}"
        + (
            "  (mapeado desde 11 -> 0)"
            if (11 - resto) == 11
            else "  (mapeado desde 10 -> 9)"
            if (11 - resto) == 10
            else ""
        )
    )


def main(argv: list[str] | None = None) -> int:
    try:
        args = parsear_argumentos(argv)
        entrada = args.cuit
        if entrada is None:
            entrada = input("Ingresá el CUIT/CUIL (11 dígitos, con o sin guiones): ")
        print("[1/3] Validando formato de entrada...")
        cuit_11 = limpiar_cuit(entrada)
        print(f"      CUIT/CUIL ingresado: {formatear_cuit(cuit_11)}  (11 dígitos)")

        print("[2/3] Aplicando el algoritmo de Módulo 11 sobre los primeros 10 dígitos...")
        imprimir_calculo(cuit_11)

        print("[3/3] Comparando con el dígito ingresado...")
        es_valido, digito_esperado, digito_ingresado = validar_cuit(cuit_11)
        print(f"      Dígito ingresado: {digito_ingresado}")
        print(f"      Dígito esperado : {digito_esperado}")
        resultado = "VÁLIDA" if es_valido else "INVÁLIDA"
        print(f"      Resultado: {resultado}")
    except ErrorEntrada as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
