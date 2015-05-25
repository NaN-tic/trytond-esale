====================
Comercio electrónico
====================

**eSale** es el módulo base de cualquier herramienta de comercio electrónico.
En este módulo se definen las vistas y algunas acciones (botones) para la
importación de pedidos de terceras aplicaciones (Magento, Prestashop, Amazon, 
Drupal Commerce, Shopify...)

Consulta stock API
------------------

Se dispone de un método para la consulta de stock via API

Método:

model.product.product.get_esale_product_quantity

Parámetros:

- codes: lista de códigos
- quantity o forecast_quantity (parámetro opcional. Por defecto, quantity)
