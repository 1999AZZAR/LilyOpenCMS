from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import desc, or_, and_
from models import db, News, Album, AlbumChapter, Image, Category, User, UserRole, CustomRole
from flask_login import current_user

api_xlate = Blueprint('api_xlate', __name__, url_prefix='/api/xlate')


def _safe_datetime(dt):
    return dt.isoformat() if dt else None


def _excerpt(text, limit=160):
    if not text:
        return None
    # naive strip html tags
    import re
    s = re.sub('<[^<]+?>', '', text)
    return (s[:limit] + '…') if len(s) > limit else s


def _image_info(img):
    if not img:
        return None
    url = getattr(img, 'file_url', None) or getattr(img, 'url', None)
    return {
        'id': getattr(img, 'id', None),
        'url': url,
        'alt_text': getattr(img, 'alt_text', None),
        'caption': getattr(img, 'caption', None),
        'title': getattr(img, 'title', None),
        'description': getattr(img, 'description', None),
        'is_visible': getattr(img, 'is_visible', None),
        'created_at': _safe_datetime(getattr(img, 'created_at', None)),
        'updated_at': _safe_datetime(getattr(img, 'updated_at', None)),
        'owner': _user_info(getattr(img, 'user', None)),
    }



def _user_info(u):
    if not u:
        return None
    return {
        'id': getattr(u, 'id', None),
        'username': getattr(u, 'username', None),
        'display_name': getattr(u, 'full_name', None) or getattr(u, 'username', None),
        'avatar_url': getattr(u, 'avatar_url', None),
        'is_premium_user': getattr(u, 'is_premium', None),
        'created_at': _safe_datetime(getattr(u, 'created_at', None)),
        'last_login': _safe_datetime(getattr(u, 'last_login', None)),
    }


def _category_info(c):
    if not c:
        return None
    return {
        'id': getattr(c, 'id', None),
        'name': getattr(c, 'name', None),
        'description': getattr(c, 'description', None),
        'slug': getattr(c, 'slug', None),
    }


def _tag_names(tag_list):
    names = []
    try:
        for t in (tag_list or []):
            name = getattr(t, 'name', None)
            if name:
                names.append(name)
    except Exception:
        pass
    return names


def _album_brief(a):
    if not a:
        return None
    return {
        'id': getattr(a, 'id', None),
        'title': getattr(a, 'title', None),
        'description': getattr(a, 'description', None),
        'is_premium': getattr(a, 'is_premium', None),
        'is_completed': getattr(a, 'is_completed', None),
        'is_hiatus': getattr(a, 'is_hiatus', None),
        'created_at': _safe_datetime(getattr(a, 'created_at', None)),
        'updated_at': _safe_datetime(getattr(a, 'updated_at', None)),
        'read_count': getattr(a, 'total_views', None),
        'chapter_count': getattr(a, 'total_chapters', None),
        'category': _category_info(getattr(a, 'category', None)),
        'header_image': _image_info(getattr(a, 'image', None)),
        'author': _user_info(getattr(a, 'user', None)),
        'tags': _tag_names(getattr(a, 'tags', None)),
    }


def _chapter_brief(ch):
    if not ch:
        return None
    return {
        'id': getattr(ch, 'id', None),
        'chapter_number': getattr(ch, 'chapter_number', None),
        'chapter_title': getattr(ch, 'chapter_title', None),
        'is_premium': getattr(ch, 'is_premium', None),
        'created_at': _safe_datetime(getattr(ch, 'created_at', None)),
        'updated_at': _safe_datetime(getattr(ch, 'updated_at', None)),
        'view_count': getattr(ch, 'view_count', None),
    }


