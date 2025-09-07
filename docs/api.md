# LilyOpenCMS API & Endpoint Reference

A comprehensive, grouped list of all CRUD and callable endpoints in LilyOpenCMS, including HTTP method, path, authentication, and description.

---

## 🌐 **Public API Endpoints for Multiplatform Access**

These endpoints provide JSON equivalents for resources previously only available as HTML pages. All public API endpoints are read-only (`GET` requests) and do not require authentication, enabling mobile apps, desktop clients, and third-party integrations.

### **News Public API**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/public/news/<int:news_id>`         | No   | Get single news article details with rich data enrichment |
| GET    | `/api/public/news`                       | No   | Get paginated list of news with filtering, search, and sorting |
| GET    | `/api/public/news/<int:news_id>/detail` | No | Get news detail with comprehensive data (new endpoint) |
| GET    | `/api/public/news/list` | No | Get news list using existing search logic (new endpoint) |

### **Albums Public API**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/public/albums/<int:album_id>`      | No   | Get single album details with chapters and metadata |
| GET    | `/api/public/albums`                     | No   | Get paginated list of albums with filtering and sorting |
| GET    | `/api/public/albums/<int:album_id>/chapters/<int:chapter_id>` | No | Get single chapter details with navigation |
| GET    | `/api/public/albums/<int:album_id>/detail` | No | Get album detail with chapters (new endpoint) |
| GET    | `/api/public/albums/<int:album_id>/chapters/<int:chapter_id>/detail` | No | Get chapter detail with content (new endpoint) |
| GET    | `/api/public/albums/list` | No | Get albums list using existing search logic (new endpoint) |

### **User Profile Public API**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/public/user/<username>`            | No   | Get public user profile information |
| GET    | `/api/public/user/<username>/stats`      | No   | Get user statistics and performance metrics |
| GET    | `/api/public/user/<username>/library`    | No   | Get user's public library and reading history |

### **Categories & Tags Public API**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/public/categories`                 | No   | Get list of active categories with content counts |
| GET    | `/api/public/tags`                       | No   | Get list of tags with optional search filtering |

### **Comments Public API**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/public/comments/<string:content_type>/<int:content_id>` | No | Get comments for content with pagination |
| GET    | `/api/public/comments/<int:comment_id>/replies` | No | Get comment replies with pagination |

### **Unified Search Public API**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/public/search`                     | No   | Cross-content search across news and albums |

### **Homepage Public API**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/public/homepage`                   | No   | Get comprehensive homepage data with featured content |

**Features:**
- **Premium Content Handling**: Returns limited info for premium content with appropriate messaging
- **Rich Data Enrichment**: Related content, user info, media assets, and metadata
- **Advanced Filtering**: Search, categories, status, and content type filtering
- **Pagination**: Configurable page sizes with navigation metadata
- **Sorting Options**: Latest, popular, oldest, and relevance-based sorting
- **Error Handling**: Proper HTTP status codes and JSON error responses
- **No Authentication**: Public access for multiplatform development

---

## News (Cerita & Bab)
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/news`                              | Yes  | List news articles/stories (with filters)   |
| POST   | `/api/news`                              | Yes  | Create a new story/chapter (accepts: title, content, category, date, age_rating, is_news, is_main_news, is_premium, is_visible, writer, external_source, image_id, prize, prize_coin_type; optional `album_id` for chapter context). Note: default visibility is hidden (is_visible=false) unless explicitly published. |
| GET    | `/api/news/<news_id>`                    | Yes  | Get story/chapter details                   |
| PUT    | `/api/news/<news_id>`                    | Yes  | Update story/chapter (same fields as POST)  |
| DELETE | `/api/news/<news_id>`                    | Yes  | Delete story/chapter (admin-tier users only) |
| POST   | `/api/news/<news_id>/request-deletion`   | Yes  | Request story/chapter deletion (non-admin users) |
| GET    | `/api/news/deletion-requests`            | Yes  | Get story/chapter deletion requests (admin only) |
| POST   | `/api/news/<news_id>/approve-deletion`   | Yes  | Approve story/chapter deletion request (admin only) |
| POST   | `/api/news/<news_id>/reject-deletion`    | Yes  | Reject story/chapter deletion request (admin only) |
| PATCH  | `/api/news/<news_id>/visibility`         | Yes  | Toggle story/chapter visibility             |
| GET    | `/api/news/owned`                        | Yes  | List stories/chapters owned by current user |
| POST   | `/api/news/<news_id>/track-share`        | No   | Track a share action for a story/chapter    |
| GET    | `/api/news/<news_id>/share-data`         | No   | Get share counts for a story/chapter        |
| GET    | `/api/search/news`                       | No   | Unified news search API (supports: q, category, category_name, tag, sort, type, page, per_page) - type options: general, news, articles, utama - sort options: newest, oldest, popular, least-popular |
| POST   | `/api/news/upload-docx`                  | Yes  | Upload DOCX file and convert to story/chapter (accepts: file, title, category, date, age_rating, writer, external_source, prize, prize_coin_type) |

> Admin Create/Edit Flow: Use `/settings/create_news` with optional `news_id` to edit. If `album_id` is present, successful create/edit redirects back to `/admin/albums/<album_id>/chapters`; otherwise redirects to `/settings/manage_news`. In edit mode, saving keeps the current visibility unless explicitly changed (e.g., Publish action).

## Premium Content & Coin System
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/premium/check-access`              | Yes  | Check user's premium access status          |
| GET    | `/api/premium/content-stats`             | No   | Get premium content statistics              |
| POST   | `/api/premium/process-content`           | No   | Process content for premium filtering       |
| GET    | `/api/premium/user-status`               | Yes  | Get current user's premium status           |
| POST   | `/api/news/<news_id>/purchase`           | Yes  | Purchase access to premium story content with coins |
| GET    | `/api/user/coins`                        | Yes  | Get user's coin balance and premium status  |

