# dsh-lc-doc-check — 信用证单据条款核对

`dsh-lc-doc-check` 读取一份信用证交单核对表——表头加每条条款一行——核对这份核对表自身的齐备与内部一致：每条条款是否写明单据种类与信用证要求、是否记录了提交情况、交单日期是否不晚于有效期、最迟装运日是否不晚于有效期、不符点标记是否取自你自己配置的取值清单、表头是否声明信用证号与受益人、币制是否写成三位字母代码、单据种类是否重复。

## 它回答什么问题

| 你会问 | 它怎么答 |
|---|---|
| 某条条款的单据种类与信用证要求都没填，会被报出吗？ | 会。`LC-001` 会报出该条：凡是带了 `docType` 或 `requirement` 栏的条款，都要求两栏至少填了一栏。它只核对是否写了内容，不解读条款含义——它不解读信用证条款，所以填了但填错的照样通过。 |
| 信用证要求写了，提交情况栏空着。 | `LC-002` 要求凡是带了 `presented` 栏的条款都必须填写，空着即报出该行。它只核对提交情况是否记录在册，不核对写了什么——它不把这一栏与信用证要求栏做比对，因为比对需要读懂条款与单据内容。 |
| 它实际比对的是哪几个日期？解析不出来的日期怎么办？ | 只有两对：`LC-003` 比较 `presentedAt` 与 `expiryAt`，`LC-004` 比较 `latestShipment` 与 `expiryAt`；有效期可以在表头，因为引擎先查行、再查表头，同一天视为不晚于。两条规则解析不出的日期都随该行报出，而不是略过。`LC-004` 不读实际装运日期；装运日后若干天内交单的要求也不核对，规则库写明本次未取得该条文。 |
| `LC-005` 从来不报任何东西，是坏了吗？ | `LC-005` 没有坏：它的 `values` 出厂为空，表示未配置，于是本条在 `skipped` 里报出自己并说明原因，而不是静默通过。把 `values` 填上本机构的「不符点」口径，它就会报出 `discrepancy` 值不在册的行。它只核对标记是否在册，绝不判断是否真的构成不符点。 |
| 表头没写信用证号，或者币制写成了 `usd`。 | `LC-006` 在表头缺少 `lcNo` 或 `beneficiary` 时报出表头，交单情况才能对应到具体的信用证。`LC-007` 会报出任何不符合三位大写字母（规则库默认 pattern）的 `currency` 值，币制写在表头还是写在行上都一样；它只核对书写形式，不判断该币别对这份信用证是否选得对。 |
| 同一单据种类在两行里各出现一次。 | `LC-008` 会把后一行作为与前一行重复报出，比对时忽略空格。命中需要人工确认：一份信用证对同一单据提出多项要求是常见的，应在条款号栏把两行区分开，而不是删掉一行——或者停用本条。 |

## 依据的标准

| 文件 | 文号 | 引用它的规则 |
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

| 项目 | 状态 |
|---|---|
| Harness | 对等版本范围 `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` —— 已实测同时接受 `0.2.0-rc.2` 与 `0.2.1-alpha.1`。**刻意不声明 `engines.dsh`**：它没有任何读取者，也无法拒装任何宿主 |
| Node | `^22.19.0 || >=24.0.0` |
| 平台 | 全平台（纯 ESM；无原生代码、无联网、不调用模型） |
| 工具模式 | `native` / `ptc` / `both` 均可；批量校验整个目录时建议 `ptc`，schema 成本只付一次 |

## What it does

规则表、字段说明与行为细节见 [README.md](README.md#what-it-does)（英文主版本）。本插件只列出材料与所引条款之间的字面差异，并对无法执行的检查在 `skipped` 中逐项说明。

## Install

```sh
dsh plugin --profile <name> add dsh-lc-doc-check
dsh --profile <name> --dump-config | grep 'dsh-lc-doc-check'
```

## Configuration

全部可调参数都在 `src/config.ts` 的 Schemastery schema 中，只改 `cordis.yml` 即可生效，无需改代码；逐条阈值在 `rules/` 下的规则库文件里。

| 键 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `rulesFile` | string | `rules/lc-doc-check.yaml` | 规则库文件路径，相对插件包根目录 |
| `disabledRules` | string[] | `[]` | 要停用的规则 id 列表；每条都会出现在 `skipped` 中 |
| `onlyRules` | string[] | `[]` | 只执行这些规则 id；留空表示执行全部规则 |
| `skipNotes` | string | `""` | 附加到每条 `skipped` 说明后的备注 |
| `timeoutMs` | number | `120000` | 工具协作式超时预算（毫秒） |

## Material format

支持 JSON 与 YAML。完整字段示例见 [README.md](README.md#material-format)（英文主版本）。字段在读取层是可选的，由检查引擎校验，因此部分导出的材料会产生"缺项"类差异，而不是让程序崩溃。

## Rule sources

规则数据与代码分离，每条规则都带文件名、文号、按原文自身编号体系的条款号、逐字摘录与来源地址。加载期强制：摘录必须是真实引文且不少于八个字符；依据仅为原则性条款（`kind: derived-from-principle`，严重级上限 `warn`）或本机构配置（`kind: institutional-configuration`，上限 `info`）的检查不得标为 `error`。夸大依据的规则库会在加载期失败，而不会产出一份看起来很有底气的报告。

核验中确认的边界与"刻意没有作出的结论"见 [README.md](README.md#rule-sources)（英文主版本）与随包的 `rules/evidence/` 目录。

## Troubleshooting

- **插件装上了但工具不出现**：确认 `main` 指向 `lib/index.mjs` 且 `pnpm run build` 已生成该文件；`main` 写错会让加载器静默跳过该条目。
- **`dsh plugin add` 报版本不兼容**：peer 范围覆盖 `0.1.x` 与 `0.2.x`；若运行时在其之外，可显式豁免：`dsh plugin --profile <name> allow-version <包名@版本> --dsh-version <runtime> --accept-risk`
- **某条规则没有执行**：查看 `skipped` 数组，其中写明了规则 id 与原因。
- **`check` 报 `manifest-peers` 失败**：静态检查器比对的是一份早于 0.2 世代的硬编码 peer 范围；安装期的 peer 校验以运行时为准。这是 `dsh-plugin-dev` 的已知上游问题。
- **时间看起来偏移**：全部计算都是对输入字符串做墙上时钟运算，不做时区换算。

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-lc-doc-check
```

第 4 项把 `../_shared` 的共享件同步进 `src/shared/`；每次改动共享件后都要重跑。

## License

[Apache License 2.0](LICENSE) © 2026 dsh-lc-doc-check contributors.
