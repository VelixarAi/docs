# VOU and token explanation: implementation contract

Status: proposed implementation contract, 2026-09-27. The accompanying customer pages and benchmark audit are implemented documentation changes. This contract does not claim that its proposed API, catalog projection or telemetry fields are deployed.

Founder input: use the two supplied ChatGPT drafts as a framework. Use actual Velixar receipts, code and deployment evidence for numbers and capabilities. Coordinate changes through memory tagged `collab:claude-codex`.

## Authority and present implementation

Cognition's `lambda/vou/catalog.py` defines operation vocabulary and quantity semantics. `normalizer.py`, schedule records and ledger entries define normalized work; `rating.py` and effective commercial policy determine classification. `explain.py` reconstructs stored ledger values. `api/token_meter.py` distinguishes provider usage, local tokenizer counts and heuristic estimates. These are inputs to review, not proof of production availability.

Current catalog comments label resource-derived weights as assumptions. Documentation must preserve actual schedule evidence quality and effective dates. A founder pricing decision is distinct from an enabled billing deployment. The existing legacy docs pricing pages and Claude's `cpo/docs-pricing-truth` branch require coordinated reconciliation; this change does not replace either billing policy.

The proposed frontend and CLI VOU summaries already consume server totals. Do not bolt a guessed token conversion onto those totals. Add token details only after the server can supply the evidence described below. Direct external model calls remain unknown unless the caller supplies a trusted usage receipt.

## Customer explanation contract

Every surface answers four questions independently:

1. What governed operations ran? Show ledger amount, quantity, unit, historical weight/schedule, corrections and completeness.
2. What did the model process? Show actual usage and measurement method by invocation; context is a separately labelled subset.
3. What was charged? Show commercial state, rating, applicable allowance/credit and versioned rate. A measured VOU total alone is not an invoice.
4. What supports savings? Show a paired baseline and its provenance, or leave the comparison unavailable. Keep estimated scenarios visually distinct.

Never display missing data as zero. Known zero, unknown, estimated and unavailable are separate states. Never silently drop a negative correction from a group subtotal. An execution's grouped model/provider/task totals are alternate views of the same rows, not quantities to add together.

## CTO: evidence pipeline and attribution

Add an authenticated, workspace-scoped projection with additive versioned fields. Reuse durable attempt IDs and operation IDs; retries that actually invoke a model receive separate attempt usage, while duplicate delivery of one receipt is idempotent. Parent operations reference child usage rather than duplicating it. Reconciliation must never rerun inference.

Required receipt dimensions:

- Workspace, execution, operation, invocation/attempt, parent operation, task type, provider, deployment/model version and occurrence time.
- Provider-reported input/output counts; optional cache-read/write and reasoning counts; explicit schema explaining subset versus exclusive bucket semantics. Preserve missing values.
- Retrieved-context count, baseline count, tokenizer/version or provider counter, count method, baseline scope, paired sample identifier and evidence reference.
- Optional measured cost or rated cost, currency, rate-source/version/effective time, coverage and exclusions. Distinguish provider-reported spend from a rate calculation.
- VOU ledger/rating/schedule references and correction lineage. Retain historical schedule values.

Do not persist prompts, memory content, generated code or API keys to explain token usage. Baseline counting must not create new third-party content egress by default. Existing token-counter defaults intentionally avoid that egress.

Normalize provider usage into mutually exclusive price buckets before cost calculation. Some providers include cached input in total input and reasoning in output; others use separate buckets. Unknown cache semantics prevent an exact cost result. Provider adapter fixtures must prove that cached or reasoning tokens cannot be billed twice. A missing usage receipt leaves cost unknown.

End-to-end cost includes actual paid attempts, failed attempts where provider usage exists, and attributable ingestion/indexing/embedding costs. If ingest is amortized, show the allocation basis and reuse count. If these dimensions are absent, label the result as reader-only or partial. Do not mix a context-only reference with a full task bill.

Aggregate reduction as `1 - sum(selected_tokens) / sum(paired_baseline_tokens)` over the same scope and compatible tokenizer. Empty/nonpositive baseline means unavailable. Include regressions where selected tokens exceed baseline; do not clamp them to zero. Do not mix token families into one percentage or treat retrieval recall as token savings. Matched-quality comparison needs a paired evaluation, not an unrelated accuracy headline.

## Catalog-driven documentation

Create a strictly allowlisted public projection of the operation catalog and effective published schedule. Include operation name, customer description, family, quantity basis, bundling, weight, evidence quality, schedule/version and effective dates. Include availability state so planned code is not advertised as deployed.

Expose price information only from an approved, effective public commercial projection. Exclude internal resource coefficients, cost/margin data, private policy, tenant records, infrastructure identifiers and unpublished model entitlements. Descriptions need product/security review even if the underlying catalog is correct.

Generate docs examples from that projection. Build checks reject vocabulary, unit, weight, schedule or price drift. Retain historical versions for old receipts. On projection failure, do not silently render stale values as current. Until this exists, use no hardcoded illustrative price/weight table in the new explanation.

## CPO and Head of Design: customer surfaces

Use the same explanation vocabulary in docs, dashboard and CLI. Show VOU consumption and model token usage as separate measures, with a visible period, selected workspace and completeness. Put the actual input/output counts before a savings percentage. Allow expansion into operation and attempt detail without exposing content.

Savings should name its reference: for example, “84.23% less context in the audited 120-question benchmark.” Do not label it “your savings” on a customer's account. A per-customer comparison must identify that customer's paired sample and method. A rate calculator accepts explicitly labelled rates and shows a scenario, not a charge receipt.

The evidence page's six categories are benchmark question types; do not rename them VOU operation families. A model leaderboard must compare task success, latency and total attributed cost under the same test protocol, not choose a winner from token count alone.

## CISO: release evidence

Review workspace isolation for all receipt joins and aggregations; current membership, API scope and delegated authority; secret/content exclusion; replay/idempotency; correction integrity; bounded queries; incomplete-meter behavior; and cache/reasoning double counting. A cross-workspace ID must not disclose existence or details.

A security approval must name exact source/artifact revisions and tested boundaries. Docs source checks are not production verification. Core cancellation and n8n recovery remediation remains under a separate existing CISO review; these documentation changes do not waive that gate.

## CRO: commercial decisions

CRO owns the proposed price-gating design and evidence for allowances, free usage, premium models and build access. Reflect ratified policy and deployment state, including spending controls; do not infer a price from an operation weight or the token benchmark. No billing activation is part of this docs change.

## Completion evidence

- Source audit: reproducible token totals, hashes, paired sample and explicit exclusions; independent recomputation of baseline; no raw conversations published.
- Accounting tests: cached/reasoning subset fixtures, retries, missing usage, duplicate receipts, negative corrections, partial coverage, historical rate/schedule preservation and cross-workspace denial.
- Docs checks: valid navigation and MDX; catalog-projection drift checks once implemented; all numeric examples carry their source and scope.
- Deployment: source review and CI, staged authenticated receipt/display checks, exact artifact verification and CISO decision before runtime enablement. Publish the new docs before releasing the website correction that links to them.
