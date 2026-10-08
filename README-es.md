# dsh-lc-doc-check — Completitud de la lista de presentación de documentos de un crédito documentario y coherencia interna de sus fechas

`dsh-lc-doc-check` lee una lista de presentación de documentos de un crédito documentario —la cabecera del crédito más una fila por cláusula— y comprueba la completitud y la coherencia interna de esa lista: que cada cláusula registre el tipo de documento y la exigencia del crédito, que la presentación esté registrada, que la fecha de presentación no sea posterior al vencimiento, que la fecha límite de embarque no sea posterior al vencimiento, que la marca de discrepancia proceda del vocabulario que usted configure, que se declaren el número de crédito y el beneficiario, que la moneda se escriba como código de tres letras y que no se repita ningún tipo de documento.

## Qué responde

| Usted pregunta | Qué responde |
|---|---|
| Una cláusula deja vacíos el tipo de documento y la exigencia del crédito. ¿Se informa de eso? | Sí. `LC-001` informa de esa cláusula, porque toda cláusula que traiga la columna `docType` o `requirement` debe tener al menos una de las dos rellena. Comprueba que haya texto, no lo que la cláusula significa: no interpreta las condiciones del crédito, así que una exigencia mal escrita pasa. |
| La exigencia está escrita, pero la columna de la presentación está vacía. | `LC-002` exige `presented` en toda cláusula que traiga la columna e informa de la fila en que está vacía. Comprueba que la presentación quede registrada, no lo que dice: no compara esa celda con la celda de la exigencia, porque compararlas obliga a leer las cláusulas y los documentos. |
| ¿Qué fechas compara realmente y qué ocurre con una fecha que no se puede analizar? | Dos pares, y solo dos: `LC-003` compara `presentedAt` con `expiryAt`, y `LC-004` compara `latestShipment` con `expiryAt`; el vencimiento puede estar en la cabecera, porque el lector mira primero en la fila y luego en la cabecera, y el mismo día cuenta como no posterior. Una fecha que la regla no puede analizar se informa con su fila en lugar de omitirse. `LC-004` no lee ninguna fecha real de embarque, y la exigencia de presentar dentro de un cierto número de días tras el embarque no se comprueba: el paquete declara que no obtuvo ese texto. |
| `LC-005` no informa nunca de nada. ¿Está averiado? | `LC-005` no está averiado: su lista `values` viene vacía, es decir, sin configurar, y entonces la regla se informa a sí misma en `skipped` con ese motivo en lugar de pasar en silencio. Rellene `values` con la terminología de su institución y señalará toda fila cuyo valor de `discrepancy` no esté en la lista. Solo comprueba que la marca sea una que usted reconozca; nunca juzga si existe realmente una discrepancia. |
| La cabecera no trae número de crédito, o la moneda figura como `usd`. | `LC-006` informa de la cabecera cuando no se declaran `lcNo` o `beneficiary`, para que la presentación pueda ligarse a un crédito concreto. `LC-007` informa de todo valor de `currency` que no sean tres letras mayúsculas (el patrón por defecto del paquete), esté la moneda en la cabecera o en la fila; solo comprueba la forma, no si esa moneda es la correcta para el crédito. |
| El mismo tipo de documento aparece en dos filas. | `LC-008` informa de la fila posterior como duplicada de la anterior, ignorando los espacios del valor. El hallazgo necesita confirmación humana: es habitual que un crédito plantee varias exigencias sobre un mismo tipo de documento, así que distinga las filas en la columna del número de cláusula en vez de borrar una, o desactive la regla. |

## Normas que sigue

| Documento | Número | Reglas que lo citan |
|---|---|---|
| 《跟单信用证统一惯例》（UCP600） | 国际商会第 600 号出版物（本次未取得条文） | LC-001, LC-002, LC-003, LC-004, LC-005, LC-006, LC-008 |
| 《表示货币的代码》 | GB/T 12406—2022（表示货币的代码；2022-12-30 发布并实施；全部代替 GB/T 12406—2008（该版名称为「表示货币和资金的代码」）——注意旧版名称含"资金"；修改采用 ISO 4217:2015，非等同采用；条号本次未取得） | LC-007 |

**Boundary:** this plugin checks a **信用证交单核对表** for the mechanical side of documentary compliance — that
each term records the document type and the credit's requirement, that the presentation is recorded, that the
presentation date is not later than the expiry, that the latest shipment date is not later than the expiry,
that the discrepancy marker comes from your vocabulary, that the credit number and beneficiary are declared,
that the currency follows its format, and that document types are unique. It does **not** decide whether a
presentation is discrepant, whether a bank must pay, or whether the documents meet the credit's terms.

