# Ads Injection System – Comprehensive Design, Audit, and Premium Integration

## 1) Executive Summary

- Purpose: Centralize the current implementation, identified gaps/risks, and a prioritized roadmap for the ads injection stack.
- Scope: Client injection, server APIs, data models, premium detector integration, measurement, security, compliance, performance, and admin/analytics.

## 2) Architecture Overview

- Client: `static/js/ads-injection.js` injects ads into page content using placement rules, premium detection, and IntersectionObserver viewability.
- Server: `routes/routes_ads.py` serves creatives and tracks events; `models.py` holds `Ad`, `AdPlacement`, `AdStats`.
- Styling: `static/css/ads-injection.css` for containers/wrappers; imitates page card visuals.
- Premium: `/api/subscriptions/check-premium-access` informs placement and whether to load ads.

## 3) What’s Implemented Today

| Area | Capabilities |
|------|--------------|
| Client injection | Placement rules by page type/section/position; lazy-load + IO; client soft frequency capping; ad close button; style alignment |
| Premium | Calls `/api/subscriptions/check-premium-access`; respects users who disabled ads; different placements for non-premium |
| Serving | POST `/ads/api/serve` filters active placements, random rotation, returns rendered HTML (internal or external) |
| Tracking | POST `/ads/api/track-impression`, POST `/ads/api/track-click`; rate limits + short-window dedupe; per-hour aggregation in `AdStats` |
| Models | `Ad`, `AdPlacement` (targeting incl. device/user type, location), `AdStats` |
| Styles | `.ad-placement-container`, `.ad-wrapper`, fade-in animations; in-stream variants |

## 4) Placement Matrix (Current)

| Page Type | Position(s) | Target Selector(s) | Notes |
|----------|--------------|--------------------|-------|
| home | top | `main` | prepend |
| home | after_n_items (3, 6) | `[data-group="latest-articles"] article` | in-stream |
| home | after_n_items (2, 4) | `[data-group="popular-news"] article` | in-stream |
| home | middle (mobile) | `main` | mobile-only |
| home | bottom | `main` | non-premium only |
| news | after_n_items (2, 5, 8) | `.news-card` | in-stream |
| album | after_n_items (1, 3, 6) | `.album-card` | in-stream |
| gallery | after_n_items (2, 5) | `.gallery-item` | in-stream |
| videos | after_n_items (2, 5) | `.video-card` | in-stream |
| about | middle | main content only | minimal |

Safety: navigation areas are avoided; selectors target main content.