## Albums
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/albums`                            | Yes  | List albums (with filters)                  |
| POST   | `/api/albums`                            | Yes  | Create a new album                          |
| GET    | `/api/albums/<album_id>`                 | Yes  | Get album details                           |
| PUT    | `/api/albums/<album_id>`                 | Yes  | Update album                                |
| DELETE | `/api/albums/<album_id>`                 | Yes  | Delete album (admin-tier users only)       |
| POST   | `/admin/albums/<album_id>/request-deletion` | Yes | Request album deletion (admin interface)   |
| POST   | `/api/albums/<album_id>/request-deletion` | Yes | Request album deletion (user interface)   |
| GET    | `/admin/albums/deletion-requests`        | Yes  | Get album deletion requests (admin only)   |
| POST   | `/admin/albums/<album_id>/approve-deletion` | Yes | Approve album deletion request (admin only) |
| POST   | `/admin/albums/<album_id>/reject-deletion` | Yes | Reject album deletion request (admin only) |
| PATCH  | `/api/albums/<album_id>/visibility`      | Yes  | Toggle album visibility                     |
| PATCH  | `/api/albums/<album_id>/archive`         | Yes  | Archive album                               |
| PATCH  | `/api/albums/<album_id>/unarchive`       | Yes  | Unarchive album                             |
| POST   | `/api/albums/<album_id>/chapters`        | Yes  | Add chapter to album                        |
| DELETE | `/api/albums/<album_id>/chapters/<chapter_id>` | Yes | Remove chapter from album           |
| POST   | `/api/albums/<album_id>/track-share`     | No   | Track a share action for an album           |
| GET    | `/api/albums/<album_id>/share-data`      | No   | Get share counts for an album               |
| GET    | `/api/search/albums`                     | No   | Search albums across entire database (supports: q, category, status, rating, sort, page, per_page) - sort options: newest, oldest, popular, least-popular, most-viewed, least-viewed, highest-rated |
| GET    | `/` or `/beranda`                        | No   | Homepage with dynamic design support (news-focused: main_news, latest_articles, latest_news, popular_news, latest_videos, latest_images, featured_albums, categories with news_count) (albums-focused: featured_albums, latest_albums, popular_albums, best_albums, ongoing_albums, best_completed_albums, categories with album_count) |

### Albums Admin (Blueprint pages and JSON utilities)
| Method  | Endpoint                                                     | Auth | Description |
|---------|--------------------------------------------------------------|------|-------------|
| GET     | `/admin/albums/dashboard`                                    | Yes  | Album management dashboard with stats and quick actions |
| GET     | `/admin/albums/list`                                         | Yes  | Albums list with filters and pagination |
| GET     | `/admin/albums/<album_id>`                                   | Yes  | Album detail page with chapter list |
| GET/POST| `/admin/albums/create`                                       | Yes  | Create album page and JSON submit (modal-compatible) |
| GET/POST| `/admin/albums/<album_id>/edit`                              | Yes  | Edit album page and JSON submit (modal-compatible) |
| POST    | `/admin/albums/<album_id>/delete`                            | Yes  | Delete album (JSON) |
| POST    | `/admin/albums/<album_id>/toggle-visibility`                 | Yes  | Toggle album visibility (JSON) |
| POST    | `/admin/albums/<album_id>/toggle-type`                       | Yes  | Toggle premium/regular type (JSON) |
| POST    | `/admin/albums/<album_id>/archive`                           | Yes  | Toggle archive status (JSON) |
| POST    | `/admin/albums/bulk/toggle-visibility`                       | Yes  | Bulk toggle visibility (JSON) |
| POST    | `/admin/albums/bulk/toggle-type`                             | Yes  | Bulk toggle type (JSON) |
| POST    | `/admin/albums/bulk/archive`                                 | Yes  | Bulk archive albums (JSON) |
| GET     | `/admin/albums/<album_id>/chapters`                          | Yes  | Chapters management page for an album |
| POST    | `/admin/albums/<album_id>/chapters/add`                      | Yes  | Add chapter (JSON) - **FIXED: Updates album total_chapters count** |
| POST    | `/admin/albums/<album_id>/chapters/<chapter_id>/edit`        | Yes  | Edit chapter (JSON) |
| POST    | `/admin/albums/<album_id>/chapters/<chapter_id>/remove`      | Yes  | Remove chapter (JSON) - **FIXED: Updates album total_chapters count** |
| POST    | `/admin/albums/<album_id>/chapters/<chapter_id>/move`        | Yes  | Move chapter up/down in order (JSON) |
| POST    | `/admin/albums/<album_id>/chapters/<chapter_id>/toggle-visibility` | Yes  | Toggle chapter visibility (JSON) |
| GET     | `/admin/albums/api/search-news`                              | Yes  | Search owned stories to add as chapters (JSON) - **UPDATED: Shows all owned stories regardless of visibility** |
| GET     | `/admin/albums/api/album-stats/<album_id>`                   | Yes  | Get album statistics (JSON) |
| GET     | `/admin/albums/<album_id>/data`                              | Yes  | Get album data for edit modal (JSON) |
| GET     | `/admin/albums/<album_id>/chapters/data`                     | Yes  | Get chapters data for modal (JSON) |
| GET     | `/admin/albums/analytics`                                    | Yes  | Albums analytics dashboard |
| GET     | `/settings/content-deletion-requests`                       | Yes  | Content deletion requests management page |

## Comments
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/comments/<content_type>/<content_id>` | No  | Get comments for content (news/album) - **FIXED: Enhanced error handling and robust user serialization** |
| POST   | `/api/comments`                          | Yes  | Create a new comment                        |
| PUT    | `/api/comments/<comment_id>`             | Yes  | Update comment - **UPDATED: Returns success field for frontend compatibility** |
| DELETE | `/api/comments/<comment_id>`             | Yes  | Delete comment (soft delete) - **UPDATED: Returns success field for frontend compatibility** |
| POST   | `/api/comments/<comment_id>/like`        | Yes  | Like/dislike comment                        |
| POST   | `/api/comments/<comment_id>/report`      | Yes  | Report comment                              |
| GET    | `/api/comments/reports`                  | Yes  | Get comment reports (admin)                 |
| PUT    | `/api/comments/<comment_id>/moderate`    | Yes  | Moderate comment (approve/reject)           |

## Ratings
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/ratings/<content_type>/<content_id>` | No  | Get ratings for content (news/album)        |
| POST   | `/api/ratings`                           | Yes  | Create/update rating                        |
| DELETE | `/api/ratings/<content_type>/<content_id>` | Yes | Delete rating                               |
| GET    | `/api/ratings/stats`                     | No   | Get overall rating statistics               |
| GET    | `/api/ratings/user/<user_id>`            | No   | Get user's ratings                          |
| GET    | `/api/ratings/album/<album_id>/weighted` | No  | Get weighted rating statistics for album    |
| GET    | `/api/ratings/analytics`                 | Yes  | Get rating analytics (admin)                |

## Users
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/users`                             | Yes  | List users with pagination, search, and filtering (role, status, verification) |
| POST   | `/api/users`                             | Yes  | Create a new user with role assignment and premium status |
| GET    | `/api/users/<user_id>/details`           | Yes  | Get comprehensive user details and statistics |
| POST   | `/api/users/<user_id>/reset-password`    | Yes  | Reset user password (admin only) |
| GET    | `/api/users/stats`                       | Yes  | Get overall user statistics (total, active, premium, pending, role distribution) |
| GET    | `/api/pending/stats`                     | Yes  | Get pending registration statistics |
| GET    | `/api/users/<user_id>/performance`       | Yes  | Get user performance metrics                |
| GET    | `/api/users/performance/leaderboard`     | Yes  | Get user leaderboard (fixed: now includes full names) |
| GET    | `/api/registrations/pending`             | Yes  | Get pending registrations (fixed: proper serialization) |
| GET    | `/api/users/performance/report`          | Yes  | Get user performance report                 |
| GET    | `/api/users/<user_id>/performance/export`| Yes  | Export user performance data (fixed: now includes full names) |
| PATCH  | `/api/users/<user_id>/verify`            | Yes  | Verify user                                 |
| PATCH  | `/api/users/<user_id>/status`            | Yes  | Activate/deactivate user                    |
| PUT    | `/api/users/<user_id>`                   | Yes  | Update user details (fixed: no more method errors) |
| DELETE | `/api/users/<user_id>`                   | Yes  | Delete user (fixed: proper cascade deletion) |
| POST   | `/api/users/bulk/status`                 | Yes  | Bulk update user status                     |
| POST   | `/api/users/bulk/role`                   | Yes  | Bulk update user roles                      |
| POST   | `/api/users/bulk/verify`                 | Yes  | Bulk verify users                           |
| POST   | `/api/users/bulk/suspend`                | Yes  | Bulk suspend users                          |
| POST   | `/api/users/bulk/delete`                 | Yes  | Bulk delete users                           |
| POST   | `/api/users/bulk/export`                 | Yes  | Bulk export users                           |
| GET    | `/api/user/role`                         | Yes  | Get current user's role                     |
| GET    | `/api/settings/verified-users`           | Yes  | List verified users                         |
| POST   | `/api/users/<user_id>/suspend`           | Yes  | Suspend user                                |
| POST   | `/api/users/<user_id>/unsuspend`         | Yes  | Unsuspend user                              |
| GET    | `/api/users/deletion-requests`           | Yes  | Get pending account deletion requests (admin only) |
| POST   | `/api/users/<user_id>/approve-deletion`  | Yes  | Approve account deletion request (admin only) |
| POST   | `/api/users/<user_id>/reject-deletion`   | Yes  | Reject account deletion request (admin only) |
| GET    | `/api/users/<user_id>/activities`        | Yes  | Get user activities (fixed: proper serialization) |

## User Profile System
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/user/<username>`                       | No   | User profile page (Home tab)               |
| GET    | `/user/<username>?tab=list`              | No   | User profile page (List tab) - **UPDATED: Unified card design matching other profile pages** |
| GET    | `/user/<username>/library`               | No   | User's library page (saved content)         |
| GET    | `/user/<username>/stories`               | No   | User's stories page (drafts & published)    |
| GET    | `/user/<username>/stats`                 | No   | User's statistics page (analytics)           |
| GET    | `/user/<username>/following?tab=following` | No | User's following list page                 |
| GET    | `/user/<username>/following?tab=followers` | No | User's followers list page                  |
| GET    | `/user/<username>/settings`              | Yes  | User's settings page (account management)  |
| GET    | `/user/<username>/stories/create`        | Yes  | User-friendly story creation page           |
| POST   | `/api/follow/<int:user_id>`              | Yes  | Follow/unfollow a user                     |
| POST   | `/api/profile/update`                    | Yes  | Update user profile information             |
| POST   | `/api/write-access/request`              | Yes  | Request write access (for general users)   |
| GET    | `/api/write-access-requests`            | Yes  | Get write access requests (admin only)      |
| POST   | `/api/write-access-requests/<request_id>/approve` | Yes | Approve write access request (admin only) |
| POST   | `/api/write-access-requests/<request_id>/reject` | Yes | Reject write access request (admin only)  |
| POST   | `/api/library/add`                       | Yes  | Add content to user's library              |
| POST   | `/api/library/remove`                    | Yes  | Remove content from user's library         |
| GET    | `/api/library/check`                     | Yes  | Check if content is in user's library      |
| POST   | `/api/reading-history/record`            | Yes  | Record content in reading history          |

## User Library & Reading History
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/library`                           | Yes  | Get user's saved library items (news/albums) |
| POST   | `/api/library`                           | Yes  | Add item to user's library                  |
| DELETE | `/api/library`                           | Yes  | Remove item from user's library             |
| GET    | `/api/reading-history`                   | Yes  | Get user's reading history                  |

