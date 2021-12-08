> Signup
- Vendors can sign up as a vendor of the market.
  - Vendors are signed up by being registered into the vendors table.
  - Vendors are assigned a unique id. For time's sake, this id will be the rowid assigned by the database.

> Inventory Management
- Vendors can add a bin.
  - A bin is identified as a pair involving the vendor id and the unique bin id.
  - A bin with a product is added to the bins table.

- Vendors can remove a bin.
  - A specified bin is removed from the bins table.

- Vendors can update the product of a bin.
  - A bin may have the name of its product changed.

- Vendors can update the stock of a bin.
  - A bin's product can increase or decrease.

- Vendors can update the unit price of a bin.
  - A bin's product unit price can be changed.

> Transactions
- Customers make an order from a vendor.
  - The vendor fulfills the order.

> Performance Analysis & Dashboard
- Vendors can request a report detailing sales made within a time range.
  - Displays total profit.
  - Displays total units sold.
  - Displays total units sold per bin.
- Dashboard will show pending transactions from customers that still need to be filled.
  - Will display difference in stock to show if the Vendor has to restock or can fill the order with the current stock.
  - Allow Vendors to fill orders.

> Advertisements
- Customers can sign up to a vendor's newsletter.
  - On purchase, customers are inquired to supply their email to subscribe to vendor newsletters.

- A newsletter is created when ever a product is updated.
  - Customers are notified of the following updates.
    - When a product is updated by a vendor they are subscribed to.
    - When a new bin is added by a vendor they are subscribed to.