@api_xlate.get('/news')
def xlate_news_list():
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = max(1, min(100, int(request.args.get('per_page', 20))))
        sort = request.args.get('sort', 'latest')
        q = request.args.get('search') or request.args.get('q')
        category_id = request.args.get('category', type=int)

        query = News.query
        if q:
            like = f"%{q}%"
            query = query.filter((News.title.ilike(like)) | (News.content.ilike(like)))
        if category_id:
            query = query.filter(News.category_id == category_id)

        if sort == 'popular':
            if hasattr(News, 'read_count'):
                query = query.order_by(desc(News.read_count))
            else:
                query = query.order_by(desc(News.created_at))
        else:
            query = query.order_by(desc(News.created_at))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = []
        for n in pagination.items:
            items.append({
                'id': getattr(n, 'id', None),
                'title': getattr(n, 'title', None),
                'excerpt': getattr(n, 'excerpt', None) or _excerpt(getattr(n, 'content', None)),
                'is_premium': bool(getattr(n, 'is_premium', False)),
                'is_news': bool(getattr(n, 'is_news', True)),
                'created_at': _safe_datetime(getattr(n, 'created_at', None)),
                'updated_at': _safe_datetime(getattr(n, 'updated_at', None)),
                'view_count': getattr(n, 'read_count', None),
                'share_count': getattr(n, 'share_count', None),
                'category': _category_info(getattr(n, 'category', None)),
                'header_image': _image_info(getattr(n, 'image', None)),
                'author': _user_info(getattr(n, 'user', None)),
                'tags': _tag_names(getattr(n, 'tags', None)),
            })
        return jsonify({
            'news': items,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            },
            'filters': {
                'current_category': category_id,
                'current_search': q,
                'current_sort': sort,
            }
        })
    except Exception as e:
        current_app.logger.error(f"xlate_news_list error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_xlate.get('/news/<int:news_id>')
def xlate_news_detail(news_id: int):
    try:
        n = News.query.get_or_404(news_id)
        data = {
            'id': getattr(n, 'id', None),
            'title': getattr(n, 'title', None),
            'content': getattr(n, 'content', None),
            'excerpt': getattr(n, 'excerpt', None) or _excerpt(getattr(n, 'content', None)),
            'is_premium': bool(getattr(n, 'is_premium', False)),
            'is_news': bool(getattr(n, 'is_news', True)),
            'created_at': _safe_datetime(getattr(n, 'created_at', None)),
            'updated_at': _safe_datetime(getattr(n, 'updated_at', None)),
            'view_count': getattr(n, 'read_count', None),
            'share_count': getattr(n, 'share_count', None),
            'category': _category_info(getattr(n, 'category', None)),
            'header_image': _image_info(getattr(n, 'image', None)),
            'author': _user_info(getattr(n, 'user', None)),
            'tags': _tag_names(getattr(n, 'tags', None)),
            'album': _album_brief(getattr(n, 'album', None)) if hasattr(n, 'album') else None,
        }
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"xlate_news_detail error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_xlate.get('/albums')
def xlate_albums_list():
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = max(1, min(100, int(request.args.get('per_page', 20))))
        sort = request.args.get('sort', 'latest')
        q = request.args.get('search') or request.args.get('q')
        category_id = request.args.get('category', type=int)

        query = Album.query
        if q:
            like = f"%{q}%"
            query = query.filter((Album.title.ilike(like)) | (Album.description.ilike(like)))
        if category_id:
            query = query.filter(Album.category_id == category_id)

        if sort == 'popular':
            if hasattr(Album, 'total_views'):
                query = query.order_by(desc(Album.total_views))
            else:
                query = query.order_by(desc(Album.created_at))
        elif sort == 'chapters':
            if hasattr(Album, 'total_chapters'):
                query = query.order_by(desc(Album.total_chapters))
            else:
                query = query.order_by(desc(Album.created_at))
        else:
            query = query.order_by(desc(Album.created_at))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        items = []
        for a in pagination.items:
            items.append({
                'id': getattr(a, 'id', None),
                'title': getattr(a, 'title', None),
                'description': getattr(a, 'description', None),
                'is_premium': bool(getattr(a, 'is_premium', False)),
                'is_completed': bool(getattr(a, 'is_completed', False)),
                'is_hiatus': bool(getattr(a, 'is_hiatus', False)),
                'created_at': _safe_datetime(getattr(a, 'created_at', None)),
                'updated_at': _safe_datetime(getattr(a, 'updated_at', None)),
                'read_count': getattr(a, 'total_views', None),
                'chapter_count': getattr(a, 'total_chapters', None) or (len(getattr(a, 'chapters', []) or []) if hasattr(a, 'chapters') else None),
                'category': _category_info(getattr(a, 'category', None)),
                'header_image': _image_info(getattr(a, 'image', None)),
                'author': _user_info(getattr(a, 'user', None)),
                'tags': _tag_names(getattr(a, 'tags', None)),
            })
        return jsonify({
            'albums': items,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            },
            'filters': {
                'current_category': category_id,
                'current_search': q,
                'current_sort': sort,
            }
        })
    except Exception as e:
        current_app.logger.error(f"xlate_albums_list error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_xlate.get('/albums/<int:album_id>')
def xlate_album_detail(album_id: int):
    try:
        a = Album.query.get_or_404(album_id)
        chapters = getattr(a, 'chapters', []) or []
        data = {
            'id': getattr(a, 'id', None),
            'title': getattr(a, 'title', None),
            'description': getattr(a, 'description', None),
            'is_premium': bool(getattr(a, 'is_premium', False)),
            'is_completed': bool(getattr(a, 'is_completed', False)),
            'is_hiatus': bool(getattr(a, 'is_hiatus', False)),
            'created_at': _safe_datetime(getattr(a, 'created_at', None)),
            'updated_at': _safe_datetime(getattr(a, 'updated_at', None)),
            'read_count': getattr(a, 'total_views', None),
            'category': _category_info(getattr(a, 'category', None)),
            'header_image': _image_info(getattr(a, 'image', None)),
            'author': _user_info(getattr(a, 'user', None)),
            'tags': _tag_names(getattr(a, 'tags', None)),
            'chapters': [_chapter_brief(ch) for ch in chapters],
        }
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"xlate_album_detail error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_xlate.get('/albums/<int:album_id>/chapters/<int:chapter_id>')
def xlate_album_chapter(album_id: int, chapter_id: int):
    try:
        ch = AlbumChapter.query.get_or_404(chapter_id)
        if getattr(ch, 'album_id', None) != album_id:
            return jsonify({'error': 'Chapter not in album'}), 404

        # Ensure we attach the correct album brief even if relationship is lazy/None
        album_obj = getattr(ch, 'album', None)
        if album_obj is None and getattr(ch, 'album_id', None):
            try:
                album_obj = Album.query.get(getattr(ch, 'album_id'))
            except Exception:
                album_obj = None

        # Build content with fallbacks
        news_obj = getattr(ch, 'news', None)
        content_val = None
        for attr in ['content', 'summary', 'excerpt']:
            if news_obj is not None:
                val = getattr(news_obj, attr, None)
                if val:
                    content_val = val
                    break
        # Fallback to chapter.content if exists
        if not content_val:
            content_val = getattr(ch, 'content', None)

        data = {
            'id': getattr(ch, 'id', None),
            'chapter_number': getattr(ch, 'chapter_number', None),
            'chapter_title': getattr(ch, 'chapter_title', None),
            'content': content_val,
            'is_premium': bool(getattr(ch, 'is_premium', False)),
            'created_at': _safe_datetime(getattr(ch, 'created_at', None)),
            'updated_at': _safe_datetime(getattr(ch, 'updated_at', None)),
            'album': _album_brief(album_obj),
            'news_content': ({
                'id': getattr(news_obj, 'id', None),
                'title': getattr(news_obj, 'title', None),
                'content': getattr(news_obj, 'content', None),
                'excerpt': _excerpt(getattr(news_obj, 'content', None) or getattr(news_obj, 'summary', None)),
                'is_premium': bool(getattr(news_obj, 'is_premium', False)),
                'created_at': _safe_datetime(getattr(news_obj, 'created_at', None)),
                'updated_at': _safe_datetime(getattr(news_obj, 'updated_at', None)),
                'author': _user_info(getattr(news_obj, 'user', None)),
                'category': _category_info(getattr(news_obj, 'category', None)),
                'header_image': _image_info(getattr(news_obj, 'image', None)),
                'tags': _tag_names(getattr(news_obj, 'tags', None)),
            } if news_obj else None),
            'navigation': {
                'previous': None,
                'next': None,
            },
        }
        # naive prev/next by chapter_number within album
        try:
            album_chaps = (AlbumChapter.query
                           .filter(AlbumChapter.album_id == album_id)
                           .order_by(AlbumChapter.chapter_number.asc())
                           .all())
            ids = [getattr(c, 'id', None) for c in album_chaps]
            idx = ids.index(chapter_id)
            if idx > 0:
                prev = album_chaps[idx - 1]
                data['navigation']['previous'] = {
                    'id': getattr(prev, 'id', None),
                    'chapter_title': getattr(prev, 'chapter_title', None),
                    'chapter_number': getattr(prev, 'chapter_number', None),
                }
            if idx < len(album_chaps) - 1:
                nx = album_chaps[idx + 1]
                data['navigation']['next'] = {
                    'id': getattr(nx, 'id', None),
                    'chapter_title': getattr(nx, 'chapter_title', None),
                    'chapter_number': getattr(nx, 'chapter_number', None),
                }
        except Exception:
            pass
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"xlate_album_chapter error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_xlate.get('/images')
def xlate_images_list():
    # Requires auth in your stack; here we just expose the same shape
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = max(1, min(100, int(request.args.get('per_page', 20))))
        visibility = request.args.get('visibility')  # visible/hidden
        all_users = request.args.get('all_users', 'false').lower() == 'true'

        query = Image.query
        
        # Apply ownership filtering based on role (same logic as main API)
        custom_name = (current_user.custom_role.name.lower() if getattr(current_user, 'custom_role', None) and current_user.custom_role.name else "")
        is_admin_tier = current_user.role in [UserRole.SUPERUSER, UserRole.ADMIN] or custom_name == "subadmin"
        
        if not is_admin_tier:
            # Join uploader to allow including admin-tier uploads for everyone
            query = query.join(User, Image.user_id == User.id)
            query = query.outerjoin(CustomRole, User.custom_role_id == CustomRole.id)
            admin_uploader = or_(
                User.role.in_([UserRole.SUPERUSER, UserRole.ADMIN]),
                and_(User.custom_role_id.isnot(None), CustomRole.name.ilike('%subadmin%'))
            )
            
            if custom_name == "editor":
                try:
                    writer_ids = [w.id for w in getattr(current_user, 'assigned_writers', [])]
                except Exception:
                    writer_ids = []
                allowed_ids = set(writer_ids + [current_user.id])
                # Editor: own images + assigned writers' images + admin/suadmin visible images
                if all_users:
                    # When all_users=true, only show visible admin/suadmin images + own/assigned images
                    query = query.filter(or_(
                        Image.user_id.in_(allowed_ids),
                        and_(admin_uploader, Image.is_visible == True)
                    ))
                else:
                    query = query.filter(or_(Image.user_id.in_(allowed_ids), admin_uploader))
            else:
                # Regular users: own images + admin/suadmin visible images
                if all_users:
                    # When all_users=true, only show visible admin/suadmin images + own images
                    query = query.filter(or_(
                        Image.user_id == current_user.id,
                        and_(admin_uploader, Image.is_visible == True)
                    ))
                else:
                    query = query.filter(or_(Image.user_id == current_user.id, admin_uploader))
        
        if visibility == 'visible':
            if hasattr(Image, 'is_visible'):
                query = query.filter(Image.is_visible.is_(True))
        elif visibility == 'hidden':
            if hasattr(Image, 'is_visible'):
                query = query.filter(Image.is_visible.is_(False))

        pagination = query.order_by(desc(getattr(Image, 'created_at', None))).paginate(page=page, per_page=per_page, error_out=False)
        items = []
        for img in pagination.items:
            items.append(_image_info(img))
        return jsonify({
            'images': items,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
    except Exception as e:
        current_app.logger.error(f"xlate_images_list error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@api_xlate.get('/images/<int:image_id>')
def xlate_image_detail(image_id: int):
    try:
        img = Image.query.get_or_404(image_id)
        return jsonify(_image_info(img))
    except Exception as e:
        current_app.logger.error(f"xlate_image_detail error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
