"""Clientes de fuentes externas. Cada función lanza ServicioNoDisponible si la fuente falla."""


class ServicioNoDisponible(Exception):
    """La fuente externa no respondió o devolvió datos incompletos (RF-15)."""