## User Comment Management
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| PUT    | `/api/comments/<comment_id>`             | Yes  | Update user's own comment (inline editing in library.html) |
| DELETE | `/api/comments/<comment_id>`             | Yes  | Delete user's own comment (with confirmation) |

## Achievement System & Coin Management
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/achievements/categories`            | No   | List achievement categories                 |
| GET    | `/api/achievements`                       | No   | List all achievements                       |
| GET    | `/api/achievements/<achievement_id>`      | No   | Get achievement details                     |
| GET    | `/api/user/achievements`                  | Yes  | Get current user's achievements             |
| GET    | `/api/user/achievements/summary`          | Yes  | Get user's achievement summary (points, level, streaks) |
| GET    | `/api/user/streaks`                       | Yes  | Get user's streak information               |
| GET    | `/api/user/points`                        | Yes  | Get user's points and level information     |
| GET    | `/api/user/points/transactions`           | Yes  | Get user's point transaction history        |
| POST   | `/api/achievements/track/login`           | Yes  | Track user login for streak achievements    |
| POST   | `/api/achievements/track/activity`        | Yes  | Track user activity for activity streaks    |
| POST   | `/api/achievements/track/reading`         | Yes  | Track content reading for reading streaks   |
| POST   | `/api/achievements/track/news-creation`   | Yes  | Track news article creation                 |
| POST   | `/api/achievements/track/album-creation`  | Yes  | Track album creation                        |
| POST   | `/api/achievements/track/image-upload`    | Yes  | Track image upload                          |
| POST   | `/api/achievements/track/comment`         | Yes  | Track comment creation                      |
| POST   | `/api/achievements/track/rating`          | Yes  | Track rating creation                       |
| POST   | `/api/achievements/track/comment-like`    | Yes  | Track comment like/dislike                  |
| GET    | `/api/achievements/leaderboard`           | No   | Get achievement leaderboard                 |
| GET    | `/api/achievements/stats`                 | Yes  | Get achievement system statistics (admin)   |
| GET    | `/api/user/coins`                         | Yes  | Get user's coin balance (achievement & topup coins) |
| POST   | `/api/user/coins/add-achievement`         | Yes  | Add achievement coins to user balance       |
| POST   | `/api/user/coins/add-topup`               | Yes  | Add topup coins to user balance             |
| POST   | `/api/user/coins/spend`                   | Yes  | Spend coins for content purchase            |
| GET    | `/api/user/coins/transactions`            | Yes  | Get user's coin transaction history         |
| GET    | `/api/user/coins/can-afford`              | Yes  | Check if user can afford content with coins |

## Images
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/images`                            | Yes  | List images (with filters: page, per_page, visibility, all_users) |
| POST   | `/api/images`                            | Yes  | Upload a new image                          |
| GET    | `/api/images/<image_id>`                 | Yes  | Get image details                           |
| PUT    | `/api/images/<image_id>`                 | Yes  | Update image                                |
| DELETE | `/api/images/<image_id>`                 | Yes  | Delete image                                |
| PATCH  | `/api/images/<image_id>/visibility`      | Yes  | Toggle image visibility                     |
| POST   | `/api/images/bulk-delete`                | Yes  | Bulk delete images                          |
| POST   | `/api/images/bulk-visibility`            | Yes  | Bulk update image visibility                |
| GET    | `/api/images/<image_id>/usage`           | Yes  | Get image usage statistics                  |

> **Image Security & Ownership Filtering**:
> - **Default upload visibility**: Uploads by custom roles Writer/Editor default to hidden; uploads by others default to visible (can be overridden via is_visible form value).
> - **Ownership-based access control**:
>   - **Admin/Superuser/Subadmin**: Can see all images (no restrictions)
>   - **Editor**: Own images + assigned writers' images + admin/suadmin visible images
>   - **Regular users**: Own images + admin/suadmin visible images
> - **`all_users=true` parameter**: When specified, applies proper ownership filtering:
>   - Regular users see: own images + admin/suadmin images marked as visible
>   - Editors see: own images + assigned writers' images + admin/suadmin images marked as visible
>   - Admins see: all images (no filtering)
> - **Security**: No cross-contamination - users cannot see images from other regular users
> - **Story creation**: Image picker uses `all_users=true` with proper ownership filtering for secure image selection

## Videos (YouTube)
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/youtube_videos`                    | Yes  | List YouTube videos                         |
| POST   | `/api/youtube_videos`                    | Yes  | Add a new YouTube video                     |
| GET    | `/api/youtube_videos/<video_id>`         | Yes  | Get YouTube video details                   |
| PUT    | `/api/youtube_videos/<video_id>`         | Yes  | Update YouTube video                        |
| DELETE | `/api/youtube_videos/<video_id>`         | Yes  | Delete YouTube video                        |
| POST   | `/api/youtube_videos/bulk-delete`        | Yes  | Bulk delete YouTube videos                  |
| POST   | `/api/youtube_videos/bulk-visibility`    | Yes  | Bulk update video visibility                |
| GET    | `/api/youtube_videos/latest`             | Yes  | Get latest YouTube videos                   |

## Categories & Category Groups
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/categories`                        | Yes  | List categories (supports `?grouped=true` for hierarchical view) |
| POST   | `/api/categories`                        | Yes  | Create a new category (accepts: name, description, group_id, display_order) |
| PUT    | `/api/categories/<category_id>`          | Yes  | Update category (accepts: name, description, group_id, display_order) |
| DELETE | `/api/categories/<category_id>`          | Yes  | Delete category                             |
| POST   | `/api/categories/<category_id>/safe-delete` | Yes | Safe delete category with dependency reassignment |
| GET    | `/api/category-groups`                   | Yes  | List category groups                         |
| POST   | `/api/category-groups`                   | Yes  | Create a new category group (accepts: name, description, display_order) |
| PUT    | `/api/category-groups/<group_id>`        | Yes  | Update category group (accepts: name, description, display_order) |
| DELETE | `/api/category-groups/<group_id>`        | Yes  | Delete category group                        |

## Tags
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/tags`                              | No  | List tags                                   |

## Navigation Links
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/navigation-links`                  | Yes  | List navigation links                       |
| POST   | `/api/navigation-links`                  | Yes  | Create a new navigation link                |
| PUT    | `/api/navigation-links/<link_id>`        | Yes  | Update navigation link                      |
| DELETE | `/api/navigation-links/<link_id>`        | Yes  | Delete navigation link                      |
| PUT    | `/api/navigation-links/bulk-update`      | Yes  | Bulk update navigation links status         |
| DELETE | `/api/navigation-links/bulk-delete`      | Yes  | Bulk delete navigation links                |
| POST   | `/api/navigation-links/copy`             | Yes  | Copy navigation links between locations     |

