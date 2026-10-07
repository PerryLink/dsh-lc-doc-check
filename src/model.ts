/**
 * dsh-lc-doc-check — table shape and material contract.
 *
 * The plugin is data-only: this file declares which columns the material may use
 * and how they map onto canonical field names; the shared kit supplies the reader
 * and the check engine, and the rule pack declares every check. Adding a check
 * that fits an existing kind is a rule-pack edit, not a code change.
 */

import { canonicaliseRow, parseTable, type TableSpec } from './shared/table.ts'
import { runTableCheck, type TableCheckOptions, type TableInput } from './shared/rows.ts'
import type { Ruleset } from './shared/rules.ts'

/** Tool id exposed to the model, and the row id in `cordis.patch.yml`. */
export const TOOL_NAME = 'lc_doc_check'

/** The register's column aliases, declared once so both the spec and the guard see them. */
const COLUMNS = {
  termNo: ['序号', '条款号', '项号', 'termNo'],
  docType: ['单据种类', '单据类型', '单证名称', 'docType'],
  requirement: ['信用证要求', '条款要求', '要求', 'requirement'],
  presented: ['提交情况', '交单情况', '提交内容', 'presented'],
  copies: ['份数', '要求份数', '提交份数', 'copies'],
  issuer: ['出具人', '签发人', '出单人', 'issuer'],
  consignee: ['收货人', '抬头', '收货人抬头', 'consignee'],
  presentedAt: ['交单日期', '提交日期', 'presentedAt'],
  /**
   * The credit's currency.
   *
   * Declared as a row column as well as a header field: a credit may cover one
   * currency for the whole set or state it per document line, and the format check
   * reads whichever the register uses.
   */
  currency: ['币制', '币种', 'currency'],
  latestShipment: ['最迟装运日', '装运日期', 'latestShipment'],
  expiryAt: ['有效期', '信用证有效期', '到期日', 'expiryAt'],
  discrepancy: ['不符点', '是否不符', '差异', 'discrepancy'],
  status: ['处理状态', '状态', 'status'],
  note: ['备注', '说明', 'note', 'remark'],
} as const

/** How the material declares its table. */
export const SPEC: TableSpec = {
  rowKeys: ['rows', 'items', 'terms', '条款'],
  columns: COLUMNS,
  header: {
  lcNo: ['lcNo', '信用证号', '信用证编号'],
  lcType: ['lcType', '信用证类型', '类型'],
  applicant: ['applicant', '申请人', '开证申请人'],
  beneficiary: ['beneficiary', '受益人'],
  issuingBank: ['issuingBank', '开证行'],
  amount: ['amount', '信用证金额', '金额'],
  currency: ['currency', '币制', '币种'],
  expiryAt: ['expiryAt', '信用证有效期', '到期日'],
  latestShipment: ['latestShipment', '最迟装运日'],
  checkedAt: ['checkedAt', '核对日期'],
  },
}

/** Fields the material must carry somewhere for the reader to accept it. */
export const REQUIRE_ANY_OF = [
  '单据种类',
  'docType',
  '信用证要求',
  'requirement',
  '提交情况',
  'presented',
  '不符点',
  'discrepancy',
]

/**
 * Parse the material and attach its canonical field names.
 * @param source - JSON or YAML text.
 * @param target - description of where the material came from.
 * @returns the normalized table, with each row's aliases resolved to field names.
 */
export function parseMaterial(source: string, target: string): TableInput {
  const table = parseTable(source, target, {
    ...SPEC,
    ...(REQUIRE_ANY_OF === undefined ? {} : { requireAnyOf: REQUIRE_ANY_OF }),
  })
  for (const row of table.rows) canonicaliseRow(row, SPEC)
  return table
}

/**
 * Run the rule pack against the material.
 * @param input - normalized table.
 * @param ruleset - validated rule pack.
 * @param options - plugin identity, clock value, rule selection and overrides.
 * @returns the report.
 */
export function runCheck(input: TableInput, ruleset: Ruleset, options: TableCheckOptions) {
  return runTableCheck(input, ruleset, options)
}

export type { TableCheckOptions, TableInput }