## 5) API Surface

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/ads/api/serve` | No | Serve ads for a page/placement (page_type, section, position, position_value?, device_type?, max_ads?, user_has_premium?, user_should_show_ads?, card_style?) |
| POST | `/ads/api/track-impression` | No | Record impression (ad_id, event_id?) |
| POST | `/ads/api/track-click` | No | Record click (ad_id, event_id?) |
| GET | `/ads/analytics` | Yes | Analytics dashboard (admin) |

## 6) Premium Detector Integration (Summary)

- Uses the same endpoint as readers: `/api/subscriptions/check-premium-access`.
- Client fields: `hasPremiumAccess`, `shouldShowAds`, `premiumExpiresAt`.
- Behavior: If premium user disabled ads → skip injection; otherwise include premium context in serve request.

## 7) Measurement and Viewability

- Impression: IO threshold used; tracked via `/ads/api/track-impression` with short-window dedupe.
- Click: `/ads/api/track-click` on wrapper; may miss nested anchor clicks inside third-party code.
- Aggregation: `AdStats` per hour (impressions, clicks; device splits for impressions).

## 8) Gaps and Risks (Audit)

| Area | Gap/Risk |
|------|----------|
| Consent/Compliance | No CMP (GDPR/CCPA/TCF); no tcString/USP; no `ads.txt`/`app-ads.txt`; no DNT/COPPA gating |
| Ad tech | No GPT or Prebid; no line-item/slot mapping; no bid timeout or waterfall |
| Security | Unsanitized `innerHTML` for internal HTML ads; no sandboxed iframes; no CSP/Trusted Types |
| Measurement | No client `event_id` generation; weak duration-based viewability; clicks inside 3P HTML not reliably captured |
| Capping/Rotation | Client-only soft cap; no server-side per-user caps; no pacing; random-only rotation at runtime |
| Targeting | `location_targeting` not enforced (no geo-IP); UA-based device detection; no brand-safety/competitive exclusion |
| Performance/UX | CLS risk (no space reservation); no batching; no adblock handling; no infinite-scroll hooks |
| Admin/Analytics | Limited KPIs (no fill/viewable/eCPM/RPM); no A/B testing; no anomaly/IVT alerts |
| Accessibility/i18n | Non-localized label; missing ARIA; close button keyboard/`type="button"` not guaranteed |

## 9) Recommended Improvements (Prioritized)

| Priority | Area | Recommendations |
|---------:|------|-----------------|
| P0 | Compliance | Integrate CMP (TCF v2.2); block ad loading unless consent; pass tcString/USP; publish `ads.txt`/`app-ads.txt`; honor DNT; regional rules (GDPR/CPRA/COPPA) |
| P0 | Security | Sanitize internal HTML creatives; render 3P creatives in sandboxed iframes; enforce CSP; consider Trusted Types |
| P0 | Measurement | Generate UUID `event_id`; enforce duration-based viewability (≥ `viewabilityMinMs`) and track "viewable" metric; secure click redirect endpoint with signed URL + UTM; add `rel="nofollow noopener sponsored"` |
| P1 | Delivery | Add GPT slotting and/or Prebid.js; placement→slot mapping; bid timeout; collapse empty slots; server-side house-ads fallback when no fill |
| P1 | Capping/Rotation | Server-side frequency caps per user/device/IP and per-campaign; pacing; weighted rotation; respect per-placement "closed" state |
| P1 | Performance/UX | Reserve layout space (min-height/aspect-ratio) to avoid CLS; preconnect to ad domains; batch-serve multiple placements; debounce refresh; adblock detection and house-ad fallback; infinite-scroll hooks |
| P2 | Targeting | Geo-IP enforcement of `location_targeting`; competitive exclusion; brand-safety and sensitive-content rules |
| P2 | Admin/Analytics | KPIs: fill rate, viewable rate, eCPM/RPM by placement; A/B testing flags; anomaly/IVT alerts; export to GA4/BigQuery |
| P2 | Accessibility/i18n | Localize ad label; `role="region"` + `aria-labelledby`; keyboard focus and `type="button"` on close |

## 10) First Implementation Slice (Fast Wins)

1. Client: UUID `event_id` per impression; duration-based viewability timer; send `event_id` on impression and click.
2. Server: store `event_id`; extend `AdStats` with `viewable_impressions`.
3. Clicks: add secure redirect endpoint with URL signing and UTM; default link attrs (`rel`, `target`).
4. Security: sanitize internal creatives; sandbox third-party creatives.
5. Performance: batch-serve endpoint for multiple placements; reserve space in containers to prevent CLS.
6. CMP: block ad loading until consent; dev no-op.

## 11) KPIs and Reporting

| KPI | Definition | Source |
|-----|------------|--------|
| Impressions | Count of served impressions | `AdStats.impressions` |
| Viewable Impressions | IO threshold met for ≥ `viewabilityMinMs` | new field (to add) |
| Clicks | Count of clicks | `AdStats.clicks` |
| CTR | Clicks / Impressions | derived |
| Viewable Rate | Viewable / Impressions | derived |
| Fill Rate | Filled placements / Requested placements | server logs + analytics |
| eCPM | Revenue per 1000 impressions | integration (future) |
| RPM (page) | Revenue per 1000 pageviews | integration (future) |

## 12) Data Model Touchpoints

- `Ad` – content_type: image/text/html/google_ads; internal vs external; performance fields (impr/clicks/ctr).
- `AdPlacement` – targeting (page_type, section, position, position_value, device_type, user_type, location_targeting), rotation, display_frequency.
- `AdStats` – hourly aggregation; extend to include `viewable_impressions` (recommended).

## 13) Security and Privacy Controls

- Sanitization for internal HTML ads; sandboxed iframes for 3P ads.
- CSP tightened for scripts/frames; consider Trusted Types to block unsanitized sinks.
- CMP signals forwarded; respect DNT; avoid personal data in ad requests.

## 14) Performance Considerations

- Reserve space for all ad containers (min-height/aspect-ratio) to avoid CLS.
- Preconnect/preload to ad servers/CDN when possible.
- Batch requests; client caching; debounce refresh.

## 15) Accessibility and i18n

- Visible, localized "Advertisement" label.
- `role="region"` with `aria-labelledby` per ad block; ensure keyboard and screen-reader friendly close button.

## 16) Code References

| Path | Purpose |
|------|---------|
| `static/js/ads-injection.js` | Client injection, premium detection, IO viewability, event tracking |
| `static/css/ads-injection.css` | Ad containers/wrappers styling |
| `routes/routes_ads.py` | Serve and tracking endpoints; analytics route |
| `models.py` | `Ad`, `AdPlacement`, `AdStats` models |
| `docs/ADS_INJECTION_IMPROVEMENTS.md` | Navigation-safety and placement refinements |
| `docs/ADS_PREMIUM_DETECTOR_INTEGRATION.md` | Premium detector details |
| `docs/ADS_INJECTION_AUDIT.md` | Initial audit and prioritized improvements |

## 17) Appendix – Proposed Endpoint Additions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ads/api/serve/batch` | Accepts an array of placements; returns ads grouped by placementKey |
| GET | `/.well-known/ads.txt` | Declare authorized sellers |
| GET | `/app-ads.txt` | For app inventory (if applicable) |
| GET | `/ads/click` | Secure redirect for external clicks (signed, with UTM) |

---

This document merges and refines: `ADS_INJECTION_AUDIT.md`, `ADS_INJECTION_IMPROVEMENTS.md`, and `ADS_PREMIUM_DETECTOR_INTEGRATION.md`, providing a single source of truth for the ads injection stack’s current status and roadmap.
