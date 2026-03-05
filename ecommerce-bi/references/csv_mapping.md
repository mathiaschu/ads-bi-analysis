# CSV Column Mapping Reference - eCommerce BI

Mapeo de columnas desde exports de plataformas eCommerce a nombres canonicos internos usados por el script de analisis.

---

## Columnas Canonicas

Estas son las columnas internas que usa el script de analisis, independientemente de la plataforma de origen.

| Nombre Canonico | Descripcion |
|---|---|
| `order_id` | Identificador unico de la orden |
| `email` | Email del cliente |
| `date` | Fecha de la orden (campo de fecha principal) |
| `order_status` | Estado de la orden (open, closed, cancelled, etc.) |
| `payment_status` | Estado del pago (paid, pending, refunded, etc.) |
| `shipping_status` | Estado del envio |
| `currency` | Codigo de moneda (ej: ARS, USD) |
| `subtotal` | Subtotal antes de descuentos y envio |
| `discount` | Monto de descuento aplicado |
| `shipping_cost` | Costo de envio |
| `total` | Total de la orden |
| `customer_name` | Nombre del comprador |
| `phone` | Telefono del comprador |
| `shipping_address` | Direccion completa de envio |
| `city` | Ciudad |
| `state` | Provincia o estado |
| `country` | Pais |
| `zip_code` | Codigo postal |
| `shipping_method` | Nombre del medio de envio |
| `payment_method` | Nombre del medio de pago |
| `coupon` | Codigo de cupon de descuento |
| `payment_date` | Fecha en que se confirmo el pago |
| `shipping_date` | Fecha en que se despacho el envio |
| `product_name` | Nombre del producto (nivel linea de pedido) |
| `product_price` | Precio unitario del producto |
| `product_qty` | Cantidad del producto |
| `sku` | Codigo SKU |
| `channel` | Canal de venta (web, mobile, POS, etc.) |
| `cancellation_date` | Fecha y hora de cancelacion |
| `cancellation_reason` | Motivo de cancelacion |

---

## Plataformas

---

### Tiendanube

#### Fingerprint de deteccion

Columnas unicas que identifican este export (basta con encontrar 2 o mas):

- `"Número de orden"`
- `"Estado de la orden"`
- `"Subtotal de productos"`
- `"Nombre del comprador"`
- `"Provincia o estado"`

#### Parametros de parsing

| Parametro | Valor |
|---|---|
| Separador | `;` (punto y coma) |
| Encoding | `latin-1` (ISO-8859-1) |
| Header row | Primera fila |
| Formato fecha | `DD/MM/YYYY HH:MM` |
| Separador decimal | `.` (punto) — aunque puede aparecer con coma, normalizar |
| Separador de miles | ninguno o espacio |

#### Mapeo de columnas

| Header Original (Tiendanube) | Nombre Canonico | Notas |
|---|---|---|
| `Número de orden` | `order_id` | |
| `Email` | `email` | |
| `Fecha` | `date` | Formato: DD/MM/YYYY HH:MM |
| `Estado de la orden` | `order_status` | Ver valores abajo |
| `Estado del pago` | `payment_status` | Ver valores abajo |
| `Estado del envío` | `shipping_status` | |
| `Moneda` | `currency` | |
| `Subtotal de productos` | `subtotal` | Puede traer coma como decimal, normalizar |
| `Descuento` | `discount` | |
| `Costo de envío` | `shipping_cost` | |
| `Total` | `total` | |
| `Nombre del comprador` | `customer_name` | |
| `Teléfono` | `phone` | |
| `Dirección` | `shipping_address` | |
| `Ciudad` | `city` | |
| `Código postal` | `zip_code` | |
| `Provincia o estado` | `state` | |
| `País` | `country` | |
| `Medio de envío` | `shipping_method` | |
| `Medio de pago` | `payment_method` | |
| `Cupón de descuento` | `coupon` | |
| `Fecha de pago` | `payment_date` | Mismo formato que date |
| `Fecha de envío` | `shipping_date` | Mismo formato que date |
| `Nombre del producto` | `product_name` | Columna de linea de pedido |
| `Precio del producto` | `product_price` | |
| `Cantidad del producto` | `product_qty` | |
| `SKU` | `sku` | |
| `Canal` | `channel` | |
| `Fecha y hora de cancelación` | `cancellation_date` | |
| `Motivo de cancelación` | `cancellation_reason` | |