## Roles & Permissions
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/roles`                             | Yes  | List roles (backup implementation in routes_users.py) |
| POST   | `/api/roles`                             | Yes  | Create a new role                           |
| PUT    | `/api/roles/<role_id>`                   | Yes  | Update role                                 |
| DELETE | `/api/roles/<role_id>`                   | Yes  | Delete role                                 |
| GET    | `/api/roles/<role_id>/permissions`       | Yes  | Get role permissions                        |
| PUT    | `/api/roles/<role_id>/permissions`       | Yes  | Update role permissions                     |
| GET    | `/api/permissions`                       | Yes  | List permissions (backup implementation in routes_users.py) |
| POST   | `/api/permissions`                       | Yes  | Create a new permission                     |
| PUT    | `/api/permissions/<permission_id>`       | Yes  | Update permission                           |
| DELETE | `/api/permissions/<permission_id>`       | Yes  | Delete permission                           |
| PUT    | `/api/users/<user_id>/role`              | Yes  | Update user's role                          |
| POST   | `/api/roles/bulk/export`                 | Yes  | Bulk export roles                           |

## Editor ↔ Writer Management
| Method | Endpoint                                   | Auth | Description                                 |
|--------|--------------------------------------------|------|---------------------------------------------|
| GET    | `/settings/editor-writer`                  | Yes  | Management page to assign writers to editors |
| GET    | `/api/editor-writer/editors`               | Yes  | List available editors (Admin or custom role Editor) |
| GET    | `/api/editor-writer/writers`               | Yes  | List available writers (General or custom role Writer) |
| GET    | `/api/editor-writer/<editor_id>/list`      | Yes  | Get writers assigned to an editor           |
| POST   | `/api/editor-writer/<editor_id>/assign`    | Yes  | Replace assigned writers for an editor      |

## Permission Management System
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/user/role`                         | Yes  | Get current user's role and permissions     |
| GET    | `/api/user/permissions`                  | Yes  | Get current user's detailed permissions     |
| GET    | `/api/user/permissions/summary`          | Yes  | Get user permissions summary                |
| POST   | `/api/permissions/check`                 | Yes  | Check specific permission for user          |
| GET    | `/api/permissions/resources`             | Yes  | List available permission resources         |
| GET    | `/api/permissions/actions`               | Yes  | List available permission actions           |
| POST   | `/api/permissions/bulk-check`            | Yes  | Check multiple permissions for user         |
| GET    | `/api/roles/available`                   | Yes  | Get available roles for current user        |
| POST   | `/api/roles/assign`                      | Yes  | Assign role to user                         |
| POST   | `/api/roles/remove`                      | Yes  | Remove role from user                       |
| GET    | `/api/roles/statistics`                  | Yes  | Get role distribution statistics            |

## Social Media
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/social-media`                      | Yes  | List social media links                     |
| POST   | `/api/social-media`                      | Yes  | Add a new social media link                 |
| GET    | `/api/social-media/<social_id>`          | Yes  | Get social media link details               |
| PUT    | `/api/social-media/<social_id>`          | Yes  | Update social media link                    |
| DELETE | `/api/social-media/<social_id>`          | Yes  | Delete social media link                    |

## Subscriptions
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/subscriptions/plans`               | Yes  | Get subscription plans                      |
| POST   | `/api/subscriptions/create`              | Yes  | Create subscription                         |
| POST   | `/api/subscriptions/cancel`              | Yes  | Cancel subscription                         |
| GET    | `/api/subscriptions/status`              | Yes  | Get subscription status                     |
| POST   | `/api/subscriptions/update-ad-preferences` | Yes | Update ad preferences                   |
| GET    | `/api/subscriptions/check-premium-access` | Yes | Check premium access                    |
| GET    | `/api/admin/subscriptions`               | Yes  | List all subscriptions (admin)              |
| PUT    | `/api/admin/subscriptions/<subscription_id>` | Yes | Update subscription (admin)            |

## SEO Leveling System
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/` (any page)                           | No   | SEO leveling system automatically applies content-specific SEO over root SEO |
| GET    | `/news/<id>/<title>`                     | No   | Uses News model SEO fields (meta_title, meta_description, og_title, etc.) |
| GET    | `/album/<id>/<title>`                    | No   | Uses Album model SEO fields (meta_title, meta_description, og_title, etc.) |
| GET    | `/api/seo/leveling/status`               | Yes  | Get SEO leveling system status and configuration |
| POST   | `/api/seo/leveling/refresh`              | Yes  | Refresh SEO leveling cache and data |
| GET    | `/api/seo/leveling/content/<content_type>/<content_id>` | Yes | Get content-specific SEO data |
| PUT    | `/api/seo/leveling/content/<content_type>/<content_id>` | Yes | Update content-specific SEO data |

## SEO & Branding
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/seo/articles`                      | Yes  | List articles with SEO data                 |
| GET    | `/api/seo/articles/<article_id>`         | Yes  | Get SEO data for an article                 |
| PUT    | `/api/seo/articles/<article_id>`         | Yes  | Update SEO data for an article              |
| GET    | `/api/seo/albums`                        | Yes  | List albums with SEO data                   |
| GET    | `/api/seo/albums/<album_id>`             | Yes  | Get SEO data for an album                   |
| PUT    | `/api/seo/albums/<album_id>`             | Yes  | Update SEO data for an album                |
| GET    | `/api/seo/albums-management`             | Yes  | List albums with SEO data (albums management page) |
| GET    | `/api/seo/root`                          | Yes  | List root pages with SEO data               |
| POST   | `/api/seo/root`                          | Yes  | Create new root page SEO entry              |
| GET    | `/api/seo/root/<root_id>`                | Yes  | Get SEO data for a root page                |
| PUT    | `/api/seo/root/<root_id>`                | Yes  | Update SEO data for a root page             |
| POST   | `/api/seo/bulk-update`                   | Yes  | Bulk update SEO data                        |
| GET    | `/api/seo/metrics`                       | Yes  | Get SEO metrics                             |
| GET    | `/api/seo/global-settings`               | Yes  | Get global SEO settings                     |
| POST   | `/api/seo/global-settings`               | Yes  | Update global SEO settings                  |
| POST   | `/api/seo/global-og`                     | Yes  | Update global Open Graph settings           |
| POST   | `/api/seo/global-twitter`                | Yes  | Update global Twitter settings              |
| POST   | `/api/seo/global-structured`             | Yes  | Update global structured data settings      |
| POST   | `/api/seo/apply-global-settings`         | Yes  | Apply global SEO settings                   |
| GET    | `/api/seo/categories`                    | Yes  | List SEO categories                         |
| GET    | `/api/brand-identity`                    | Yes  | Get brand identity assets                   |
| GET    | `/api/brand-info`                        | No   | Get public brand info (no auth required)   |
| POST   | `/api/brand-identity`                    | Yes  | Update brand identity assets                |
| POST   | `/api/brand-identity/text`               | Yes  | Update brand text fields and feature toggles (brand_name, tagline, brand_description, homepage_design, categories_display_location, card_design, enable_comments, enable_ratings, enable_ads, enable_campaigns) - **UPDATED: Added brand_description field for detailed brand description** |
| POST   | `/api/brand-colors`                      | Yes  | Update brand colors                         |
| GET    | `/api/brand-colors`                      | Yes  | Get brand colors                            |

