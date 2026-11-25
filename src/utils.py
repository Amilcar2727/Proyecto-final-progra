"""
Módulo de utilidades transversales para OptiFin.
Proporciona semillas reproducibles, formateo de métricas y validaciones numéricas.
"""

import random
import time
from typing import Any, Callable, Dict, Optional


def fijar_semilla(seed: int = 42) -> None:
    """
    Fija la semilla en el generador pseudoaleatorio de Python para reproducibilidad.

    Args:
        seed: Valor entero de la semilla (por defecto 42).
    """
    random.seed(seed)


def medir_tiempo_y_memoria(
    funcion: Callable[..., Any], *args: Any, **kwargs: Any
) -> Dict[str, Any]:
    """
    Ejecuta una función midiendo el tiempo de pared (perf_counter)
    y retorna el resultado junto con las métricas computacionales.

    Args:
        funcion: Función invocable.
        *args: Argumentos posicionales.
        **kwargs: Argumentos por nombre.

    Returns:
        Diccionario con 'resultado', 'tiempo_segundos' y 'tiempo_ms'.
    """
    inicio = time.perf_counter()
    resultado = funcion(*args, **kwargs)
    fin = time.perf_counter()
    duracion = fin - inicio
    return {
        "resultado": resultado,
        "tiempo_segundos": duracion,
        "tiempo_ms": duracion * 1000.0,
    }


def formatear_monto(monto: float, moneda: str = "USD") -> str:
    """Formatea cantidades monetarias con separador de miles."""
    return f"{monto:,.2f} {moneda}"


def formatear_porcentaje(valor: float) -> str:
    """Formatea valores en escala [0, 1] a porcentaje legible."""
    return f"{valor * 100:.2f}%"