#### Columnas extra (no canonicas, preservar si estan presentes)

| Header Original | Nombre Extra | Descripcion |
|---|---|---|
| `DNI / CUIT` | `tax_id` | Documento fiscal del comprador |
| `Nombre para el envío` | `shipping_name` | Nombre del destinatario |
| `Teléfono para el envío` | `shipping_phone` | Telefono del destinatario |
| `Número` | `address_number` | Numero de calle |
| `Piso` | `address_floor` | Piso / departamento |
| `Localidad` | `locality` | Localidad (a veces difiere de ciudad) |
| `Notas del comprador` | `buyer_notes` | |
| `Notas del vendedor` | `seller_notes` | |
| `Código de tracking del envío` | `tracking_code` | |
| `Identificador de la transacción en el medio de pago` | `payment_transaction_id` | |
| `Identificador de la orden` | `order_identifier` | ID alternativo interno |
| `Producto Físico` | `physical_product` | Boolean: si el producto es fisico |
| `Persona que registró la venta` | `registered_by` | |
| `Sucursal de venta` | `store_branch` | |
| `Vendedor` | `seller` | |

#### Valores de estado (Tiendanube → canonico)

**order_status:**

| Valor original | Valor canonico |
|---|---|
| `Abierta` | `open` |
| `Cerrada` | `closed` |
| `Cancelada` | `cancelled` |

**payment_status:**

| Valor original | Valor canonico |
|---|---|
| `Pagado` | `paid` |
| `Pendiente` | `pending` |
| `Reembolsado` | `refunded` |
| `Abandonado` | `abandoned` |

**shipping_status:** valores habituales (pueden variar segun configuracion del merchant):

| Valor original | Valor canonico |
|---|---|
| `Sin envío` | `no_shipping` |
| `Pendiente` | `pending` |
| `En preparacion` | `preparing` |
| `Despachado` | `shipped` |
| `Entregado` | `delivered` |
| `Vuelto al remitente` | `returned` |

---

### Shopify

#### Fingerprint de deteccion

Columnas unicas que identifican este export (basta con encontrar 2 o mas):

- `"Name"` (con formato `#1001`, `#1002`, etc.)
- `"Financial Status"`
- `"Fulfillment Status"`
- `"Lineitem name"`
- `"Lineitem quantity"`

#### Parametros de parsing

| Parametro | Valor |
|---|---|
| Separador | `,` (coma) |
| Encoding | `utf-8` |
| Header row | Primera fila |
| Formato fecha | `YYYY-MM-DD HH:MM:SS UTC` o `YYYY-MM-DD HH:MM:SS +0000` |
| Separador decimal | `.` (punto) |
| Separador de miles | ninguno |

#### Mapeo de columnas

| Header Original (Shopify) | Nombre Canonico | Notas |
|---|---|---|
| `Name` | `order_id` | Incluye el `#` delante, ej: `#1001` |
| `Email` | `email` | |
| `Created at` | `date` | Formato ISO con timezone |
| `Financial Status` | `payment_status` | Ver valores abajo |
| `Fulfillment Status` | `shipping_status` | Ver valores abajo |
| `Currency` | `currency` | |
| `Subtotal` | `subtotal` | |
| `Discount Amount` | `discount` | |
| `Shipping` | `shipping_cost` | |
| `Total` | `total` | |
| `Billing Name` | `customer_name` | |
| `Billing Phone` | `phone` | |
| `Shipping Street` | `shipping_address` | |
| `Shipping City` | `city` | |
| `Shipping Province` | `state` | |
| `Shipping Country` | `country` | |
| `Shipping Zip` | `zip_code` | |
| `Shipping Method` | `shipping_method` | Puede estar vacio |
| `Payment Method` | `payment_method` | |
| `Discount Code` | `coupon` | |
| `Paid at` | `payment_date` | |
| `Fulfilled at` | `shipping_date` | Aproximacion; es fecha de fulfillment |
| `Lineitem name` | `product_name` | |
| `Lineitem price` | `product_price` | |
| `Lineitem quantity` | `product_qty` | |
| `Lineitem sku` | `sku` | |
| `Source` | `channel` | Ej: web, mobile, pos |
| `Cancelled at` | `cancellation_date` | |
| `Cancel Reason` | `cancellation_reason` | |

#### Columnas extra comunes en Shopify

