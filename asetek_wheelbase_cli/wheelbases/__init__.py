# flake8: noqa F401

from enum import StrEnum
from ._base import HidData, WheelbaseConfiguration, WheelbaseDefinition
from .la_prima import la_prima_wheelbase

WHEELBASE_DEFINITIONS = [
    la_prima_wheelbase
]
