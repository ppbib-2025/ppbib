# PPBIB Website Measurement and Trust Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore search and lead measurement, remove unsupported product claims, add consistent author trust signals, and ship an evidence-gated case-study format for `ppbib.web.id`.

**Architecture:** Keep the existing static HTML/CSS/JavaScript site. Add dependency-free Node validation scripts that inspect source HTML and JSON-LD before edits are deployed; external Google account configuration is verified separately through the real Search Console and GA4 interfaces.

**Tech Stack:** Static HTML, Tailwind CSS 4, vanilla JavaScript, JSON-LD, Node.js built-in test runner, Google Search Console, Google Analytics 4.

## Global Constraints

- The current video price remains Rp99.900.
- A WhatsApp click may emit `generate_lead` and `whatsapp_click`, never `purchase`.
- Do not publish unsupported guarantees, bonuses, credentials, participant counts, or performance claims.
- A case study requires evidence for at least one baseline number and one outcome number.
- Preserve existing canonical URLs, mobile layouts, purchase links, and Product/Offer structured data.
- External Google account changes must be verified in the real product UI.

---

### Task 1: Add a dependency-free website validation harness

**Files:**
- Modify: `/home/ubuntu/ppbib-website/package.json:6-10`
- Create: `/home/ubuntu/ppbib-website/tests/site-content.test.js`
- Create: `/home/ubuntu/ppbib-website/tests/helpers/html.js`

**Interfaces:**
- Produces: `readPage(relativePath): string`, `extractJsonLd(html): object[]`, and `npm test` as the regression gate used by later tasks.

- [ ] **Step 1: Write the failing helper tests**

Create `tests/site-content.test.js` with Node's `node:test` and assertions that call missing helpers, verify `/produk-digital/` has Rp99.900, a non-placeholder WhatsApp URL, valid JSON-LD, and no GA4 `purchase` event.

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { readPage, extractJsonLd } = require('./helpers/html');

