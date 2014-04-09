====================
Comercio electrónico
====================

**eSale** es el módulo base de cualquier herramienta de comercio electrónico.
En este módulo se definen las vistas y algunas acciones (botones) para la
importación de pedidos de terceras aplicaciones (Magento, Presta Shop, ...)

La gestión de las tiendas virtuales lo haremos mediante las Tiendas que permite a Tryton
definir y usar varias tiendas de la empresa. Antes de proceder el uso de la tienda 
de comercio electrónico consulte la documentación de roles y usuarios de multi tiendas.

.. inheritref:: esale/esale:section:pedidos

Importar pedidos
----------------

Las tiendas **Tryton eSale** no necesitan descargar los pedidos ya
que se generan insitu en el mismo ERP.

Para la importación de pedidos para tiendas externas (Magento, Prestashop...) al ERP,
dispone de botones para la importación de pedidos según un intérvalo de fechas.
Para la importar los pedidos accede a la tienda que desea importar.

.. inheritref:: esale/esale:section:estados

Exportar estados (pedidos)
--------------------------

Las tiendas **Tryton eSale** no necesitan exportar los estados de los pedidos ya
que se consultan insitu en el mismo ERP.

Para la exportación de estados de pedido para tiendas externas (Magento, Prestashop...),
dispone de botones para la exportación de estados según un intérvalo de fechas.
Para la exportar los estados accede a la tienda que desea exportar.

.. inheritref:: esale/esale:section:stock

Exportar stock
--------------

Las tiendas **Tryton eSale** no necesitan exportar el stock de los productos ya
que se consultan insitu en el mismo ERP.

Para la exportación de stocks para tiendas externas (Magento, Prestashop...),
dispone de botones para la exportación de precios productos según un intérvalo de fechas.
Para la exportar los stocks accede a la tienda que desea exportar.

.. inheritref:: esale/esale:section:productos

Exportar productos
------------------

Las tiendas **Tryton eSale** no necesitan exportar los productos ya que se consultan insitu 
en el mismo ERP.

Para la exportación de productos para tiendas externas (Magento, Prestashop...),
dispone de botones para la exportación de productos según un intérvalo de fechas.
Para la exportar los productos accede a la tienda que desea exportar.

.. inheritref:: esale/esale:section:precios

Exportar precios
----------------

Las tiendas **Tryton eSale** no necesitan exportar los precios de los productos ya
que se consultan insitu en el mismo ERP. Los precios de los productos se muestran según
precios del producto y tarifas de precios.

Para la exportación de precios de productos para tiendas externas (Magento, Prestashop...),
dispone de botones para la exportación de precios productos según un intérvalo de fechas.
Para la exportar los productos accede a la tienda que desea exportar.

.. inheritref:: esale/esale:section:acciones_planificadas

Acciones planificadas
---------------------

Se dispone de acciones planificadas para la repetición de ciertas
importaciones/exportaciones se vayan realizando cada cierto tiempo

----------------
Importar pedidos
----------------

Permite importar los pedidos cada cierto tiempo. Para activar esta opción
deberá configurar en la tienda que permite la opción de "Planificador de tareas".

Recuerde que el usuario "Cron eSale" (user_cron_internal_esale) disponga permisos
de acceso a las tiendas como del grupo de Ventas, Administración ventas y eSale.

--------------------------
Exportar estados (pedidos)
--------------------------

Permite exportar los pedidos cada cierto tiempo. Para activar esta opción
deberá configurar en la tienda que permite la opción de "Planificador de tareas".

Recuerde que el usuario "Cron eSale" (user_cron_internal_esale) disponga permisos
de acceso a las tiendas como del grupo de Ventas, Administración ventas y eSale.

.. inheritref:: esale/esale:section:configuracion

Configuración
-------------

La configuración de la tienda electrónica se realizará a través del menú 
|menu_sale_shop|.

.. |menu_sale_shop| tryref:: sale_shop.menu_sale_shop/complete_name

Al establecer que una tienda esté disponible como canal de comercio
electrónico, aparecerá una nueva pestaña con la información/configuración. A
medida que vaya instalando módulos las opciones van incrementando en esta
sección.

* Acciones: Dispondrá de botones para la importación/exportación de datos
  de Tryton a la tienda electrónica

  * Pedidos
  
* Configuración: Configuración de la tienda

  * General: Configuraciones generales
  
    * Impuestos incluidos
    * Buscar tercero por CIF/NIF. Si el cliente está ya dado de alta en Tryton,
      no lo va a crear (busca por CIF/NIF)
    * Producto entrega
    * Producto descuento
    * Precio: Precio venta o por tarifa
    * Planificador de tareas. Los crons de esta tienda se activarán (importación
      pedidos, exportar stoc...)

  * Países: Países que se permite la venta de esta tienda.
  * Idiomas: Idiomas que se dispone esta tienda y idioma por defecto

.. note:: Manualmente no podrá crear tiendas. Para crear y activar tiendas externas 
          tipo Magento, Prestashop, etc... consulte la documentación de cada módulo
          concreto (`Magento <../magento/index.html>`_).

.. note:: Antes de sincronizar los parámetros de una tienda externa a Tryton,
          asegúrese que en la configuración de ventas disponga de valores por
          defecto para que se usen estos cuando se generen las nuevas tiendas
          (producto entrega, producto descuento, unidad medida,...).

.. note:: Si trabaja en multimoneda o su tienda trabaja en otra moneda diferente
          de la compañía, recuerde de añadir las tasas de cambio actuales.
