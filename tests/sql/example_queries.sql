-- -- -- Vendor Queries:
-- Example vendor signup.
INSERT INTO vendors(vendor_name, vendor_secret, vendor_email) VALUES ('Vendor A', 'password', 'vendor.a@email.com');

------

-- -- -- Inventory Management Queries:
-- -- Individual Bin Management:
-- Example add bin. (initialization of a new bin inside of the bins table)
-- A new bin identified as bin 1 from vendor 1 has a stock of 10 apples that cost $2.
INSERT INTO bins(bin_id, vendor_id, product_name, stock, unit_price, price_code)
VALUES (1, 1, 'apple', 10, 2.0, 'USD');

-- Example of retrieving a bin.
-- Retrieves bin 1 belonging to vendor 1.
SELECT * FROM bins WHERE bin_id = 1 AND vendor_id = 1;

-- Example remove bin. (removes a bin that is no longer being supplied by a vendor)
-- Removes bin 1 from vendor 1. Considerations: Other considerations would have to be made so that
-- a vendor cannot delete another vendor's bin.
DELETE FROM bins WHERE bin_id = 1 AND vendor_id = 1;

-- Example update product in a bin.
-- Potential Python code for updating the table.
/*
def update_bin(product: str = None, stock: int = None, price: tuple[float, PriceCode] = None):
    # cannot update the bin if no values are provided.
    if not all(product, stock, price):
        return

    db = database.get_db()
    # self.bin and self.vendor are placeholders for final design considerations.
    if product:
        db.execute(
        """UPDATE bins SET product_name = ? WHERE bin_id = ? AND vendor_id = ?""",
        (product, self.bin, self.vendor)
        )
    if stock:
        db.execute(
        """UPDATE bins SET stock = ? WHERE bin_id = ? AND vendor_id = ?""",
        (stock, self.bin, self.vendor)
        )
    if price:
        db.execute(
        """UPDATE bins SET unit_price = ?, price_code = ? WHERE bin_id = ? AND vendor_id = ?""",
        (*price, self.bin, self.vendor)
        )
    db.commit()
*/
-- Updates the product name of a bin belonging to vendor 1 in bin 1.
UPDATE bins SET product_name = 'new_product' WHERE bin_id = 1 AND vendor_id = 1;

-- Updates the stock in bin 1 owned by vendor 1 to 10.
UPDATE bins SET stock = 10 WHERE bin_id = 1 AND vendor_id = 1;

-- Updates the price of the product in bin 1 owned by vendor 1 to $5.
UPDATE bins SET unit_price = 5, price_code = 'USD' WHERE bin_id = 1 AND vendor_id = 1;

-- -- Bin Statistics:

------

-- -- Transaction Manager:

------

-- -- Vendor Performance Queries:

------