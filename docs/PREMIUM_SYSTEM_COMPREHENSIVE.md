# Premium Content & Subscription – Comprehensive Design, Implementation, and Operations

## 1) Executive Summary

- Purpose: Combine premium content masking/filtering and subscription system documentation into a single, action-oriented reference.
- Scope: Data models, APIs, content filtering, UI components, ads interaction, security, KPIs, testing, and roadmap.

## 2) Architecture Overview

| Layer | Components | Purpose |
|------|------------|---------|
| Models | `User` (premium fields), `UserSubscription` | Store premium status and subscription lifecycle |
| APIs | `/api/subscriptions/*`, `/api/subscriptions/check-premium-access` | Manage plans, subscriptions, preferences, and premium checks |
| Content Filtering | `routes/utils/premium_content.py` | Server-side truncation of premium content for non-premium users |
| Frontend | `static/css/premium-content.css`, `static/js/premium-content.js`, templates | Mask overlay, stats display, interactions |
| Integration | Readers/templates, Ads Injection | Enforce premium access and ad preferences consistently |

## 3) Data Model Summary

| Model | Key Fields | Notes |
|-------|------------|-------|
| `User` | `has_premium_access: bool`, `premium_expires_at: DateTime`, `ad_preferences: JSON` | Preferences include `show_ads`, `ad_frequency`; helper methods for premium checks |
| `UserSubscription` | `user_id`, `subscription_type: {'monthly','yearly'}`, `status`, `start_date`, `end_date`, `payment_provider`, `payment_id`, `amount`, `currency`, `auto_renew` | Full lifecycle tracking |

## 4) API Surface

### 4.1 Public/User APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/subscriptions/plans` | List available subscription plans |
| POST | `/api/subscriptions/create` | Create subscription for current user |
| POST | `/api/subscriptions/cancel` | Cancel the current user’s active subscription |
| GET | `/api/subscriptions/status` | Get current user’s subscription state & preferences |
| POST | `/api/subscriptions/update-ad-preferences` | Update ad preferences (e.g., `show_ads`) |
| GET | `/api/subscriptions/check-premium-access` | Return `{ has_premium_access, should_show_ads, premium_expires_at }` |

### 4.2 Admin APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/subscriptions` | Paginated list of subscriptions |
| PUT | `/api/admin/subscriptions/<subscription_id>` | Update subscription |

## 5) Premium Content Filtering (Server-side)

- Non-premium users only receive truncated content; full content is never transmitted to unauthorized users.
- Entry point: `routes/utils/premium_content.py` with helpers:
  - `is_premium_user()`
  - `truncate_markdown_content(content, max_words=150)`
  - `process_premium_content(content, is_premium_content, max_words=150)`
- Typical flow:
```python
is_premium_content = news.is_premium or album.is_premium
processed_content, is_truncated, show_premium_notice = process_premium_content(
    news.content or "",
    is_premium_content,
    max_words=150,
)
html_content = markdown.markdown(processed_content, extensions=[...])
```

## 6) Frontend Integration

### 6.1 Templates
- Readers (`templates/public/reader.html`, `chapter_reader.html`) render:
  - Premium content container + stats
  - Mask overlay when `is_premium_content and is_truncated`

### 6.2 CSS and JS
- CSS: `static/css/premium-content.css` for responsive, accessible mask overlay and stats.
- JS: `static/js/premium-content.js` initializes interactions and stats rendering.

### 6.3 Example Markup (truncated)
```html
<div class="premium-content-container {% if is_truncated %}truncated{% endif %}">
  <div id="article-body" class="prose prose-lg">{{ html_content | safe }}</div>
  {% if is_premium_content and is_truncated %}
  <div id="content-mask-{{ news.id }}" class="content-mask-overlay"> ... </div>
  {% endif %}
</div>
```

## 7) Ads Integration

- Premium users can disable ads via preferences. The Ads Injection system should call `/api/subscriptions/check-premium-access` before injecting ads.
- Behavior:
  - If `has_premium_access` and `should_show_ads` is false → suppress ads.
  - Otherwise, send context flags with ad serve requests for targeting.

## 8) Security and Privacy

- Server-side enforcement: content is truncated before conversion to HTML and delivery.
- Premium checks validated against DB (no client-side bypass).
- Mask overlay is UX only; not a security boundary.
- Audit: log subscription changes; validate payloads.

## 9) KPIs and Metrics

| KPI | Definition |
|-----|-----------|
| Premium Conversion | % of readers converting to premium |
| Engagement | Read time/return rate on premium content |
| Revenue | MRR/ARR from subscriptions |
| Ad Suppression Rate | % of sessions with ads disabled (premium) |

## 10) Testing

- Script: `helper/test_subscription_system.py` to create sample users and validate flows.
- Coverage should include:
  - Premium detection (active/expired/none)
  - Content filtering/truncation & mask conditions
  - API endpoints for plans/create/cancel/status, ad preferences, premium check
  - Reader template behavior and stats visibility

## 11) Configuration

- Environment variables (future payment integration):
```env
PAYMENT_PROVIDER=stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
DEFAULT_SUBSCRIPTION_CURRENCY=IDR
SUBSCRIPTION_AUTO_RENEW=true
```
- Truncation length (`max_words`) configurable at call site.

## 12) Workflows

1) Premium Access:
- Visit premium article → server checks premium → returns full or truncated content → overlay shown if truncated.

2) Subscription Creation:
- User selects plan → POST create → status reflects active subscription → `has_premium_access=True` until `end_date`.

3) Ad Display:
- Page loads → `/api/subscriptions/check-premium-access` → Ads Injection honors `should_show_ads`.

## 13) Roadmap

- Payment gateway integrations (Stripe/PayPal)
- Advanced analytics (conversion funnels, cohort retention)
- Tiered plans and trials; referral incentives
- Personalization: premium content recommendations
- A/B testing: overlay variants, preview lengths

## 14) Reference Snippets

### Premium Checks
```python
def is_premium_user() -> bool:
    if not current_user.is_authenticated:
        return False
    return current_user.has_active_premium_subscription()
```

### Truncation
```python
def truncate_markdown_content(content: str, max_words: int = 150) -> tuple[str, bool]:
    words = re.findall(r"\S+|\n+", content)
    if len(words) <= max_words:
        return content, False
    truncated = ''.join(words[:max_words])
    if truncated and not truncated.endswith('\n'):
        truncated += '...'
    return truncated, True
```

---

This document supersedes and consolidates: `PREMIUM_CONTENT_SYSTEM.md` and `PREMIUM_SYSTEM_IMPLEMENTATION.md`. Use this as the single source of truth for premium content and subscriptions.
