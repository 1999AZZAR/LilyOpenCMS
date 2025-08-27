# Comment & Rating System – Comprehensive Design, Implementation, and Improvements

## 1) Executive Summary

- Purpose: Consolidate the system design, current implementation, recent improvements, APIs, admin tools, security posture, analytics, and a clear action roadmap for the comment and rating features.
- Scope: Database models, endpoints, frontend behavior, moderation, spam detection, performance, accessibility, testing, and future enhancements.

## 2) Architecture Overview

- Backend models: `Comment`, `Rating`, `CommentLike`, `CommentReport` (SQLAlchemy).
- APIs: REST endpoints for CRUD of comments/ratings, likes/dislikes, reporting, analytics.
- Frontend: Threaded comments UI, infinite scroll (IntersectionObserver), rating widgets with multi-instance support.
- Admin: Moderation interfaces for comments and ratings with analytics dashboards.

## 3) Data Model Summary

| Model | Key Fields | Purpose |
|-------|------------|---------|
| `Comment` | `content`, `content_type`, `content_id`, `user_id`, `parent_id`, `is_approved`, `is_spam`, `is_deleted`, timestamps | Nested comments on news/albums with moderation/spam flags |
| `Rating` | `rating_value` (1-5), `content_type`, `content_id`, `user_id`, timestamps; unique (`user_id`,`content_type`,`content_id`) | One rating per user per content with stats aggregation |
| `CommentLike` | `is_like`, `user_id`, `comment_id`, `is_deleted`, timestamps; unique (`user_id`,`comment_id`) | Like/dislike votes on comments |
| `CommentReport` | `reason`, `description`, `is_resolved`, `user_id`, `comment_id`, `resolved_by`, timestamps | User reports, resolution workflow |

## 4) API Surface

### 4.1 Comment Endpoints

| Method | Endpoint | Params/Body | Description |
|--------|----------|-------------|-------------|
| GET | `/api/comments/<content_type>/<content_id>` | `page`, `per_page` | List paginated comments for content |
| POST | `/api/comments` | `{ content, content_type, content_id, parent_id? }` | Create a comment |
| PUT | `/api/comments/<comment_id>` | `{ content }` | Update own comment |
| DELETE | `/api/comments/<comment_id>` | — | Delete own comment |
| POST | `/api/comments/<comment_id>/like` | `{ is_like: boolean }` | Like or dislike a comment |
| POST | `/api/comments/<comment_id>/report` | `{ reason, description? }` | Report a comment |

### 4.2 Rating Endpoints

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| GET | `/api/ratings/<content_type>/<content_id>` | — | Get rating stats for content |
| POST | `/api/ratings` | `{ rating_value (1-5), content_type, content_id }` | Create or update rating |
| DELETE | `/api/ratings/<content_type>/<content_id>` | — | Remove user rating for content |
| GET | `/api/ratings/stats` | — | Global rating analytics overview |
| GET | `/api/ratings/user/<user_id>` | — | All ratings by a user |

### 4.3 Admin Endpoints

| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/admin/comments` | Moderation list (filters: status, content_type, page) |
| POST | `/admin/comments/<comment_id>/approve` | Approve |
| POST | `/admin/comments/<comment_id>/reject` | Reject |
| POST | `/admin/comments/<comment_id>/mark-spam` | Mark spam |
| POST | `/admin/comments/<comment_id>/delete` | Admin delete |
| GET | `/admin/ratings` | Ratings management list |
| POST | `/admin/ratings/<rating_id>/delete` | Admin delete rating |
| GET | `/admin/ratings/analytics` | Ratings analytics dashboard |

## 5) Frontend Features

### 5.1 Comments UI
- Nested threads with `parent_id`.
- Infinite scroll: initial 12 comments, load more at 80% scroll via IntersectionObserver.
- Loading indicators and empty state messaging.
- Scrollable containers with themed thin scrollbars; responsive and accessible.

### 5.2 Ratings UI
- 5-star interactive widgets.
- Multi-instance support across pages (album detail, chapter reader, reader).
- Auto-detection and initialization via data attributes.

## 6) Recent Improvements (Refinements)

| Area | Improvement |
|------|-------------|
| Auto-loading | IntersectionObserver-based infinite scroll; reduced initial load to 12 |
| UX | Better loading states, hover effects, smooth transitions, friendly empty state |
| CSS | Scroll container with max-height; dark mode variants; auto-load indicator styles |
| Ratings | Multi-instance initialization; unique identifiers; robust error handling |
| Templates | Fixed and unified init on album detail, chapter reader, reader |
| JS | Improved state mgmt and logging; event delegation; cleanup |

## 7) Security and Moderation

- Comment moderation: auto-approval for trusted roles, manual for new users.
- Spam detection heuristics: excessive links, caps ratio, repetitive characters, flood control by recent comments.
- Rate limiting for comment creation and actions.
- Ratings: unique per user per content; validate 1-5; honor suspended users.
- Reports: valid reasons, duplicate prevention, resolution tracking.

## 8) Analytics and KPIs

| KPI | Definition | Source |
|-----|------------|--------|
| Comments per content | Count of comments per content | DB queries/analytics |
| Moderation queue | Pending/approved/rejected/spam counts | Admin dashboard |
| Engagement | Active commenters, reply depth/frequency | Analytics views |
| Ratings avg | Average rating per content and overall | Stats endpoint |
| Rating distribution | 1-5 star breakdown | Stats endpoint |
| Top-rated content | Highest avg with sufficient count | Stats endpoint |

## 9) Permissions

| Permission | Capability |
|-----------|-----------|
| `comments.read` | View comments and reports |
| `comments.approve` | Approve/reject comments |
| `comments.delete` | Delete comments |
| `ratings.read` | View ratings and analytics |
| `ratings.delete` | Delete ratings |

## 10) Configuration

```env
# Comment system
COMMENT_MAX_LENGTH=5000
COMMENT_SPAM_LINK_LIMIT=3
COMMENT_SPAM_CAPS_RATIO=0.7
COMMENT_RATE_LIMIT=10

# Rating system
RATING_MIN_VALUE=1
RATING_MAX_VALUE=5
RATING_CACHE_TTL=3600
```

## 11) Workflows

- Comment creation: validate → spam checks → auto-approve (trusted) or pending → visible → subject to admin moderation.
- Ratings: check existing → create/update → recalc stats → display.
- Moderation: admin reviews pending → approves/rejects/marks spam → notifies user (if configured).

## 12) Performance

- Caching: rating stats, comment counts, user moderation permissions, spam analysis results.
- DB: proper indexes (content_type, content_id, user_id, created_at), composite uniqueness for ratings, soft deletes for comments.
- Queries: eager loading of user data; optimized counts; bulk ops for admin.

## 13) Testing

- Coverage: comment creation, rating boundaries, spam detection, moderation flows, permissions, API endpoints.
- Scripts: `test/test_comment_rating_system.py`, `test/test_spam_detection.py`, `test/test_rating_analytics.py`.
- Manual checklist: infinite scroll behavior, indicators, multi-instance ratings, dark mode, mobile responsiveness, IO support.

## 14) Accessibility & UX

- Keyboard focus management in forms and moderation dialogs.
- Sufficient contrast and focus states; ARIA labels for buttons (like/dislike/report).
- Clear empty/error states; loading indicators with screen reader support.

## 15) Roadmap and Action Items

### 15.1 Short-term (P0/P1)
- Improve spam detection with additional signals (language models, reputation scores) while avoiding high false positives.
- Add server-side rate limiting if not already enforced on endpoints.
- Expose comment edit windows (grace period) with audit trail; prevent stealth edits after moderation.
- Add per-user comment throttling by IP/UA and captcha challenge on anomalies.
- Harden permissions with granular policies for moderators vs admins.
- Expand analytics: per-content engagement trends, moderation SLA metrics.

### 15.2 Mid-term (P2)
- Real-time updates via WebSocket for live comment streams.
- Rich text (safe markdown) with sanitization and media constraints.
- Advanced filtering/sorting: by rating, sentiment, popularity, staff picks.
- Comment reactions beyond like/dislike.
- Full-text search across comments (index + API).

### 15.3 Long-term (P3)
- ML-powered spam detection and auto-moderation suggestions.
- User reputation system influencing visibility and moderation priority.
- Cross-content user activity insights and personalized highlights.

## 16) Code References

- Models: `models.py` (`Comment`, `Rating`, `CommentLike`, `CommentReport`)
- APIs: routes for comments/ratings admin and public
- Frontend: `static/js/comment-system.js`, `static/js/rating-system.js`, `static/css/comment-rating.css`
- Templates: `templates/public/album_detail.html`, `templates/public/chapter_reader.html`, `templates/public/reader.html`

---

This document merges and refines: `COMMENT_RATING_SYSTEM.md` and `comment-rating-improvements.md`, providing a single source of truth for the comment and rating stack.