## SEO Analytics & Management
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/seo/stats/overview`                | Yes  | Get comprehensive SEO overview statistics   |
| GET    | `/api/seo/stats/score-distribution`      | Yes  | Get SEO score distribution across content types |
| GET    | `/api/seo/stats/content-performance`     | Yes  | Get content performance metrics by type     |
| GET    | `/api/seo/stats/status-breakdown`        | Yes  | Get SEO status breakdown (complete/incomplete/missing) |
| GET    | `/api/seo/activity/recent`               | Yes  | Get recent SEO activity and audit history   |
| GET    | `/api/seo/recommendations`               | Yes  | Get SEO improvement recommendations         |
| POST   | `/api/seo/chapters/<chapter_id>/inject`  | Yes  | Inject SEO data for individual chapter      |
| POST   | `/api/seo/articles/<article_id>/inject`  | Yes  | Inject SEO data for individual article      |
| POST   | `/api/seo/albums/<album_id>/inject`      | Yes  | Inject SEO data for individual album        |
| GET    | `/api/root-seo-settings`                 | Yes  | Get root SEO settings from brand identity   |
| POST   | `/api/root-seo-settings`                 | Yes  | Update root SEO settings in brand identity  |

## Comprehensive SEO Management
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/seo/articles`                      | Yes  | List articles with SEO data (comprehensive management) |
| GET    | `/api/seo/albums`                        | Yes  | List albums with SEO data (comprehensive management) |
| GET    | `/api/seo/chapters`                      | Yes  | List chapters with SEO data (comprehensive management) |
| GET    | `/api/seo/root`                          | Yes  | List root pages with SEO data (comprehensive management) |
| GET    | `/api/seo/articles/<article_id>`         | Yes  | Get detailed SEO data for an article        |
| PUT    | `/api/seo/articles/<article_id>`         | Yes  | Update SEO data for an article              |
| GET    | `/api/seo/albums/<album_id>`             | Yes  | Get detailed SEO data for an album          |
| PUT    | `/api/seo/albums/<album_id>`             | Yes  | Update SEO data for an album                |
| GET    | `/api/seo/chapters/<chapter_id>`         | Yes  | Get detailed SEO data for a chapter         |
| PUT    | `/api/seo/chapters/<chapter_id>`         | Yes  | Update SEO data for a chapter               |
| GET    | `/api/seo/root/<root_id>`                | Yes  | Get detailed SEO data for a root page       |
| PUT    | `/api/seo/root/<root_id>`                | Yes  | Update SEO data for a root page             |
| POST   | `/api/seo/root`                          | Yes  | Get detailed SEO data for a root page       |
| POST   | `/api/seo/inject`                        | Yes  | Run SEO injection for specified content type (news, albums, chapters, root, all) |
| GET    | `/api/seo/inject/status`                 | Yes  | Get SEO injection operation status and statistics |
| GET    | `/api/seo/stats`                         | Yes  | Get comprehensive SEO statistics for all content types |
| GET    | `/api/seo/global-settings`               | Yes  | Get global SEO settings and configuration   |
| PUT    | `/api/seo/global-settings`               | Yes  | Update global SEO settings and configuration |
| GET    | `/api/seo/analytics/overview`            | Yes  | Get SEO analytics overview and metrics      |
| GET    | `/api/seo/analytics/score-distribution`  | Yes  | Get SEO score distribution across content types |
| GET    | `/api/seo/analytics/content-performance` | Yes  | Get content performance metrics by type     |
| GET    | `/api/seo/analytics/status-breakdown`    | Yes  | Get SEO status breakdown (complete/incomplete/missing) |
| GET    | `/api/seo/analytics/recent-activity`     | Yes  | Get recent SEO activity and audit history   |
| GET    | `/api/seo/analytics/recommendations`     | Yes  | Get SEO improvement recommendations         |

## Root SEO Management
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/root-seo`                          | Yes  | List root SEO settings                      |
| POST   | `/api/root-seo`                          | Yes  | Create root SEO setting                     |
| GET    | `/api/root-seo/<page_identifier>`        | Yes  | Get root SEO for specific page              |
| PUT    | `/api/root-seo/<page_identifier>`        | Yes  | Update root SEO for specific page           |
| DELETE | `/api/root-seo/<page_identifier>`        | Yes  | Delete root SEO setting                     |
| POST   | `/api/root-seo/bulk-update`              | Yes  | Bulk update root SEO settings               |

## SEO Injection System
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| POST   | `/api/seo/inject`                        | Yes  | Run SEO injection for specified content type (news, albums, chapters, root, all) |
| GET    | `/api/seo/inject/status`                 | Yes  | Get SEO injection operation status and statistics |
| GET    | `/api/seo/stats`                         | Yes  | Get comprehensive SEO statistics for all content types |
| POST   | `/api/seo/inject/news`                   | Yes  | Run SEO injection for news articles only    |
| POST   | `/api/seo/inject/albums`                 | Yes  | Run SEO injection for albums only           |
| POST   | `/api/seo/inject/chapters`               | Yes  | Run SEO injection for chapters only         |
| POST   | `/api/seo/inject/root`                   | Yes  | Run SEO injection for root pages only       |
| GET    | `/api/seo-injection-settings`            | Yes  | Get SEO injection settings and default values |
| PUT    | `/api/seo-injection-settings`            | Yes  | Update SEO injection settings and default values |
| POST   | `/api/seo-injection-settings`            | Yes  | Create new SEO injection settings            |

## Team Members
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/team-members`                      | Yes  | List team members                           |
| POST   | `/api/team-members`                      | Yes  | Add a new team member                       |
| PUT    | `/api/team-members/<id>`                 | Yes  | Update team member                          |
| DELETE | `/api/team-members/<id>`                 | Yes  | Delete team member                          |

## Info, Policy, Contact
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/visi-misi`                         | No   | Get visi-misi sections                      |
| GET    | `/api/penyangkalan`                      | No   | Get penyangkalan sections                   |
| POST   | `/api/penyangkalan`                      | Yes  | Create penyangkalan section                 |
| PUT    | `/api/penyangkalan/<pid>`                | Yes  | Update penyangkalan section                 |
| GET    | `/api/contact-details`                   | No   | Get contact details                         |

## Performance Dashboard
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/database/status`                   | Yes  | Get comprehensive database statistics (users, news, albums, chapters, categories, comments, ratings) |
| POST   | `/api/database/optimize`                 | Yes  | Optimize all database tables with detailed results |
| POST   | `/api/database/cleanup`                  | Yes  | Clean up orphaned data, old activities, and optimize storage |
| POST   | `/api/database/backup`                   | Yes  | Create timestamped database backup with file info |
| GET    | `/api/database/backups`                  | Yes  | List all available database backups with metadata |
| GET    | `/api/cache/status`                      | Yes  | Get cache performance metrics and status |
| POST   | `/api/cache/clear`                       | Yes  | Clear all cache data with confirmation |
| POST   | `/api/cache/invalidate/<pattern>`        | Yes  | Invalidate specific cache patterns (news, albums, chapters, users) |
| GET    | `/api/performance/summary`               | Yes  | Get comprehensive performance metrics and statistics |
| GET    | `/api/system/status`                     | Yes  | Get system health and resource usage |

## Performance & Optimization
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| POST   | `/api/performance/clear-cache`           | Yes  | Clear performance cache                     |
| GET    | `/api/performance/alerts`                | Yes  | Get performance alerts                      |
| GET    | `/api/performance/recommendations`       | Yes  | Get performance recommendations             |
| GET    | `/api/performance/summary`               | Yes  | Get performance summary                     |
| POST   | `/api/asset-optimization/compress`       | Yes  | Compress static assets                      |
| POST   | `/api/asset-optimization/clear-cache`    | Yes  | Clear asset cache                           |
| POST   | `/api/asset-optimization/regenerate-hashes`| Yes  | Regenerate asset hashes                    |
| POST   | `/api/asset-optimization/minify`         | Yes  | Minify CSS/JS assets                        |
| POST   | `/api/ssr-optimization/clear-cache`      | Yes  | Clear SSR template cache                    |
| POST   | `/api/ssr-optimization/optimize-cache`   | Yes  | Optimize SSR cache                          |
| POST   | `/api/ssr-optimization/cache-template`   | Yes  | Cache specific template                     |

## Cache Management
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/cache/status`                      | Yes  | Get cache status                            |
| POST   | `/api/cache/clear`                       | Yes  | Clear all caches                            |
| POST   | `/api/cache/invalidate/<pattern>`        | Yes  | Invalidate cache by pattern                 |
| GET    | `/api/cache/keys`                        | Yes  | List cache keys                             |

## Database Management
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/database/status`                   | Yes  | Get database status and comprehensive statistics |
| POST   | `/api/database/optimize`                 | Yes  | Optimize database tables (all content types) |
| POST   | `/api/database/cleanup`                  | Yes  | Clean up database (orphaned data, old activities) |
| POST   | `/api/database/backup`                   | Yes  | Create database backup                      |
| GET    | `/api/database/backups`                  | Yes  | List database backups                       |

