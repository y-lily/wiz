from decimal import Decimal, DecimalTuple
from typing import TypeAlias


SupportsDecimal: TypeAlias = Decimal | str | int | float | DecimalTuple