> ### ⚠️ It reads a checklist, not the credit and not the documents
>
> **The plugin does not interpret credit terms.** It checks that the requirement column and the presentation
> column are both filled — it does **not** compare them, because comparing them means reading the terms and the
> documents, which is the bank's examination under UCP 600 and ISBP. So a term that the documents plainly fail
> passes this plugin as long as both columns carry text.
>
> **The 不符点 column is your declaration.** The plugin checks only that its value is one you recognise; it
> **never judges whether a discrepancy exists**. That judgement belongs to the bank.
>
> Two date checks are included, and only two: presentation ≤ expiry, and latest shipment ≤ expiry. **The
> UCP 600 rule requiring presentation within a number of days after shipment is not checked**, because the
> rule pack could not obtain the text and the register usually has no separate actual-shipment column. The
> note on that rule says so, and explains how to add the check if your register has the column.
>
> **Every `excerpt` in the rule pack says, in so many words, that the clause text was not obtained** — the
> ICC's UCP 600 and ISBP are publications the verification pass could not retrieve verbatim. The pack states
> the gap in the `excerpt` field itself and keeps every rule at `warn` or `info`. **When the texts are in
> hand, replace each `excerpt` with the real clause and raise `kind` to `direct`.**

## Compatibility

| Superficie | Estado |
|---|---|
| Harness | Rango de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificado para aceptar tanto `0.2.0-rc.2` como `0.2.1-alpha.1`. **No se declara `engines.dsh`**: no tiene lector y no puede rechazar ningún host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sin código nativo, sin red, sin llamada al modelo) |
| Modo de herramienta | Funciona en `native`, `ptc` y `both`; para un directorio completo use `ptc` |

## What it does

La tabla de reglas, los campos y el comportamiento detallado están en [README.md](README.md#what-it-does) (versión principal en inglés). El plugin sólo enumera divergencias literales frente a las cláusulas citadas e indica en `skipped` cada comprobación que no pudo ejecutarse.

## Install

```sh
dsh plugin --profile <name> add dsh-lc-doc-check
dsh --profile <name> --dump-config | grep 'dsh-lc-doc-check'
```

## Configuration

Todos los parámetros ajustables viven en el esquema Schemastery de `src/config.ts`, por lo que se cambian desde `cordis.yml` sin tocar el código; los umbrales por regla están en el paquete de reglas bajo `rules/`.

| Clave | Tipo | Predeterminado | Descripción |
|---|---|---|---|
| `rulesFile` | string | `rules/lc-doc-check.yaml` | Ruta del paquete de reglas, relativa a la raíz del paquete |
| `disabledRules` | string[] | `[]` | Ids de reglas que se dejan de ejecutar; cada una aparece en `skipped` |
| `onlyRules` | string[] | `[]` | Ejecutar solo estas reglas; vacío ejecuta todas |
| `skipNotes` | string | `""` | Nota añadida a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Presupuesto de tiempo de espera cooperativo de la herramienta |

## Material format

Acepta JSON o YAML. El ejemplo completo de campos está en [README.md](README.md#material-format) (versión principal en inglés). Los campos son opcionales en la capa de lectura y los valida el motor, de modo que una exportación parcial produce hallazgos sobre lo que falta en lugar de un fallo.

## Rule sources

Los datos de las reglas están separados del código: cada regla lleva documento, número, cláusula en la numeración propia de la fuente, extracto literal y URL de origen. El cargador impone que el extracto sea una cita real de al menos ocho caracteres y que una comprobación basada sólo en un principio general (`kind: derived-from-principle`, tope `warn`) o en una política local (`kind: institutional-configuration`, tope `info`) nunca se declare `error`.

Los límites verificados y las conclusiones deliberadamente **no** afirmadas están en [README.md](README.md#rule-sources) (versión principal en inglés) y en `rules/evidence/`.

## Troubleshooting

- **El plugin se instala pero la herramienta no aparece**: compruebe que `main` resuelve a `lib/index.mjs` y que `pnpm run build` lo generó.
- **`dsh plugin add` rechaza el paquete**: la faixa de peers cubre `0.1.x` y `0.2.x`; fuera de ella, conceda una exención explícita con `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Una regla no se ejecutó**: lea el arreglo `skipped`.
- **`check` informa `manifest-peers` como fallo**: es un problema conocido de `dsh-plugin-dev`; el runtime aplica la compatibilidad al instalar.
- **Los horarios parecen desplazados**: toda la aritmética es de hora local sobre las cadenas entregadas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-lc-doc-check
```

El último comando copia el kit compartido de `../_shared` a `src/shared/`; vuelva a ejecutarlo tras cada cambio compartido.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-lc-doc-check contributors.