## System Status
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/system/status`                     | Yes  | Get system status                           |
| GET    | `/health`                                | No   | Health check endpoint                       |

## Ads System

### **Enhanced Advertisement Management**
The ads system now supports both **Internal** (web-only) and **External** (API-only) ad types with comprehensive image management and secure API access.

#### **Ad Types & Access Control**
- **Internal Ads**: Only served to same origin (web interface)
- **External Ads**: Only served via API with authentication (mobile apps, third-party integrations)
- **Image Management**: Support for both file uploads and external URLs
- **API Authentication**: API key required for external ad access

#### **Admin Management Endpoints**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/ads/dashboard`                         | Yes  | Ads management dashboard                     |
| GET    | `/ads/campaigns`                         | Yes  | List ad campaigns                           |
| GET    | `/ads/campaigns/create`                  | Yes  | Create new campaign page                    |
| POST   | `/ads/campaigns/create`                  | Yes  | Create new campaign                         |
| GET    | `/ads/campaigns/<campaign_id>`           | Yes  | Campaign detail page                        |
| GET    | `/ads/campaigns/<campaign_id>/edit`      | Yes  | Edit campaign page                          |
| POST   | `/ads/campaigns/<campaign_id>/edit`      | Yes  | Update campaign                             |
| POST   | `/ads/campaigns/<campaign_id>/delete`    | Yes  | Delete campaign                             |
| GET    | `/ads/ads`                               | Yes  | List ads with image thumbnails              |
| GET    | `/ads/ads/create`                        | Yes  | Create new ad page with image upload        |
| POST   | `/ads/ads/create`                        | Yes  | Create new ad (supports file upload)        |
| GET    | `/ads/ads/<ad_id>`                       | Yes  | Ad detail page                              |
| GET    | `/ads/ads/<ad_id>/edit`                  | Yes  | Edit ad page with image management          |
| POST   | `/ads/ads/<ad_id>/edit`                  | Yes  | Update ad (supports file upload)            |
| POST   | `/ads/ads/<ad_id>/delete`                | Yes  | Delete ad and associated image files        |
| GET    | `/ads/placements`                        | Yes  | List ad placements                          |
| GET    | `/ads/placements/create`                 | Yes  | Create new placement page                   |
| POST   | `/ads/placements/create`                 | Yes  | Create new placement                        |
| GET    | `/ads/placements/<placement_id>/edit`    | Yes  | Edit placement page                         |
| POST   | `/ads/placements/<placement_id>/edit`    | Yes  | Update placement                            |
| POST   | `/ads/placements/<placement_id>/delete`  | Yes  | Delete placement                            |
| GET    | `/ads/analytics`                         | Yes  | Ads analytics dashboard                     |
| GET    | `/ads/api/analytics/stats`               | Yes  | Get ads analytics statistics                |

#### **Ad Serving API Endpoints**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| POST   | `/ads/api/serve`                         | No   | **Main ad serving endpoint** - Serves ads based on page context. Respects internal/external ad types and user premium status. Internal ads only served to same origin, external ads only served via API with authentication. |
| POST   | `/ads/api/external/serve`                | API Key | **External ads only** - Dedicated endpoint for mobile apps and third-party integrations. Requires API key authentication. Optimized for external app consumption. |
| POST   | `/ads/api/serve/batch`                   | No   | **Batch ad serving** - Serves ads for multiple placements in one request. Respects ad type access controls. |
| GET    | `/ads/click`                              | No   | **Secure click tracking** - Handles ad click tracking and secure redirection with UTM parameters and URL signing. |

#### **Analytics & Tracking Endpoints**
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| POST   | `/ads/api/track-impression`              | No   | **Track ad impressions** - Records when ads are viewed for analytics and performance tracking. |
| POST   | `/ads/api/track-click`                   | No   | **Track ad clicks** - Records when ads are clicked for analytics and performance tracking. |
| POST   | `/ads/api/layout/recommend`              | No   | **Layout recommendations** - Recommends in-stream positions based on client-probed counts. |

#### **API Request Examples**

**Web Interface (Internal Ads)**
```javascript
// Standard web request - gets internal ads only
fetch('/ads/api/serve', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        page_type: 'home',
        section: 'sidebar',
        position: 'top',
        max_ads: 1
    })
})
```

**External Apps (External Ads)**
```javascript
// External app request - gets external ads only
fetch('/ads/api/external/serve', {
    method: 'POST',
    headers: { 
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key'
    },
    body: JSON.stringify({
        page_type: 'home',
        section: 'banner',
        position: 'top',
        device_type: 'mobile',
        max_ads: 1
    })
})
```

**Batch Ad Serving**
```javascript
// Batch request for multiple placements
fetch('/ads/api/serve/batch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        placements: [
            {
                page_type: 'home',
                section: 'sidebar',
                position: 'top',
                key: 'sidebar_top'
            },
            {
                page_type: 'home',
                section: 'content',
                position: 'after_n_items',
                position_value: 3,
                key: 'content_after_3'
            }
        ],
        device_type: 'desktop'
    })
})
```

> Note: Ads serving endpoints (`/ads/api/serve`, `/ads/api/serve/batch`, `/ads/api/layout/recommend`) are globally disabled when Brand Identity toggles `enable_ads` or `enable_campaigns` are set to false.

> Client injection allowlist: Ads are injected on public pages only when the page explicitly opts in by setting `window.__ADS_ALLOWED__ = true` in the template and the global flags (`enable_ads`, `enable_campaigns`) are true. The current allowlisted public pages are:
> - `/` homepage news design (`templates/public/index.html`)
> - `/` homepage albums design (`templates/public/index_albums.html`)
> - `/albums` (`templates/public/albums.html`)
> - `/news` (`templates/public/news.html`)
> - `/album/<id>/<title>` (`templates/public/album_detail.html`)
> - `/album/<id>/chapter/<id>/<title>` (`templates/public/chapter_reader.html`)
> - `/news/<id>/<title>` (`templates/public/reader.html`)

> Placement policy: Home pages use in‑stream placements only (between cards) to avoid disrupting hero/headers/footers. Album/News list/detail pages use conservative in‑stream placements aligned to card groups.

## Registration & Auth
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/register`                              | No   | Registration page                           |
| POST   | `/register`                              | No   | Register a new user                         |
| GET    | `/verify-email`                          | No   | Verify user email with token; upon success may auto-approve low-risk users per hybrid policy |
| GET    | `/login`                                 | No   | Login page                                  |
| POST   | `/login`                                 | No   | Login action                                |
| GET    | `/logout`                                | Yes  | Logout action                               |
| GET    | `/api/registrations/pending`             | Yes  | Get pending user registrations (fixed: proper role checks) |
| POST   | `/api/registrations/<user_id>/approve`   | Yes  | Approve user registration (fixed: proper role checks) |
| POST   | `/api/registrations/<user_id>/reject`    | Yes  | Reject user registration (fixed: proper role checks) |
| POST   | `/api/registrations/bulk/approve`        | Yes  | Bulk approve registrations (fixed: proper role checks) |
| POST   | `/api/registrations/bulk/reject`         | Yes  | Bulk reject registrations (fixed: proper role checks) |

### External Auth API (for mobile/3rd-party apps)
| Method | Endpoint               | Auth | Description |
|--------|------------------------|------|-------------|
| POST   | `/api/auth/register`   | No   | JSON registration; creates pending account (requires approval) |
| POST   | `/api/auth/login`      | No   | Login; returns `access_token`, `refresh_token`, `expires_in`, `user` |
| POST   | `/api/auth/refresh`    | No   | Exchange `refresh_token` for new access/refresh tokens |
| POST   | `/api/auth/logout`     | No   | Stateless logout; clients discard tokens |
| GET    | `/api/auth/me`         | Bearer | Get current user; requires `Authorization: Bearer <access_token>` |

#### External Profile & Account API (Bearer)
| Method | Endpoint                              | Auth   | Description |
|--------|---------------------------------------|--------|-------------|
| GET    | `/api/auth/profile`                   | Bearer | Get current user's profile + user fields |
| PUT    | `/api/auth/profile`                   | Bearer | Update user (first_name, last_name, email, birthdate, bio) and profile (pronouns, short_bio, location, website, social_links) |
| PATCH  | `/api/auth/profile/privacy`           | Bearer | Update privacy flags (`show_email`, `show_birthdate`) |
| PATCH  | `/api/auth/profile/username`          | Bearer | Change username (requires `current_password`) |
| POST   | `/api/auth/account/change-password`   | Bearer | Change password (current_password, new_password, confirm_password) |
| DELETE | `/api/auth/account`                   | Bearer | Delete account and owned content (best-effort) |

Hybrid verification/approval flow:
- Registration creates users as pending (`is_active=false`, `verified=false`).
- A signed verification link is sent/logged; `GET /verify-email?token=...` marks `verified=true`.
- If risk score is low (see `routes/utils/risk_policy.py`), the user is auto-approved (`is_active=true`); otherwise remains pending for admin review.

## Settings/Admin Pages
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/settings`                              | Yes  | Admin settings dashboard (admin-tier users) |
| GET    | `/dashboard`                             | Yes  | General user dashboard (reader dashboard)   |
| GET    | `/login`                                 | No   | Login page with smart routing (redirects to appropriate dashboard based on user role) |
| GET    | `/settings/account`                      | Yes  | Account settings page (admin/superuser)     |
| GET    | `/account/settings`                      | Yes  | User account settings page (general users)  |
| GET    | `/settings/users`                        | Yes  | User management page                        |
| GET    | `/settings/analytics`                    | Yes  | Analytics dashboard                         |
| GET    | `/settings/seo`                          | Yes  | SEO management page (redirects to management) |
| GET    | `/settings/seo/management`               | Yes  | Main SEO management page (Articles, Albums, Chapters, Root Pages) |
| GET    | `/settings/seo/settings`                 | Yes  | SEO settings page (Root SEO settings, global settings) |
| GET    | `/settings/seo/analytics`                | Yes  | SEO analytics dashboard (statistics, charts, recommendations) |
| GET    | `/settings/comprehensive_seo_management` | Yes  | Legacy SEO management page (redirects to management) |
| GET    | `/settings/root-seo`                     | Yes  | Root SEO management page                    |
| GET    | `/admin/seo-management`                  | Yes  | Comprehensive SEO management page (Settings, Articles, Analytics tabs) |
| GET    | `/settings/create_news`                  | Yes  | Create/Edit news page (optional `news_id`, optional `album_id` for chapter context) |
| GET    | `/settings/manage_news`                  | Yes  | Manage news page                            |
| GET    | `/settings/albums`                       | Yes  | Album management page                       |
| GET    | `/settings/editor-writer`                | Yes  | Editor ↔ Writer management page             |
| GET    | `/admin/tools/docx-upload`               | Yes  | DOCX upload tool page with quick link to news management |
| GET    | `/admin/tools/docx-template`             | Yes  | Download DOCX template file                 |
| GET    | `/admin/tools/docx-contoh`               | Yes  | Download example DOCX file                  |

