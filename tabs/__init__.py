from .revenue import render_revenue_tab
from .customer import render_customer_tab
from .product import render_product_tab
from .discount_promo import render_discount_promo_tab
from .shipping import render_shipping_tab
from .geographic import render_geographic_tab
from .payment import render_payment_tab
from .advanced import render_advanced_tab
from .ai_sql import render_ai_sql_tab

__all__ = [
    "render_revenue_tab",
    "render_customer_tab",
    "render_product_tab",
    "render_discount_promo_tab",
    "render_shipping_tab",
    "render_geographic_tab",
    "render_payment_tab",
    "render_advanced_tab",
    "render_ai_sql_tab",
]