| Header Original | Nombre Extra |
|---|---|
| `Id` | `shopify_order_id` |
| `Financial Status` | — (mapeado a payment_status) |
| `Taxes` | `taxes` |
| `Tax 1 Name` | `tax_1_name` |
| `Tax 1 Value` | `tax_1_value` |
| `Billing Street` | `billing_address` |
| `Billing City` | `billing_city` |
| `Billing Province` | `billing_state` |
| `Billing Country` | `billing_country` |
| `Billing Zip` | `billing_zip` |
| `Note` | `buyer_notes` |
| `Vendor` | `vendor` |
| `Tags` | `tags` |
| `Risk Level` | `risk_level` |
| `Lineitem compare at price` | `product_compare_price` |
| `Lineitem requires shipping` | `product_requires_shipping` |
| `Lineitem taxable` | `product_taxable` |
| `Lineitem fulfillment status` | `lineitem_fulfillment_status` |

#### Valores de estado (Shopify → canonico)

**payment_status (Financial Status):**

| Valor original | Valor canonico |
|---|---|
| `paid` | `paid` |
| `pending` | `pending` |
| `refunded` | `refunded` |
| `partially_refunded` | `partially_refunded` |
| `authorized` | `authorized` |
| `voided` | `voided` |

**shipping_status (Fulfillment Status):**

| Valor original | Valor canonico |
|---|---|
| `fulfilled` | `shipped` |
| `partial` | `partially_shipped` |
| `unfulfilled` | `pending` |
| (vacio) | `pending` |
| `restocked` | `returned` |

**order_status:** Shopify no exporta un campo de orden status directo. Se infiere:
- Si `Cancelled at` tiene valor → `cancelled`
- Si `Financial Status` = `paid` y `Fulfillment Status` = `fulfilled` → `closed`
- Resto → `open`

---

### WooCommerce

#### Fingerprint de deteccion

Columnas unicas que identifican este export (basta con encontrar 2 o mas):

- `"Order ID"` (numerico sin prefijo)
- `"Order Status"` con valores tipo `wc-completed`, `wc-processing`, etc.
- `"Billing First Name"` + `"Billing Last Name"` (separados)
- `"Payment Method Title"`

#### Parametros de parsing

| Parametro | Valor |
|---|---|
| Separador | `,` (coma) |
| Encoding | `utf-8` |
| Header row | Primera fila |
| Formato fecha | `YYYY-MM-DD HH:MM:SS` |
| Separador decimal | `.` (punto) |
| Separador de miles | ninguno |

#### Mapeo de columnas

| Header Original (WooCommerce) | Nombre Canonico | Notas |
|---|---|---|
| `Order ID` | `order_id` | |
| `Billing Email` | `email` | |
| `Order Date` | `date` | |
| `Order Status` | `order_status` | Ver valores abajo; tambien infiere payment_status |
| `Currency` | `currency` | |
| `Order Subtotal Amount` | `subtotal` | |
| `Coupon Discount Amount` | `discount` | |
| `Order Shipping Amount` | `shipping_cost` | |
| `Order Total Amount` | `total` | |
| `Billing First Name` + `Billing Last Name` | `customer_name` | Concatenar con espacio |
| `Billing Phone` | `phone` | |
| `Billing Address 1` | `shipping_address` | WooCommerce separa billing y shipping; usar shipping si esta disponible |
| `Billing City` | `city` | Preferir `Shipping City` si existe |
| `Billing State` | `state` | Preferir `Shipping State` si existe |
| `Billing Country` | `country` | Preferir `Shipping Country` si existe |
| `Billing Postcode` | `zip_code` | Preferir `Shipping Postcode` si existe |
| `Shipping Method Title` | `shipping_method` | |
| `Payment Method Title` | `payment_method` | |
| `Coupon Code` | `coupon` | |
| `Order Date Paid` | `payment_date` | |
| `SKU` | `sku` | Puede estar como columna separada o dentro de items |
| `Item Name` | `product_name` | |
| `Item Cost` | `product_price` | |
| `Quantity` | `product_qty` | |

#### Columnas extra comunes en WooCommerce

| Header Original | Nombre Extra |
|---|---|
| `Shipping First Name` | `shipping_first_name` |
| `Shipping Last Name` | `shipping_last_name` |
| `Shipping Address 1` | `shipping_address_1` |
| `Shipping Address 2` | `shipping_address_2` |
| `Shipping City` | `shipping_city` |
| `Shipping State` | `shipping_state` |
| `Shipping Country` | `shipping_country` |
| `Shipping Postcode` | `shipping_zip` |
| `Customer Note` | `buyer_notes` |
| `Transaction ID` | `payment_transaction_id` |
| `Order Notes` | `seller_notes` |
| `Refund Amount` | `refund_amount` |