## Admin Sidebar & Quick Toggles
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/api/admin/sidebar/navigation`          | Yes  | Get sidebar navigation structure with permissions |
| POST   | `/api/admin/sidebar/toggle`              | Yes  | Toggle sidebar visibility                   |
| GET    | `/api/admin/toggles/status`              | Yes  | Get quick toggles status (comments, ratings, ads, campaigns) |
| POST   | `/api/admin/toggles/update`              | Yes  | Update quick toggle settings               |
| GET    | `/api/admin/toggles/storage`             | Yes  | Get localStorage toggle preferences         |
| POST   | `/api/admin/toggles/reset`               | Yes  | Reset all toggle settings to defaults      |
| GET    | `/api/admin/permissions/check`           | Yes  | Check permission for sidebar item visibility |
| POST   | `/api/admin/navigation/search`           | Yes  | Search sidebar navigation items            |

> Legacy: `/settings/create_news_management` now 302-redirects to `/settings/create_news` (query params preserved).
| GET/POST| `/settings/privacy-policy`              | Yes  | Privacy policy management                   |
### Quick Toggles Behavior (Unified)
- Ads: persisted via `GET/POST /api/settings/ads` (JSON: `{ ads: { show_ads: bool } }` on GET; `{ show_ads: bool }` on POST). UI in sidebar and `settings_management.html` reflect and update the same value. LocalStorage mirrors the latest value as a UI fallback only.
- Campaigns: stored in shared `localStorage` key `toggle-campaigns`; sidebar and `settings_management.html` are synchronized across pages. Backend persistence can be added later.
- Comments/Ratings: UI-only toggles stored in `localStorage` (`toggle-comments`, `toggle-ratings`).
- Removed: global ads toggle block from `users_management.html` to avoid duplication.
| GET/POST| `/settings/media-guidelines`            | Yes  | Media guidelines management                 |
| GET/POST| `/settings/visi-misi`                   | Yes  | Visi-misi management                       |
| GET/POST| `/settings/pedomanhak`                  | Yes  | Pedoman hak management                      |
| GET/POST| `/settings/penyangkalan`                | Yes  | Penyangkalan management                     |
| GET/POST| `/settings/contact-details`             | Yes  | Contact details management                  |
| GET/POST| `/settings/team-members`                | Yes  | Team members management                     |
| GET    | `/settings/categories`                   | Yes  | Categories management page                  |
| GET    | `/settings/youtube`                      | Yes  | YouTube management page                     |
| GET    | `/settings/social-media`                 | Yes  | Social media management page                |
| GET    | `/settings/brand-identity`               | Yes  | Brand identity management page              |
| GET    | `/settings/performance`                  | Yes  | Performance monitoring dashboard            |
| GET    | `/settings/asset-optimization`           | Yes  | Asset optimization dashboard                |
| GET    | `/settings/ssr-optimization`             | Yes  | SSR optimization dashboard                  |
| GET    | `/admin/comments`                        | Yes  | Comment moderation interface                |
| GET    | `/admin/ratings`                         | Yes  | Rating management interface                 |
| GET    | `/admin/ratings/analytics`               | Yes  | Rating analytics dashboard                  |

## User Account Management API
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| POST   | `/api/account/change-password`           | Yes  | Change user password                        |
| DELETE | `/api/account/delete`                    | Yes  | Delete user account                         |
| POST   | `/api/user/request-account-deletion`     | Yes  | Request account deletion (general users only) |
| GET    | `/api/users/deletion-requests`           | Yes  | Get account deletion requests (admin only) |
| POST   | `/api/users/<id>/approve-deletion`       | Yes  | Approve account deletion request (admin only) |
| POST   | `/api/users/<id>/reject-deletion`        | Yes  | Reject account deletion request (admin only) |
| GET    | `/api/account/stats`                     | Yes  | Get comprehensive account statistics (articles, albums, chapters, comments) |
| GET    | `/api/account/albums`                    | Yes  | Get user's albums with pagination and filtering |
| GET    | `/api/account/comments`                  | Yes  | Get user's recent comments                  |
| GET    | `/api/account/activity`                  | Yes  | Get user's recent activity                  |
| GET    | `/api/account/profile`                   | Yes  | Get current user's profile data (username, email, full_name, first_name, last_name, birthdate, age, role, custom_role_name, created_at, last_login) |
| PUT    | `/api/account/profile`                   | Yes  | Update current user's profile data (full_name, birthdate) - full_name is split into first_name and last_name |

## Public/Pages
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/` or `/beranda`                        | No   | Homepage (supports news-focused and albums-focused designs) |
| GET    | `/news`                                  | No   | Unified news listing page (supports URL parameters: type, q, category, tag, sort, page, per_page) |
| GET    | `/news/<news_id>`                        | No   | News detail page                            |
| GET    | `/news/<news_id>/<slug>`                 | No   | News detail page (SEO slug)                 |
| GET    | `/albums`                                | No   | Albums listing page (supports URL parameters: sort, status, category, rating) |
| GET    | `/album/<album_id>/<album_title>`        | No   | Album detail page                           |
| GET    | `/album/<album_id>/chapter/<chapter_id>/<chapter_title>` | No | Chapter reader page |
| GET    | `/videos`                                | No   | Video listing page                          |
| GET    | `/gallery`                               | No   | Image gallery page                          |
| GET    | `/about`                                 | No   | About/team/contact page                     |
| GET    | `/utama`                                 | No   | **REDIRECTS TO** `/news?type=utama` (Featured/premium news) |
| GET    | `/hypes`                                 | No   | **REDIRECTS TO** `/news?type=news` (News/featured content) |
| GET    | `/articles`                              | No   | **REDIRECTS TO** `/news?type=articles` (Articles page) |
| GET    | `/search`                                | No   | **REDIRECTS TO** `/news` with search parameters |

## Sitemaps & Robots
| Method | Endpoint                                 | Auth | Description                                 |
|--------|------------------------------------------|------|---------------------------------------------|
| GET    | `/sitemap.xml`                           | No   | Main sitemap (SEO) - **UPDATED: Fixed datetime timezone issues and AlbumChapter.title field** |
| GET    | `/sitemap-news.xml`                      | No   | News-specific sitemap (SEO)                 |
| GET    | `/sitemap-albums.xml`                    | No   | Albums-specific sitemap (SEO)               |
| GET    | `/sitemap-index.xml`                     | No   | Sitemap index (SEO)                         |
| GET    | `/robots.txt`                            | No   | Robots.txt (SEO) - **UPDATED: Auto-updated with correct website URL from SEO settings** |

---

> **Note:** All endpoints are listed, including those for admin/settings, public pages, and all CRUD operations. For endpoints with multiple methods (e.g., GET/POST), both are shown. Bulk and utility endpoints are included for completeness. The new Albums section includes all album and chapter management endpoints.

### **Recent Backend Updates**

