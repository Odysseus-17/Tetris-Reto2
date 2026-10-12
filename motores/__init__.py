from .base import MotorAleatorio, semilla_por_reloj
from .cuadrado_medio import CuadradoMedio
from .congruencial import CongruencialLineal, cumple_hull_dobell
from .pcg import PCG32
from .xoshiro import Xoshiro256

# Lo que usa el juego para el menú y las teclas 1, 2, 3, 4
MOTORES = {
    "1": CuadradoMedio,
    "2": CongruencialLineal,
    "3": PCG32,
    "4": Xoshiro256,
}
