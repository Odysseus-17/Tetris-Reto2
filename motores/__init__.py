from .base import MotorAleatorio, semilla_por_reloj
from .cuadrado_medio import CuadradoMedio
from .congruencial import CongruencialLineal, cumple_hull_dobell
from .pcg import PCG32

# Lo que usa el juego para el menú y las teclas 1, 2, 3
MOTORES = {
    "1": CuadradoMedio,
    "2": CongruencialLineal,
    "3": PCG32,
}
