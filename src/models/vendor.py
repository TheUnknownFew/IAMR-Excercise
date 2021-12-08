import json
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Union, Optional

from flask_login import login_required, current_user

import database
import models
from models import MarketMap, PriceCode, Bin
from errors import UniquenessError
from models.orders import Order, Transaction


@dataclass
class Vendor:
    vendor_id: int
    vendor_name: str
    vendor_email: str

    @login_required
    def get_all_orders(self) -> Optional[dict[Order, list[Transaction]]]:
        # Owner Required in order to perform this transaction.
        if self.vendor_id != Vendor.current_user().vendor_id:
            return None

        db = database.get_db()
        transaction_map: dict[Order, list[Transaction]] = {}
        order_items = db.execute(
            """
            SELECT orders.customer_id, orders.order_id, orders.order_filled, orders.order_filled_at FROM orders
                INNER JOIN transactions ON orders.order_id = transactions.order_id
                INNER JOIN bins ON transactions.bin_id = bins.bin_id
            WHERE bins.vendor_id = ?
            """,
            (self.vendor_id,)
        ).fetchall()
        orders = [Order(*data) for data in order_items]
        for order in orders:
            transaction_items = db.execute("""SELECT * FROM transactions WHERE order_id = ?""", (order.order_id,)).fetchall()
            transaction_map[order] = [Transaction(*data) for data in transaction_items]
        return transaction_map

    @login_required
    def create_bin(
            self,
            product_name: str,
            initial_stock: float,
            unit_price: float,
            price_code: PriceCode
    ) -> Optional[Bin]:
        """
        REQUIRES LOGIN AND AUTHENTICATION TO BE CALLED. WILL RETURN NONE IF UNAUTHORIZED!
        Adds a new bin for the vendor to the database. Returns the bin created or None if current vendor
        is unauthorized to create a bin.
        """
        # Owner Required in order to perform this transaction.
        if self.vendor_id != Vendor.current_user().vendor_id:
            return None

        bin_id = database.gen_uuid()
        params = (bin_id, self.vendor_id, product_name, initial_stock, unit_price, price_code.name)
        db = database.get_db()
        db.execute(
            """INSERT INTO bins(bin_id, vendor_id, product_name, stock, unit_price, price_code)
               VALUES (?, ?, ?, ?, ?, ?)""",
            params
        )
        db.commit()
        MarketMap.cache_stall(bin_id, self.vendor_id)
        return Bin(*params)

    @login_required
    def update_bin(
            self,
            bin_id: str, *,
            product_name: str = None,
            stock: float = None,
            price: tuple[float, PriceCode] = None
    ) -> Optional[Bin]:
        """
        REQUIRES LOGIN AND AUTHENTICATION TO BE CALLED. WILL RETURN NONE IF UNAUTHORIZED!
        Updates a bin a vendor owns with specified values to be replaced with.
        Returns the updated bin.
        Returns None if no update was made or the current vendor was not authorized to update a bin.
        """
        # Owner Required in order to perform this transaction.
        if self.vendor_id != Vendor.current_user().vendor_id:
            return None

        _bin = self.get_bin(bin_id)
        if _bin is None or not any((product_name, stock, price)):
            return None

        db = database.get_db()
        if product_name is not None:
            _bin.product_name = product_name
            db.execute(
                """UPDATE bins SET product_name = ? WHERE bin_id = ? AND vendor_id = ?""",
                (product_name, bin_id, self.vendor_id)
            )
        if stock is not None:
            _bin.stock = stock
            db.execute(
                """UPDATE bins SET stock = ? WHERE bin_id = ? AND vendor_id = ?""",
                (stock, bin_id, self.vendor_id)
            )
        if price is not None:
            unit_price, price_code = price
            _bin.unit_price = unit_price
            _bin.price_code = price_code
            db.execute(
                """UPDATE bins SET unit_price = ?, price_code = ? WHERE bin_id = ? AND vendor_id = ?""",
                (unit_price, price_code.name, bin_id, self.vendor_id)
            )
        db.commit()
        return _bin

    @login_required
    def remove_bin(self, bin_id: str) -> Optional[Bin]:
        """
        REQUIRES LOGIN AND AUTHENTICATION TO BE CALLED. WILL RETURN NONE IF UNAUTHORIZED!
        Removes a bin from the vendor.
        """
        # Owner Required in order to perform this transaction.
        if self.vendor_id != Vendor.current_user().vendor_id:
            return None

        _bin = self.get_bin(bin_id)
        if _bin is None:
            return None

        db = database.get_db()
        db.execute("""DELETE FROM bins WHERE bin_id = ? AND vendor_id = ?""", (_bin.bin_id, self.vendor_id))
        db.commit()
        MarketMap.dump_stall(_bin.bin_id, update_map=models.get_market_map())
        return _bin

    def get_bin(self, bin_id: str) -> Optional[Bin]:
        """Gets a bin belonging to vendor from given bin id."""
        bins = self.bins
        if bins is None:
            return None

        _bin = [b for b in bins if b.bin_id == bin_id]
        if len(_bin) == 0:
            return None
        if len(_bin) == 1:
            return _bin[0]
        # This should not be reached. Most likely handled by the database since bin_id is a primary key.
        raise UniquenessError(_bin, 'Queried for a single bin. Got multiple bins with the same id.')

    @property
    def bins(self) -> Optional[list[Bin]]:
        """
        Returns a list of bins belonging to the vendor.
        Returns None is current user is not authorized to view bins.
        """
        bins = database.get_db().execute("""SELECT * FROM bins WHERE vendor_id = ?""", (self.vendor_id,)).fetchall()
        return [Bin(*data) for data in bins]

    # ---------------------------------------
    # Flask-Login Required Definitions
    # ---------------------------------------

    @property
    def is_authenticated(self):
        """Flask-Login required implementation."""
        # Owner Required in order to perform this transaction.
        if self.vendor_id != Vendor.current_user().vendor_id:
            return False
        return True

    @property
    def is_active(self):
        """Flask-Login required implementation."""
        return True

    @property
    def is_anonymous(self):
        """Flask-Login required implementation."""
        return False

    def get_id(self) -> str:
        """Flask-Login required implementation."""
        return str(self.vendor_id)

    # ---------------------------------------
    # General Convenience methods.
    # ---------------------------------------

    @classmethod
    def get(cls, vendor_id: Optional[Union[str, int]]) -> Optional['Vendor']:
        """
        Gets vendor information from the database and serializes into a Vendor object.
        If no vendor exists with a given vendor id, None is returned.
        vendor_id: The vendor to access from the database.
        Returns A Vendor object or None if no vendor was found with a given Vendor id.

        Future considerations:
        - Omit email as that may be a security issue.
        """
        if vendor_id is None:
            return None
        vendor_data = database.get_db().execute(
            """SELECT vendor_id, vendor_name, vendor_email FROM vendors WHERE vendor_id = ?""", (int(vendor_id),)
        ).fetchone()
        return cls(*vendor_data) if vendor_data is not None else None

    @classmethod
    def get_all_vendors(cls) -> Optional[list['Vendor']]:
        """
        Future considerations:
        - Omit email as that may be a security issue.
        """
        vendor_data = database.get_db().execute("""SELECT vendor_id, vendor_name, vendor_email FROM vendors""").fetchall()
        return [cls(*data) for data in vendor_data] if len(vendor_data) > 0 else None

    @classmethod
    def current_user(cls) -> Optional['Vendor']:
        """Convenience function for accessing the current logged in vendor."""
        return cls.get(current_user.get_id())