test('product page preserves authoritative price and purchase link', () => {
  const html = readPage('produk-digital/index.html');
  assert.match(html, /Rp99\.900/);
  assert.doesNotMatch(html, /href=["']#["']/);
  assert.doesNotMatch(html, /gtag\(['"]event['"],\s*['"]purchase['"]/);
});

test('product page JSON-LD parses', () => {
  assert.ok(extractJsonLd(readPage('produk-digital/index.html')).length > 0);
});
```

- [ ] **Step 2: Run the test and verify RED**

Run: `cd /home/ubuntu/ppbib-website && node --test tests/site-content.test.js`
Expected: FAIL with `Cannot find module './helpers/html'`.

- [ ] **Step 3: Implement the minimal HTML helpers**

Create `tests/helpers/html.js` using only `fs` and `path`. `extractJsonLd` must collect every `<script type="application/ld+json">...</script>` block and `JSON.parse` it.

- [ ] **Step 4: Wire the test command and verify GREEN**

Set `package.json` script to `"test": "node --test tests/*.test.js"`.
Run: `cd /home/ubuntu/ppbib-website && npm test`
Expected: PASS with no warnings.

- [ ] **Step 5: Commit**

```bash
cd /home/ubuntu/ppbib-website
git add package.json tests/site-content.test.js tests/helpers/html.js
git commit -m "test: add static website regression harness"
```

If `/home/ubuntu/ppbib-website` still has no Git repository, record the change in `/home/ubuntu/ppbib` and commit the mirrored patch there without initializing a new repository silently.

---

### Task 2: Restore Search Console and verify search-data access

**Files:**
- Create: `/home/ubuntu/ppbib-website/docs/measurement/search-console-verification.md`

**Interfaces:**
- Produces: verified property URL, ownership state, sitemap status, latest data date, and screenshots or textual observations for the implementation log.

- [ ] **Step 1: Check browser readiness**

Run the browser status action. Use the currently authenticated Google account. If OAuth consent is required, stop only for the user to approve the Google screen.

- [ ] **Step 2: Open the canonical Search Console property**

Open `https://search.google.com/search-console` and select `https://ppbib.web.id/` or the matching domain property. Do not create a duplicate property when an existing one is available.

- [ ] **Step 3: Verify the main workflow**

Observe ownership/access, Performance report availability, Page indexing report, and `https://ppbib.web.id/sitemap.xml` under Sitemaps. Record exact status and latest data date.

- [ ] **Step 4: Exercise failure paths**

If access is denied, document the active Google account and required permission. If the sitemap is missing or failed, resubmit the exact sitemap URL and capture the returned status. Do not claim reconnection until query or indexing data is visible.

- [ ] **Step 5: Save the evidence note**

Write `docs/measurement/search-console-verification.md` with date, property, observed reports, sitemap state, blockers, and no secrets.

---

### Task 3: Promote `generate_lead` to a GA4 key event after real ingestion

**Files:**
- Modify: `/home/ubuntu/ppbib-website/tests/site-content.test.js`
- Create: `/home/ubuntu/ppbib-website/docs/measurement/ga4-key-event-verification.md`

**Interfaces:**
- Consumes: existing product CTA tracking in `produk-digital/index.html` and `kursus/index.html`.
- Produces: a verified GA4 `generate_lead` key event and evidence of received parameters.

- [ ] **Step 1: Add failing source assertions for event parameters**

Add tests requiring `generate_lead` events on both product pages to include `currency`, `value`, `product_id`, and `cta_location`, while prohibiting `purchase`.

- [ ] **Step 2: Run the targeted tests and verify RED if any parameter is absent**

Run: `cd /home/ubuntu/ppbib-website && npm test`
Expected: FAIL naming the missing parameter, or PASS if the existing implementation already satisfies the contract. If it passes immediately, retain the regression test and do not change working source unnecessarily.

- [ ] **Step 3: Make the minimum source correction when RED**

Modify only the affected tracking blocks in:

- `/home/ubuntu/ppbib-website/produk-digital/index.html`
- `/home/ubuntu/ppbib-website/kursus/index.html`

Use `value: 99900`, `currency: 'IDR'`, stable product ID, and the actual CTA location.

- [ ] **Step 4: Verify GREEN and live event receipt**

Run `npm test`, then trigger one real CTA interaction without sending a WhatsApp message. Confirm `generate_lead` in GA4 Realtime or DebugView with the expected parameters.

- [ ] **Step 5: Mark the event as key event**

In GA4 Admin, open Events/Key events and mark the received `generate_lead` event as a key event. Do not create or mark `purchase`.

- [ ] **Step 6: Save evidence**

Write `docs/measurement/ga4-key-event-verification.md` with property/stream identifiers, observed event time, parameters, key-event state, and any ingestion delay.

---

### Task 4: Audit and reconcile product fulfillment claims

**Files:**
- Create: `/home/ubuntu/ppbib-website/data/product-offer-claims.json`
- Modify: `/home/ubuntu/ppbib-website/tests/site-content.test.js`
- Modify: `/home/ubuntu/ppbib-website/produk-digital/index.html:250-500`
- Modify: `/home/ubuntu/ppbib-website/kursus/index.html:320-620`

**Interfaces:**
- Produces: machine-readable claim inventory with `id`, `claim`, `status`, `evidence`, `allowedCopy`, and `pages`.

- [ ] **Step 1: Write failing tests for unsupported claims**

Add a test that loads `data/product-offer-claims.json`, rejects missing evidence for `verified` claims, and asserts that every `unsupported` claim's exact text is absent from both pages.

- [ ] **Step 2: Run and verify RED**

Run: `cd /home/ubuntu/ppbib-website && npm test`
Expected: FAIL because the inventory does not exist.

- [ ] **Step 3: Build the claim inventory from current source**

Include the 30-day guarantee, Telegram alumni access, 15-minute consultation, package components, delivery timing, and Rp1.395.000 package value. Use only `verified`, `conditional`, or `unsupported`. Evidence paths or dated internal references must be concrete; unknown evidence means `unsupported`.

- [ ] **Step 4: Reconcile page copy minimally**

Keep verified copy, add explicit conditions to conditional claims, and remove unsupported claims. Preserve Rp99.900 and label Rp1.395.000 only as component value when verified.

- [ ] **Step 5: Verify GREEN**

Run: `cd /home/ubuntu/ppbib-website && npm test`
Expected: PASS.

- [ ] **Step 6: Commit**

Commit the inventory, tests, and page changes as one independently reviewable claim-reconciliation change.

---

### Task 5: Add a consistent author entity and visible trust block

**Files:**
- Create: `/home/ubuntu/ppbib-website/data/author.json`
- Create: `/home/ubuntu/ppbib-website/js/author-profile.js`
- Modify: `/home/ubuntu/ppbib-website/tentang/index.html`
- Modify: the ten article pages under `/home/ubuntu/ppbib-website/budidaya/*/index.html` and `/home/ubuntu/ppbib-website/pakan-ikan/*/index.html`
- Modify: `/home/ubuntu/ppbib-website/tests/site-content.test.js`

**Interfaces:**
- Produces: canonical author `@id` of `https://ppbib.web.id/tentang/#adit`, visible author block, and consistent Article JSON-LD references.

- [ ] **Step 1: Write failing consistency tests**

Add tests over the ten article files requiring:

- visible text `Oleh Adit`;
- a link to `/tentang/`;
- Article `author.@id === 'https://ppbib.web.id/tentang/#adit'`;
- a single canonical author record whose visible name and JSON-LD name agree.

- [ ] **Step 2: Run and verify RED**

Run: `cd /home/ubuntu/ppbib-website && npm test`
Expected: FAIL on article pages that currently contain only `{ "name": "Adit" }`.

- [ ] **Step 3: Create the canonical author data**

Populate `data/author.json` only with facts verified from PPBIB records and the existing `/tentang/` page. Unknown credential fields must be omitted, not guessed.

- [ ] **Step 4: Implement the visible author block and schema references**

Add the stable Person node to `/tentang/` and update each Article author to reference the canonical `@id`. Use an existing real portrait asset; if none exists, use the PPBIB organization logo and describe the author without fabricating a portrait.

- [ ] **Step 5: Verify GREEN, JSON-LD parsing, links, and mobile source order**

Run `npm test`, then inspect `/tentang/` and two representative articles at mobile and desktop widths.

- [ ] **Step 6: Commit**

Commit canonical author data, trust block, schema changes, and tests.

---

### Task 6: Add an evidence-gated case-study template

**Files:**
- Create: `/home/ubuntu/ppbib-website/data/case-studies/example.schema.json`
- Create: `/home/ubuntu/ppbib-website/scripts/render-case-study.js`
- Create: `/home/ubuntu/ppbib-website/tests/case-study.test.js`
- Create: `/home/ubuntu/ppbib-website/studi-kasus/index.html`
- Modify: `/home/ubuntu/ppbib-website/sitemap.xml`

**Interfaces:**
- Produces: `validateCaseStudy(data): { valid: boolean, errors: string[] }` and `renderCaseStudy(data): string`.

- [ ] **Step 1: Write failing validation tests**

Test that a draft without baseline evidence fails, a draft without outcome evidence fails, and a complete fixture passes. Require species, location/consent mode, baseline metric/value/date/source, intervention, outcome metric/value/date/source, limitations, and CTA source.

- [ ] **Step 2: Run and verify RED**

Run: `cd /home/ubuntu/ppbib-website && node --test tests/case-study.test.js`
Expected: FAIL because the renderer does not exist.

- [ ] **Step 3: Implement the minimal validator and renderer**

Use Node built-ins only. Reject publication when evidence fields are empty. Escape all inserted HTML. Render numbers with their units and preserve limitations visibly.

- [ ] **Step 4: Create the case-study index without fabricated results**

Publish an index explaining the evidence standard and link only verified studies. If no study passes validation, show no numerical success claim and invite eligible alumni to submit before/after records.

- [ ] **Step 5: Verify GREEN and sitemap validity**

Run `npm test`. Parse `sitemap.xml`, fetch the local page through a static server, and check the WhatsApp CTA source value `case_study_index`.

- [ ] **Step 6: Commit**

Commit the schema, renderer, tests, index page, and sitemap entry.

---

### Task 7: Full regression, live deployment verification, and vault propagation

**Files:**
- Modify: `/home/ubuntu/second-brain/Dev Logs/2026-09-01 - PPBIB Website Growth Plan and Product Tracking.md`
- Modify: `/home/ubuntu/second-brain/Daily/2026-09-01.md`
- Modify: `/home/ubuntu/second-brain/Logs/2026-09-01.md`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: verified live workflow and durable record of what changed.

- [ ] **Step 1: Run all automated checks**

```bash
cd /home/ubuntu/ppbib-website
npm test
npm run build
```

Expected: all tests PASS and Tailwind build exits 0.

- [ ] **Step 2: Run source-wide regression checks**

Confirm no obsolete product prices, unsupported claims, placeholder purchase links, invalid JSON-LD, or GA4 `purchase` events remain.

- [ ] **Step 3: Exercise representative live workflows**

Check homepage → product page → WhatsApp CTA, one article → author page, case-study index → CTA, sitemap fetch, robots fetch, and mobile layouts. Do not send a WhatsApp message during CTA testing.

- [ ] **Step 4: Verify external measurement state**

Reopen Search Console and GA4. Confirm property access, sitemap state, `generate_lead` receipt, and key-event state.

- [ ] **Step 5: Update Obsidian records**

Rewrite the existing dev log with completed work, observed results, unresolved blockers, exact live URLs, and confidence. Propagate a short summary to the daily note and append the operation to the per-day log.

- [ ] **Step 6: Commit documentation separately**

Commit website changes in their repository if available, and vault notes in the vault repository if available. Never combine secrets or browser session data with source commits.
