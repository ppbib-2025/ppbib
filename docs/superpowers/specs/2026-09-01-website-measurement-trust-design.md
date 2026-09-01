# PPBIB Website Measurement and Trust Design

**Date:** 2026-09-01
**Status:** Approved for planning

## Goal

Turn `ppbib.web.id` into a measurable business funnel by restoring search data, promoting qualified WhatsApp inquiries to a GA4 key event, removing unsupported offer claims, and adding credible author and case-study evidence.

## Scope

This design covers four bounded workstreams:

1. Search Console access and query visibility.
2. GA4 lead-conversion configuration and verification.
3. Offer-claim verification on the digital product funnel.
4. Author trust signals and an evidence-first case-study format.

It does not add checkout, payment confirmation, AdSense placements, or new product pricing.

## Recommended sequence

### 1. Restore measurement first

Reconnect the `https://ppbib.web.id/` Search Console property through the currently authorized Google account. Confirm ownership, sitemap status, indexing coverage, and query/page data availability. In GA4, register `generate_lead` as a key event only after the event appears in Realtime or DebugView.

A WhatsApp click remains a lead signal. It must not emit `purchase`, because payment is not confirmed on the website.

### 2. Verify the offer against fulfillment

Create a claim inventory from `/produk-digital/` and `/kursus/`. Each claim receives one of three states:

- verified: fulfillment evidence exists and the claim may remain;
- conditional: the wording must state its conditions;
- unsupported: remove or suppress it until evidence exists.

The audit specifically covers the 30-day guarantee, Telegram alumni access, 15-minute consultation, package contents, delivery timing, and Rp1.395.000 assigned package value. The Rp99.900 selling price remains authoritative.

### 3. Add author trust without inflated claims

Add a reusable author block for Adit and PPBIB using only verifiable facts already present in PPBIB records. The block should include name, role, field focus, relevant experience, a real portrait, and links to the organization/contact pages. Article structured data should reference a stable `Person` or `Organization` entity using consistent IDs.

No unsupported credential, participant count, success rate, or “expert” label may be introduced.

### 4. Publish evidence-first case studies

Create a reusable case-study page format with these fields:

- operator and location, with consent-aware naming;
- fish species and cultivation setup;
- baseline period and measurement method;
- intervention performed;
- before and after numbers such as FCR, mortality, feed cost, harvest weight, or margin;
- limitations and factors not controlled;
- supporting photo, message, spreadsheet, or observation date;
- CTA to discuss a comparable case through WhatsApp.

A case study is not published until at least one measurable baseline and one measurable outcome are supported by evidence. Testimonials without operational numbers remain testimonials, not case studies.

## Architecture and boundaries

The site remains static HTML, CSS, and JavaScript. Reusable trust and analytics behavior should follow existing project conventions rather than introducing a framework.

- Google account settings remain external configuration.
- Tracking code emits events but never invents commercial outcomes.
- Offer copy reads from verified business facts.
- Author identity is represented consistently in visible HTML and JSON-LD.
- Case-study pages are content artifacts with a fixed evidence schema.

## Data flow

1. A visitor lands through search or another channel.
2. GA4 records page and product interactions.
3. A qualified CTA emits `generate_lead` and `whatsapp_click` with product/source context.
4. Search Console supplies query, page, country, device, and indexing data.
5. Reporting compares leads and revenue per 1,000 visits, not traffic alone.
6. Case-study CTAs use distinct source values so their contribution can be measured.

## Failure handling

- If Search Console OAuth requires user approval, stop at the Google consent screen and request only that approval.
- If `generate_lead` has not appeared in GA4, test the live CTA first and wait for ingestion rather than creating a key event blindly.
- If a fulfillment claim cannot be proven, remove or qualify it. Do not replace it with vague marketing language.
- If a proposed case study lacks numeric evidence, keep it as a testimonial draft.
- If JSON-LD or inline JavaScript fails parsing, do not deploy.

## Verification

Acceptance requires all of the following:

- Search Console property is accessible and the submitted sitemap can be inspected.
- A real live-site CTA produces `generate_lead` with expected parameters.
- GA4 shows `generate_lead` as a key event after event receipt.
- Every guarantee and bonus claim has a documented status and matching page copy.
- Author HTML and JSON-LD agree on identity and URLs.
- Case-study template rejects publication when baseline or outcome evidence is absent.
- Existing purchase links, Rp99.900 pricing, mobile rendering, canonical tags, and structured data remain valid.

## Rollout

Work proceeds in small independently verifiable commits: measurement access, offer audit, author trust, case-study template, then live regression verification. External account changes are recorded separately from source changes so failures can be isolated and rolled back without affecting the website.
