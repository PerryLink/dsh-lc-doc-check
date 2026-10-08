# dsh-lc-doc-check — Letter-of-credit presentation checklist completeness and internal date consistency check

`dsh-lc-doc-check` reads one letter-of-credit presentation checklist — the credit header plus one row per term — and checks that checklist's own completeness and internal consistency: that each term records the document type and the credit's requirement, that the presentation is recorded, that the presentation date is not later than the expiry, that the latest shipment date is not later than the expiry, that the discrepancy marker comes from the vocabulary you configure, that the credit number and beneficiary are declared, that the currency is written as a three-letter code, and that no document type is repeated.

## What it answers

| You ask | What it answers |
|---|---|
| One term leaves both the document type and the credit's requirement blank. Is that reported? | Yes. `LC-001` reports that term, because every term carrying the `docType` or `requirement` column must have at least one of the two filled. It checks that something is written, not what the term means: it does not interpret the credit's terms, so a requirement that is filled in but wrong passes. |
| The requirement is written down, but the presentation column is empty. | `LC-002` requires `presented` on every term that carries the column and reports the row where it is blank. It checks that the presentation is recorded, not what it says — it does not compare that cell with the requirement cell, because comparing them means reading the terms and the documents. |
| Which dates does it actually compare, and what happens to a date that will not parse? | Two pairs, and only two: `LC-003` compares `presentedAt` with `expiryAt`, and `LC-004` compares `latestShipment` with `expiryAt`; the expiry may sit in the header, because the reader looks in the row first and then in the header, and the same day counts as not later. A date neither rule can parse is reported with its row instead of being passed over. `LC-004` reads no actual shipment date, and the requirement to present within a number of days after shipment is not checked, because the pack states that it could not obtain that text. |
| `LC-005` never reports anything. Is it broken? | `LC-005` is not broken: its `values` list ships empty, which means unconfigured, and the rule then reports itself in `skipped` with that reason rather than passing silently. Fill `values` with your institution's discrepancy wording and it reports every row whose `discrepancy` value is not on the list. It checks only that the marker is one you recognise; it never judges whether a discrepancy exists. |
| The header carries no credit number, or the currency is written as `usd`. | `LC-006` reports the header when `lcNo` or `beneficiary` is not declared, so that a presentation can be tied to one credit. `LC-007` reports any `currency` value that is not three upper-case letters (the pack's default pattern), whether the currency sits in the header or on the row; it checks the shape only, not whether that currency is the right one for the credit. |
| The same document type appears in two rows. | `LC-008` reports the later row as a duplicate of the earlier one, ignoring spaces in the value. The hit needs human confirmation: a credit often raises several requirements against one document type, so distinguish the rows in the term-number column instead of deleting one — or disable the rule. |

## Standards it follows

| Document | Number | Cited by rules |
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

| Surface | Status |
|---|---|
| Harness | Peer range `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verified to accept both `0.2.0-rc.2` and `0.2.1-alpha.1`. `engines.dsh` is deliberately not declared: it has no reader and cannot reject a host |
| Node | `^22.19.0 || >=24.0.0` |
| Platforms | All (plain ESM; no native code, no network, no model call) |
| Tool mode | Works in `native`, `ptc` and `both`; for a full presentation use `ptc` |

## What it does

Registers the `lc_doc_check` tool. It reads one presentation checklist — the credit header plus one row per
term — applies a versioned rule pack, and returns a report.

| Rule | Check | Severity | Basis kind |
|---|---|---|---|
| `LC-001` | each term records its document type and requirement | warn | principle |
| `LC-002` | each term records the presentation | warn | principle |
| `LC-003` | presentation is not later than the expiry | warn | principle |
| `LC-004` | latest shipment is not later than the expiry | warn | principle |
| `LC-005` | the discrepancy marker comes from your vocabulary (off by default) | info | local |
| `LC-006` | the credit number and beneficiary are declared | warn | principle |
| `LC-007` | the currency is a three-letter code | warn | principle |
| `LC-008` | document types are unique | warn | principle |

## Install

```sh
dsh plugin --profile <name> add dsh-lc-doc-check
dsh --profile <name> --dump-config | grep 'dsh-lc-doc-check'
```

## Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `rulesFile` | string | `rules/lc-doc-check.yaml` | Rule-pack path, relative to the package root |
| `disabledRules` | string[] | `[]` | Rule ids to stop running; each appears in `skipped` |
| `onlyRules` | string[] | `[]` | Run only these rule ids; empty runs every rule |
| `skipNotes` | string | `""` | Note appended to every `skipped` reason |
| `timeoutMs` | number | `120000` | Cooperative tool timeout budget |

Rule-level parameters worth knowing:

- `LC-003` / `LC-004` `field` / `notAfterField` — the date pair to compare. The expiry may live in the header;
  the reader looks in the row first and then the header, so a credit-wide expiry is found.
- `LC-005` `values` — your discrepancy vocabulary, e.g. `[无不符点, 有不符点, 已接受, 已拒付]`. Empty means no
  check.
- `LC-007` `pattern` — the currency shape, three upper-case letters by default.
- `LC-008` — document types must be unique. If your credit raises several requirements against one document
  type, distinguish the rows in the term-number column or disable the rule.

## Material format

The tool accepts JSON or YAML:

```yaml
lcNo: LC2026-0018
lcType: 不可撤销即期信用证
applicant: 某某进口商
beneficiary: 某某出口有限公司
issuingBank: 某某银行
currency: USD
expiryAt: 2026-04-10
rows:
  - { 序号: '1', 单据种类: 商业发票,
      信用证要求: 商业发票一式三份，注明信用证号与合同号,
      提交情况: 已提交一式三份，已注明信用证号与合同号, 份数: '3',
      交单日期: 2026-03-20, 最迟装运日: 2026-03-15, 有效期: 2026-04-10,
      不符点: 无不符点, 处理状态: 已审单 }
```

Column names are matched case-insensitively and ignoring spaces, underscores and hyphens; the checklist's own
column names are kept, so a finding names the column it read. Dates may be `2026-03-20` or
`2026-03-20 14:00`.

## Rule sources

Rule data lives in `rules/lc-doc-check.yaml`. The pack's header states what the plugin checks and what it
leaves to the bank, and each rule's `note` repeats the part that matters for that rule. The load-time guard
still requires a document, clause, excerpt and source per rule, and still forbids a locally configured check
from being `error`.

## Troubleshooting

- **It passed a presentation I know is discrepant.** By design: it records that the requirement and the
  presentation are both written down, and never compares them. Examination is the bank's job.
- **`LC-005` never runs.** Its vocabulary is empty. Fill it with your bank's wording, or leave it disabled.
- **`LC-004` does not catch a late shipment.** The rule compares the latest shipment date against the expiry,
  not an actual shipment date. Add a rule with `field: <actual shipment column>` and
  `notAfterField: latestShipment` if your register has one.
- **`LC-008` fires on two requirements for one document type.** That is normal in many credits; number the
  rows apart or disable the rule.
- **The plugin installs but the tool never appears.** Check that `main` resolves to `lib/index.mjs` and
  that `pnpm run build` produced it; a wrong `main` makes the loader skip the entry silently.
- **`dsh plugin add` refuses the package as incompatible.** The peer range covers `0.1.x` and `0.2.x`; if
  your runtime sits outside it, grant an explicit exemption:
  `dsh plugin --profile <name> allow-version dsh-lc-doc-check@0.1.0 --dsh-version <runtime> --accept-risk`
- **`check` reports `manifest-peers` as failed.** The static checker compares against a hard-coded peer
  range that predates the 0.2 line. The runtime enforces peer compatibility at install time, so the
  declared range is the correct one; this is a known upstream issue in `dsh-plugin-dev`.

## Development

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit
pnpm test            # vitest, the shared table-plugin suite plus paired fixtures
pnpm run build       # tsdown -> lib/index.mjs + lib/index.d.mts
node ../scripts/sync-shared.mjs dsh-lc-doc-check   # refresh src/shared from ../_shared
```

The plugin is **data-only**: `src/model.ts` declares the table shape, the shared kit supplies the reader and
the check engine, and the rule pack declares every check.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-lc-doc-check contributors.
