# 1

> Nota historica: esta idea esta superada. El modelo vigente NO usa actividad por comentarios como criterio de ventana, NO mantiene backlog explicito y trabaja con posts de `r/Odoo` filtrados por fecha de creacion dentro de 7 dias. Ver `docs/product/product.md` y `docs/integrations/reddit/api-strategy.md`.

En la fase 2 candidate-memory-and-uniqueness: TTL DE LOS REGISTROS DE "FECHA DE POST + 7 DÍAS". PORQUE CON EL FILTRO DE POSTS CON ACTIVIDAD ULTIMOS 7 DÍAS YA NOS SALDRÁN COMO OPCIÓN Y NO SERÁ NECESARIO VALIDAR SI YA SE HA ENVIADO, ASÍ AHORRAMOS ESPACIO.
