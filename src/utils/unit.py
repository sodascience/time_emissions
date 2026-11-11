from __future__ import annotations

import polars as pl
from dataclasses import dataclass, field

from .helpers import _label, Named


class Unit(frozenset):
    """A set of Keys: what one row is."""

    def __new__(cls, *keys: Key) -> Unit:
        return super().__new__(cls, keys)
    
    @property
    def cols(self) -> list[str]:
        """The key column names, sorted: what Polars joins, groups and selects on."""
        return sorted(k.name for k in self)
    
    # set operations stay Units, so .cols works on their results too
    def __or__(self, other):    return Unit(*frozenset.__or__(self, other))
    def __and__(self, other):   return Unit(*frozenset.__and__(self, other))
    def __sub__(self, other):   return Unit(*frozenset.__sub__(self, other))

    def __repr__(self) -> str:
        """The unit as its named building blocks, e.g. PERSON | HH_SPELL | MONTH."""
        import config.units as units
        blocks = sorted(((n, u) for n, u in vars(units).items() if isinstance(u, Unit) and u),
                        key = lambda item: -len(item[1]))           # largest first: MONTH before YEAR
        parts, left = [], set(self)
        for name, block in blocks:
            if block <= left:
                parts.append(name)
                left -= block
        parts.sort(key = lambda n: n in ("YEAR", "MONTH"))          # entities first, time last
        parts += sorted(k.name for k in left)                       # keys no block covers
        return " | ".join(parts) or "Unit()"



@dataclass(eq = False)              # eq = False: hashable by identity
class Key(Named):
    "A key column: in many datasets, owned by none"

    # fields
    dtype: pl.DataType
    format: str = "%Y%m%d"              # dates only: how the date is written
    description: str = ""
    codebook: dict[str, str | None] = field(default_factory = dict) # CBS code -> value; None = missing
    name: str | None = None

    def __repr__(self) -> str:
        return _label(kind = "Key", name = self.name, dtype = self.dtype,
                      description = self.description)
