"""Modelo de datos (sección 12 del documento). Las columnas marcadas como «ampliación» no estaban
en el modelo preliminar y se agregaron porque el motor las necesita."""
import json
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Agricultor(Base):
    __tablename__ = "agricultor"
    id_agricultor: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    fecha_registro: Mapped[date] = mapped_column(Date, default=date.today)
    # --- ampliación: cartera del técnico ---
    documento: Mapped[str | None] = mapped_column(String(13), nullable=True)   # cédula
    comunidad: Mapped[str | None] = mapped_column(String(80), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(15), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    parcelas: Mapped[list["Parcela"]] = relationship(back_populates="agricultor", cascade="all, delete-orphan")


class Tecnico(Base):
    """Técnico agropecuario de territorio (MAG, GAD provincial, cooperativa, ONG)."""
    __tablename__ = "tecnico"
    id_tecnico: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    cargo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    institucion: Mapped[str | None] = mapped_column(String(120), nullable=True)
    canton_parroquia: Mapped[str | None] = mapped_column(String(120), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(15), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fecha_registro: Mapped[date] = mapped_column(Date, default=date.today)

    @property
    def firma(self) -> str:
        """«Ing. Ana Pérez – Técnica de extensión, MAG Chimborazo»"""
        extra = ", ".join(x for x in (self.cargo, self.institucion) if x)
        return self.nombre + (f" – {extra}" if extra else "")

    @property
    def contacto(self) -> str:
        return " · ".join(x for x in (self.telefono, self.correo) if x)


class Parcela(Base):
    __tablename__ = "parcela"
    id_parcela: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_agricultor: Mapped[int] = mapped_column(ForeignKey("agricultor.id_agricultor"))
    nombre: Mapped[str] = mapped_column(String(120))
    latitud: Mapped[float] = mapped_column(Float)
    longitud: Mapped[float] = mapped_column(Float)
    superficie: Mapped[float] = mapped_column(Float)  # hectáreas
    disponibilidad_agua: Mapped[str] = mapped_column(String(20))  # completo | turnos | secano
    pendiente: Mapped[float | None] = mapped_column(Float, nullable=True)  # % (None = no sabe)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    # --- ampliación ---
    problemas: Mapped[str] = mapped_column(Text, default="[]")  # lista JSON de claves de PROBLEMAS
    ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    textura: Mapped[str | None] = mapped_column(String(30), nullable=True)
    materia_organica: Mapped[float | None] = mapped_column(Float, nullable=True)
    poligono: Mapped[str | None] = mapped_column(Text, nullable=True)  # GeoJSON del contorno
    drenaje: Mapped[str | None] = mapped_column(String(15), nullable=True)  # rapido | normal | empoza
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    agricultor: Mapped[Agricultor] = relationship(back_populates="parcelas")
    historial: Mapped[list["HistorialCultivo"]] = relationship(back_populates="parcela", cascade="all, delete-orphan")
    planes: Mapped[list["PlanRotacion"]] = relationship(back_populates="parcela", cascade="all, delete-orphan")
    datos_ambientales: Mapped[list["DatoAmbiental"]] = relationship(back_populates="parcela", cascade="all, delete-orphan")

    @property
    def lista_problemas(self) -> list[str]:
        try:
            return json.loads(self.problemas or "[]")
        except ValueError:
            return []


class Cultivo(Base):
    __tablename__ = "cultivo"
    id_cultivo: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    ciclo_dias: Mapped[int] = mapped_column(Integer)
    necesidad_hidrica: Mapped[str] = mapped_column(String(10))  # baja | media | alta
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    # --- ampliación ---
    clave: Mapped[str] = mapped_column(String(40), unique=True)
    parametros: Mapped[str] = mapped_column(Text)  # JSON con todos los parámetros agronómicos
    personalizado: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def params(self) -> dict:
        return json.loads(self.parametros)


class HistorialCultivo(Base):
    __tablename__ = "historial_cultivo"
    id_historial: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_parcela: Mapped[int] = mapped_column(ForeignKey("parcela.id_parcela"))
    id_cultivo: Mapped[int] = mapped_column(ForeignKey("cultivo.id_cultivo"))
    fecha_siembra: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_cosecha: Mapped[date | None] = mapped_column(Date, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    parcela: Mapped[Parcela] = relationship(back_populates="historial")
    cultivo: Mapped[Cultivo] = relationship()


class PlanRotacion(Base):
    __tablename__ = "plan_rotacion"
    id_plan: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_parcela: Mapped[int] = mapped_column(ForeignKey("parcela.id_parcela"))
    fecha_generacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    alternativa: Mapped[str] = mapped_column(String(40))
    justificacion: Mapped[str] = mapped_column(Text)
    puntuacion: Mapped[float] = mapped_column(Float)  # indicador comparativo del modelo (0-100)
    # --- ampliación ---
    secuencia: Mapped[str] = mapped_column(Text)  # claves de cultivos separadas por coma
    confianza: Mapped[str] = mapped_column(String(10))  # Alta | Media | Baja
    escenario: Mapped[str | None] = mapped_column(String(30), nullable=True)
    detalle: Mapped[str] = mapped_column(Text)  # JSON con puntajes, ciclos y trazabilidad
    id_tecnico: Mapped[int | None] = mapped_column(ForeignKey("tecnico.id_tecnico"), nullable=True)  # técnico responsable
    tipo: Mapped[str | None] = mapped_column(String(15), nullable=True)  # anual | rotacion

    parcela: Mapped[Parcela] = relationship(back_populates="planes")


class DatoAmbiental(Base):
    __tablename__ = "datos_ambientales"
    id_dato: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_parcela: Mapped[int] = mapped_column(ForeignKey("parcela.id_parcela"))
    fuente: Mapped[str] = mapped_column(String(40))
    variable: Mapped[str] = mapped_column(String(40))
    valor: Mapped[float] = mapped_column(Float)
    unidad: Mapped[str] = mapped_column(String(20))
    fecha_dato: Mapped[date] = mapped_column(Date, default=date.today)

    parcela: Mapped[Parcela] = relationship(back_populates="datos_ambientales")
