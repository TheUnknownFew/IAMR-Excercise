PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id INTEGER PRIMARY KEY,      -- Primary key: vendor unique identifier
    vendor_name TEXT NOT NULL,          -- Company Name of the vendor
    vendor_secret TEXT NOT NULL,        -- Vendor login password
    vendor_email TEXT NOT NULL UNIQUE   -- Vendor company email. doubles as login username.
--  promoted BOOL -- Could be added to promote this vendor's products on the home page.
);

CREATE TABLE IF NOT EXISTS bins (
    bin_id TEXT NOT NULL,               -- UUID: bin unique identifier
    vendor_id INT NOT NULL,             -- The id of the vendor that owns the bin
    product_name TEXT NOT NULL,         -- The name of the product stored in the bin
    stock FLOAT NOT NULL,               -- The amount of stock in the bin
    unit_price FLOAT NOT NULL,          -- The price of an individual/amount of stock. e.g. price per unit (i.e $/lb)
    price_code TEXT NOT NULL,           -- The currency type
    PRIMARY KEY(bin_id, vendor_id),
    FOREIGN KEY(vendor_id) REFERENCES vendors(vendor_id)
);

CREATE TABLE IF NOT EXISTS market_map (
    -- bin id pairs consist of an edge on the map. The map is undirected
    -- so a duplicate edge with the bin ids swapped should not be found in this table.
    vendor_bin_id TEXT NOT NULL,        -- The bin connecting to the next bin -> undirected
    neighbor_bin_id TEXT NOT NULL,      -- The bin connecting to the previous bin -> undirected
    unit_distance FLOAT NOT NULL,       -- The distance between the two bins.
--  distance_code TEXT NOT NULL, -- add in to enable distance typing. current unit is in ft. as a standard unit.
    PRIMARY KEY(vendor_bin_id, neighbor_bin_id),
    FOREIGN KEY(vendor_bin_id) REFERENCES bins(bin_id),
    FOREIGN KEY(neighbor_bin_id) REFERENCES bins(bin_id)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,               -- The generated UUID of a customer
    name TEXT,                                  -- The name of the customer if provided
    email TEXT,                                 -- The email of the customer if provided
    newsletter_subscription BOOLEAN NOT NULL    -- Indicator if the customer should receive newsletter emails.
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,                  -- The generated UUID of an order
    customer_id TEXT NOT NULL,                  -- The customer that the order belongs to
    order_filled BOOLEAN NOT NULL,              -- Indicates if all of the transactions in the order have been filled.
    order_filled_at DATETIME,                   -- Time of when the last transaction has been filled.
    FOREIGN KEY(customer_id) REFERENCES customer(customer_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    -- Used as a store of all transactions from customers.

    -- Other consideration: possibly store price of item and item purchased instead of the bin id
    -- at the time of purchase to retain sales information regarding the transaction in case information
    -- changes before a vendor goes to generate an analysis report.

    order_id TEXT NOT NULL,                 -- The id of the order. Used to identify the customer as well.
    bin_id TEXT NOT NULL,                   -- The id of the bin. Used to identify the product purchased and what vendor was purchased from
    units_purchased FLOAT NOT NULL,         -- Units of the corresponding bin purchased
    transaction_filled BOOLEAN NOT NULL,    -- Indicator if an individual transaction of an order has been filled.
    time_of_sale DATETIME NOT NULL,         -- Time of transaction.
    transaction_filled_at DATETIME,         -- Indicates when the vendor completed filling this single transaction. Can be used in conjunction with time_of_purchase
                                            -- to find the average time it takes for a vendor to fill an order.
    PRIMARY KEY(order_id, bin_id),
    FOREIGN KEY(order_id) REFERENCES orders(order_id),
    FOREIGN KEY(bin_id) REFERENCES bins(bin_id)
);