# dsh-lc-doc-check — Completude da lista de apresentação de documentos de um crédito documentário e coerência interna das suas datas

[![DSH Market](https://raw.githubusercontent.com/2BingLing/dsh-market/master/assets/readme/badge-listed-en.svg)](https://dsh.market/)

`dsh-lc-doc-check` lê uma lista de apresentação de documentos de um crédito documentário —o cabeçalho do crédito mais uma linha por cláusula— e verifica a completude e a coerência interna dessa lista: se cada cláusula regista o tipo de documento e a exigência do crédito, se a apresentação está registada, se a data de apresentação não é posterior ao vencimento, se a data-limite de embarque não é posterior ao vencimento, se a marca de discrepância vem do vocabulário que você configura, se o número do crédito e o beneficiário são declarados, se a moeda está escrita como código de três letras e se não há tipos de documento repetidos.

## Como é a saída

![Terminal demo of dsh-lc-doc-check: real output over its LC-001 fixture](https://raw.githubusercontent.com/PerryLink/dsh-lc-doc-check/main/docs/assets/dsh-lc-doc-check-demo.png)

Saída real deste plugin sobre o seu próprio fixture de teste `LC-001` — não é uma simulação. O pacote de regras não inventa citações, por isso cada achado nomeia a cláusula aplicada e avisa que o seu texto não foi obtido.

## O que ele responde

| Você pergunta | O que ele responde |
|---|---|
| Uma cláusula deixa vazios o tipo de documento e a exigência do crédito. Isso é reportado? | Sim. `LC-001` reporta essa cláusula, porque toda cláusula que traga a coluna `docType` ou `requirement` tem de ter pelo menos uma das duas preenchida. Verifica que haja texto, não o que a cláusula significa: não interpreta as condições do crédito, por isso uma exigência mal escrita passa. |
| A exigência está escrita, mas a coluna da apresentação está vazia. | `LC-002` exige `presented` em toda cláusula que traga a coluna e reporta a linha em que está vazia. Verifica que a apresentação fique registada, não o que diz: não compara essa célula com a célula da exigência, porque compará-las obriga a ler as cláusulas e os documentos. |
| Que datas compara realmente e o que acontece a uma data que não é analisável? | Dois pares, e só dois: `LC-003` compara `presentedAt` com `expiryAt`, e `LC-004` compara `latestShipment` com `expiryAt`; o vencimento pode estar no cabeçalho, porque o leitor procura primeiro na linha e depois no cabeçalho, e o mesmo dia conta como não posterior. Uma data que a regra não consegue analisar é reportada com a sua linha em vez de ser omitida. `LC-004` não lê nenhuma data real de embarque, e a exigência de apresentar dentro de um certo número de dias após o embarque não é verificada: o pacote declara que não obteve esse texto. |
| `LC-005` nunca reporta nada. Está avariado? | `LC-005` não está avariado: a sua lista `values` vem vazia, ou seja, por configurar, e a regra reporta-se então a si mesma em `skipped` com esse motivo, em vez de passar em silêncio. Preencha `values` com a terminologia da sua instituição e ela assinalará toda a linha cujo valor de `discrepancy` não conste da lista. Verifica apenas que a marca seja uma que você reconheça; nunca julga se existe realmente uma discrepância. |
| O cabeçalho não traz número do crédito, ou a moeda está escrita como `usd`. | `LC-006` reporta o cabeçalho quando `lcNo` ou `beneficiary` não são declarados, para que a apresentação possa ser ligada a um crédito concreto. `LC-007` reporta qualquer valor de `currency` que não sejam três letras maiúsculas (o padrão de origem do pacote), esteja a moeda no cabeçalho ou na linha; verifica apenas a forma, não se essa moeda é a correta para o crédito. |
| O mesmo tipo de documento aparece em duas linhas. | `LC-008` reporta a linha posterior como duplicada da anterior, ignorando os espaços do valor. O achado precisa de confirmação humana: é comum um crédito levantar várias exigências sobre um mesmo tipo de documento, por isso distinga as linhas na coluna do número da cláusula em vez de apagar uma — ou desative a regra. |

## Normas que segue

| Documento | Número | Regras que o citam |
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

| Superfície | Estado |
|---|---|
| Harness | Faixa de peers `>=0.1.2-rc.1 <0.2.0 \|\| >=0.2.0-0 <0.3.0` — verificada para aceitar tanto `0.2.0-rc.2` quanto `0.2.1-alpha.1`. **`engines.dsh` não é declarado**: não tem leitor e não pode recusar nenhum host |
| Node | `^22.19.0 || >=24.0.0` |
| Plataformas | Todas (ESM puro; sem código nativo, sem rede, sem chamada ao modelo) |
| Modo de ferramenta | Funciona em `native`, `ptc` e `both`; para um diretório inteiro use `ptc` |

## What it does

A tabela de regras, os campos e o comportamento detalhado estão em [README.md](README.md#what-it-does) (versão principal em inglês). O plugin apenas lista divergências literais frente às cláusulas citadas e indica em `skipped` cada verificação que não pôde ser executada.

## Install

```sh
dsh plugin --profile <name> add dsh-lc-doc-check
dsh --profile <name> --dump-config | grep 'dsh-lc-doc-check'
```

## Configuration

Todos os parâmetros ajustáveis ficam no esquema Schemastery de `src/config.ts`, portanto mudam pelo `cordis.yml` sem editar código; os limites por regra ficam no pacote de regras sob `rules/`.

| Chave | Tipo | Padrão | Descrição |
|---|---|---|---|
| `rulesFile` | string | `rules/lc-doc-check.yaml` | Caminho do pacote de regras, relativo à raiz do pacote |
| `disabledRules` | string[] | `[]` | Ids de regras a desativar; cada uma aparece em `skipped` |
| `onlyRules` | string[] | `[]` | Executar apenas estas regras; vazio executa todas |
| `skipNotes` | string | `""` | Nota acrescentada a cada motivo de `skipped` |
| `timeoutMs` | number | `120000` | Orçamento de tempo limite cooperativo da ferramenta |

## Material format

Aceita JSON ou YAML. O exemplo completo de campos está em [README.md](README.md#material-format) (versão principal em inglês). Os campos são opcionais na camada de leitura e validados pelo motor, de modo que uma exportação parcial gera achados sobre o que falta em vez de falhar.

## Rule sources

Os dados das regras ficam separados do código: cada regra traz documento, número, cláusula na numeração própria da fonte, trecho literal e URL de origem. O carregador impõe que o trecho seja citação real de pelo menos oito caracteres e que uma verificação baseada apenas em princípio geral (`kind: derived-from-principle`, teto `warn`) ou em política local (`kind: institutional-configuration`, teto `info`) nunca seja declarada `error`.

Os limites verificados e as conclusões deliberadamente **não** afirmadas estão em [README.md](README.md#rule-sources) (versão principal em inglês) e em `rules/evidence/`.

## Troubleshooting

- **O plugin instala mas a ferramenta não aparece**: confirme que `main` resolve para `lib/index.mjs` e que `pnpm run build` o gerou.
- **`dsh plugin add` recusa o pacote**: a faixa de peers cobre `0.1.x` e `0.2.x`; fora dela, conceda isenção explícita com `dsh plugin --profile <name> allow-version <pkg@ver> --dsh-version <runtime> --accept-risk`.
- **Uma regra não executou**: leia o arranjo `skipped`.
- **`check` informa `manifest-peers` como falha**: problema conhecido do `dsh-plugin-dev`; o runtime aplica a compatibilidade na instalação.
- **Os horários parecem deslocados**: toda a aritmética é de hora local sobre as cadeias fornecidas.

## Development

```sh
pnpm install
pnpm run typecheck
pnpm test
pnpm run build
node ../scripts/sync-shared.mjs dsh-lc-doc-check
```

O último comando copia o kit compartilhado de `../_shared` para `src/shared/`; execute-o novamente após cada alteração compartilhada.

## License

[Apache License 2.0](LICENSE) © 2026 dsh-lc-doc-check contributors.
