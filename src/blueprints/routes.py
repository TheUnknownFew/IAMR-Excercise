from typing import Final

# auth:
REGISTER: Final = 'auth.register'
LOGIN: Final = 'auth.login'
LOGOUT: Final = 'auth.logout'

# inventory:
CREATE_BIN: Final = 'inventory.create_inventory_bin'
EDIT_BIN: Final = 'inventory.edit_inventory_bin'
REMOVE_BIN: Final = 'inventory.remove_inventory_bin'
DISPLAY_INVENTORY: Final = 'inventory.display_inventory'

# orders:
INDEX: Final = 'orders.index'
ADD_TO_CART: Final = 'orders.add_to_cart'
DISPLAY_CART: Final = 'orders.display_cart'
CHECKOUT: Final = 'orders.checkout'