#### **Image API Security Enhancement & Story Creation**
- **Secure Ownership Filtering**: Implemented proper ownership-based access control for image API endpoints
- **Role-Based Image Access**: 
  - Admin/Superuser/Subadmin: Can see all images (no restrictions)
  - Editor: Own images + assigned writers' images + admin/suadmin visible images
  - Regular users: Own images + admin/suadmin visible images
- **`all_users=true` Parameter Security**: Fixed parameter to apply proper ownership filtering instead of bypassing restrictions
- **Cross-Contamination Prevention**: Users cannot see images from other regular users, ensuring data privacy
- **Backend Logic Update**: Modified `routes/routes_images.py` and `routes/routes_api_xlate.py` with secure filtering logic
- **Frontend Integration**: Enhanced `create_story.html` with secure image loading and proper API parameter usage
- **Story Creation Image Picker**: Users can now securely select from their own images plus admin-uploaded visible images
- **Error Handling**: Added comprehensive error handling and fallback mechanisms for image rendering and SimpleMDE integration

#### **Profile List Card Design Unification**
- **Unified Card Design**: Updated `profile_list.html` to use consistent card design matching other user profile pages (stories.html, library.html)
- **Layout Consistency**: Replaced custom album card grid with uniform list layout using `space-y-6` spacing
- **Flex Layout Structure**: Implemented consistent flex layout with image container (`sm:w-1/3 lg:w-2/5 xl:w-1/3`) and text container
- **Visual Improvements**: Same hover effects, transitions, badge styling, and icon usage as other profile pages
- **Responsive Design**: Mobile stacked layout, tablet side-by-side, desktop optimized proportions
- **CSS Cleanup**: Removed dependency on custom `albums.css` file for cleaner codebase
- **Better Information Hierarchy**: Title and badges in header, category link, description with line clamping, metadata footer with icons
- **Performance**: Lazy loading for images and proper ARIA labels for accessibility

#### **Sitemap Generation & Robots.txt Auto-Update**
- **Fixed Sitemap Generation Errors**: Resolved datetime timezone issues and `AttributeError: type object 'AlbumChapter' has no attribute 'title'` by updating field reference to `chapter_title`
- **Robots.txt Auto-Update Feature**: Created `update_robots_txt()` function that automatically updates robots.txt with correct website URL from SEO injection settings
- **Automatic Integration**: Sitemap generation now automatically updates robots.txt with correct website URL when accessed
- **Error Handling**: Added comprehensive error handling for sitemap generation with proper timezone-aware date calculations
- **Helper Functions**: Created `calculate_days_old()` helper function for proper timezone handling in sitemap generation

#### **Database Health & Performance Improvements**
- **Database Health Checks**: All 9 health checks now passing with 77.8% success rate (7/9 passed)
- **Missing Indexes Identified**: Album `created_at` and Image `is_visible` indexes identified for performance optimization
- **Safe Migration System**: Custom `safe_migrate.py` system replaces external migration dependencies for minimal external dependencies
- **Database Optimization**: 50+ strategic database indexes added for optimal query performance
- **Health Monitoring**: Comprehensive database health monitoring and orphaned data cleanup
- **Performance Metrics**: Real-time database performance tracking and optimization

#### **UI Terminology Updates**
- **Story & Chapter Management**: Updated UI terminology from "artikel" to "cerita dan bab" for better context
- **Admin Interface**: Create and manage news pages now use "Cerita" and "Bab" terminology
- **Public Interface**: News listing page updated with new terminology for consistency
- **Form Labels**: All form labels, placeholders, and descriptions updated to reflect story/chapter context
- **Accessibility**: ARIA labels and descriptions updated for better screen reader support

#### **Smart Routing System Implementation**
- **Role-Based Navigation**: Automatic dashboard routing based on user role (admin/superuser/owner → `/settings`, general users → `/dashboard`)
- **Template Context Integration**: Added `get_user_dashboard_url()` function to Flask template context processors
- **Consistent User Experience**: All dashboard links now use smart routing for seamless navigation
- **Template Updates**: Updated `base.html` and `user_account_settings.html` to use smart routing
- **Login Integration**: Login redirects now use the same smart routing logic for consistency
- **Mobile Navigation**: Mobile menu also uses smart routing for dashboard links
- **Backward Compatibility**: Existing functionality preserved while adding smart routing

#### **Album Chapter Management System Enhancements**
- **Owned Articles Display**: Updated to show all owned articles (published and draft) regardless of visibility status
- **Chapter Visibility Management**: Added independent chapter visibility control separate from article visibility
- **Enhanced Action Buttons**: Larger, properly spaced buttons with hover effects and new tab opening for source articles
- **Comprehensive Pagination**: 12 articles per page with search integration and per-page selector (6, 12, 24, 48)
- **Role-Based Article Filtering**: Admins see all articles, editors see assigned writers' articles, others see only their own
- **Chapter Visibility Toggle**: New endpoint `/admin/albums/<album_id>/chapters/<chapter_id>/toggle-visibility` for show/hide functionality
- **Search Persistence**: Search terms maintained across pagination with proper URL parameter handling
- **Enhanced Article Display**: Shows visibility status, category, author, and creation date for each article
- **Chapter Reader Compatibility**: Chapters can be displayed regardless of source article visibility status
- **Chapter Count Updates**: Fixed album total_chapters count not updating when adding/removing chapters
- **Database Consistency**: Added proper album.update_chapter_count() calls after chapter operations
- **Relationship Loading**: Fixed SQLAlchemy relationship loading using album.chapters instead of separate queries
- **Session Management**: Added db.session.refresh(album) to ensure latest data before count updates
- **Blueprint URL Structure**: Updated albums blueprint to use `/admin/albums` prefix for proper admin routing
- **Template URL Updates**: Fixed all JavaScript fetch calls to use correct admin URLs
- **Chapter Reordering**: Added move chapter functionality with proper chapter number swapping
- **Error Handling**: Enhanced error handling and logging for chapter management operations

#### **Comment API System Fixes**
- **Enhanced Error Handling**: Improved error logging with detailed exception information for better debugging
- **Robust User Serialization**: Fixed comment and rating serialization to handle user data without requiring User.to_dict() method
- **Timezone Handling**: Fixed UserSubscription.is_active property with proper timezone-aware comparisons
- **API Stability**: Resolved 500 errors on `/api/comments/news/{id}` and `/api/comments/album/{id}` endpoints
- **Fallback Mechanisms**: Graceful handling of missing user data with lightweight user payloads

#### **User Role System Enhancement**
- **Role-Based Access Control**: Implemented admin-tier vs general user separation with distinct dashboards
- **Login Redirects**: Dynamic redirection based on user role (admins to /settings, general users to /dashboard)
- **Custom Roles**: Enhanced role system with Writer, Editor, and Subadmin custom roles
- **Premium Access**: Improved premium subscription status checking and ad preference management
- **Reader Features**: Added reading history and user library functionality for general users

#### **Permission Management System Implementation**
- **Centralized Permission System**: Created `routes/utils/permission_manager.py` with `PermissionManager` class
- **Role Management System**: Created `routes/utils/role_manager.py` with `RoleManager` class
- **Template Integration**: Added Flask context processor `inject_permission_functions` in `main.py`
- **Permission Helper Functions**: 20+ helper functions for permission checking (can_access_admin, can_manage_users, etc.)
- **Resource-Based Permissions**: 16 resources (news, albums, users, categories, etc.) with 12 actions each
- **Role Hierarchy**: Superuser (100), Admin (80), General (10) with proper inheritance
- **Custom Role Support**: Full support for custom roles with permission inheritance
- **Template Safety**: All permission functions available in Jinja2 templates via context processor
- **Package Organization**: Proper `routes/utils/__init__.py` exports for clean imports
- **Comprehensive Documentation**: Complete README with usage examples and security considerations
- **Backup API Endpoints**: Added backup implementations of `/api/roles` and `/api/permissions` in `routes_users.py` to resolve persistent 404 errors
- **API Stability**: Ensured frontend can successfully fetch role and permission data for user management interface

#### **Performance Dashboard System**
- **Comprehensive Database Statistics**: Enhanced `/api/database/status` with detailed statistics for all content types (users, news, albums, chapters, categories, comments, ratings)
- **Database Optimization**: `/api/database/optimize` now targets all 25+ database tables including albums, chapters, categories, comments, and ratings
- **Enhanced Cleanup Operations**: `/api/database/cleanup`