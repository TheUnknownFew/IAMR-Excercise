from dataclasses import dataclass, field, astuple
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

import database
from models.bin import Bin


class CartItem(BaseModel):
    item_bin: Bin
    quantity: float


# Note: Uses Pydantic BaseModel for the convenience of Obj.parse_obj(...).
# Serializing and de-serializing from flask session and form data becomes easier
# since basic dataclasses do not provide any functionality for de-serializing complex,
# nested types.
# Doubles as an intermediate customer who has yet to place a single order.
class CustomerCart(BaseModel):
    customer_id: str = Field(default_factory=database.gen_uuid)
    cart_items: dict[str, CartItem] = Field(default_factory=dict)

    @property
    def cart_total(self):
        return sum(cart_item.item_bin.unit_price * cart_item.quantity for cart_item in self.cart_items.values())


@dataclass
class Customer:
    customer_id: str
    name: Optional[str] = field(default=None, compare=False)
    email: Optional[str] = field(default=None, compare=False)
    newsletter_subscription: bool = field(default=False, compare=False)

    def tuple(self):
        """Convert to tuple so this can be inserted into the database."""
        return astuple(self)


@dataclass(unsafe_hash=True)
class Order:
    customer_id: str
    order_id: str = field(default_factory=database.gen_uuid)
    order_filled: bool = field(default=False)
    order_filled_at: datetime = field(default=None)

    def __post_init__(self):
        self.order_filled = bool(self.order_filled)

    def tuple(self):
        """Convert to tuple so this can be inserted into the database."""
        return astuple(self)


@dataclass
class Transaction:
    order_id: str
    bin_id: str
    units_purchased: float
    transaction_filled: bool = field(default=False)
    time_of_sale: datetime = field(default_factory=datetime.now, compare=False)
    transaction_filled_at: datetime = field(default=None, compare=False)

    def tuple(self):
        """Convert to tuple so this can be inserted into the database."""
        return astuple(self)
