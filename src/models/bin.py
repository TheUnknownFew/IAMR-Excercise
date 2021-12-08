import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Union


class PriceCode(str, Enum):
    """
    Notes & Considerations:
    These price codes can be expanded manually here in the PriceCode enum class, or price codes
    could be added to a 'codes' table within the database.
    The former would allow for theoretical administration access to expand the supported codes on
    the fly by the web applications.

    For the time being, an enum is being used for time's sake.
    """

    USD = 'USD'
    EURO = 'EUR'
    YEN = 'YEN'


def price_codes() -> list[str]:
    """Convenience function for accessing all the PriceCode enums as a list of strings."""
    return [c.value for c in PriceCode]


@dataclass
class Bin:
    bin_id: str
    vendor_id: int
    product_name: str
    stock: float
    unit_price: float
    price_code: Union[PriceCode, str]

    @property
    def json_str(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_string: str):
        return cls(**json.loads(json_string))

    def __post_init__(self):
        if isinstance(self.price_code, str):
            self.price_code = PriceCode[self.price_code]