#### Valores de estado (WooCommerce → canonico)

**order_status (Order Status):**

| Valor original | Valor canonico | payment_status inferido |
|---|---|---|
| `wc-completed` o `completed` | `closed` | `paid` |
| `wc-processing` o `processing` | `open` | `paid` |
| `wc-on-hold` o `on-hold` | `open` | `pending` |
| `wc-pending` o `pending` | `open` | `pending` |
| `wc-cancelled` o `cancelled` | `cancelled` | `voided` |
| `wc-refunded` o `refunded` | `closed` | `refunded` |
| `wc-failed` o `failed` | `cancelled` | `failed` |

WooCommerce no tiene un campo separado de payment_status en el export estandar; se infiere desde order_status.

---

## Deteccion automatica de plataforma

El script detecta la plataforma inspeccionando los headers del CSV antes de parsear datos.

### Algoritmo de deteccion

1. Leer la primera fila del archivo (headers)
2. Normalizar: strip de espacios, lowercase para comparacion
3. Buscar coincidencias con fingerprints de cada plataforma
4. Seleccionar la plataforma con mayor score de coincidencias (minimo 2 headers del fingerprint)

### Tabla de fingerprints

| Plataforma | Headers clave para deteccion |
|---|---|
| Tiendanube | `Número de orden`, `Estado de la orden`, `Subtotal de productos`, `Nombre del comprador`, `Provincia o estado` |
| Shopify | `Name` (con `#` en datos), `Financial Status`, `Fulfillment Status`, `Lineitem name`, `Lineitem quantity` |
| WooCommerce | `Order ID`, `Order Status` (con valores `wc-*`), `Billing First Name`, `Billing Last Name`, `Payment Method Title` |

### Fallback si no se detecta plataforma

Si no se detecta ninguna plataforma conocida:

1. **Modo fuzzy**: el script intenta mapear columnas desconocidas a canonicas usando similitud de strings (ej: `"order number"` → `order_id`, `"buyer email"` → `email`). Se loguea un warning con las columnas que no se pudieron mapear.
2. **Modo manual**: el usuario puede proveer un archivo `custom_mapping.json` en la misma carpeta que el CSV con el formato:
   ```json
   {
     "Mi Columna Original": "order_id",
     "Correo": "email",
     "Fecha Compra": "date"
   }
   ```
3. Si despues del fuzzy y del custom mapping quedan columnas canonicas criticas sin mapear (`order_id`, `date`, `total`), el script falla con error descriptivo indicando que columnas faltan.

### Columnas canonicas criticas (minimas para que el analisis funcione)

El script requiere al menos estas columnas para correr sin error:

- `order_id`
- `date`
- `total`
- `order_status` o `payment_status` (al menos una)

El resto son opcionales pero recomendadas para analisis completo.

---

## Notas generales de parsing

### Numeros

- Siempre normalizar a float antes de operar: remover simbolos de moneda (`$`, `ARS`, etc.), remover separadores de miles (`.` o `,` segun locale), reemplazar coma decimal por punto.
- Valores vacios o `"-"` o `"N/A"` → `0.0` para montos, `None` para campos opcionales.

### Fechas

- Siempre convertir a `datetime` con timezone UTC o naive (consistente en todo el dataset).
- Si el formato tiene hora, preservarla. Si no, usar `00:00:00`.
- Valores vacios → `None` (no rellenar con fecha falsa).

### Encodings

- Tiendanube: intentar `latin-1` primero; si falla, intentar `utf-8-sig`.
- Shopify y WooCommerce: `utf-8` o `utf-8-sig` (BOM).
- En caso de error de decodificacion, intentar con `errors='replace'` y loguear warning.

### Ordenes multi-linea (line items)

Tanto Tiendanube como Shopify y WooCommerce exportan una fila por cada producto de la orden. El script debe:

1. Agrupar por `order_id` para metricas de orden (totales, estado, cliente).
2. Mantener el nivel de linea para analisis de productos.
3. No duplicar totales al agrupar (el total de la orden se repite en cada linea; tomar solo la primera ocurrencia por orden).
