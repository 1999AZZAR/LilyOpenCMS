from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, User, UserProfile, UserStats, News, Album, UserLibrary, ReadingHistory, Category, WriteAccessRequest
from sqlalchemy import text
import json
from datetime import datetime, timedelta

user_profile_bp = Blueprint('user_profile', __name__)

def has_write_access(user):
    """Check if user has write access (admin tier or write_access granted)."""
    return user.is_admin_tier() or user.write_access == True


@user_profile_bp.route('/user/<username>')
def user_profile(username):
    """Main user profile page with Medium-like tabs."""
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('main.home'))
    
    # Get or create user profile and stats
    profile = UserProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    
    stats = UserStats.query.filter_by(user_id=user.id).first()
    if not stats:
        stats = UserStats(user_id=user.id)
        db.session.add(stats)
        db.session.commit()
    
    # Get active tab
    active_tab = request.args.get('tab', 'home')
    
    # Check if current user is following this user
    is_following = False
    if current_user.is_authenticated:
        is_following = current_user.following.filter_by(id=user.id).first() is not None
    
    # Handle list tab (albums)
    if active_tab == 'list':
        # Check if user has write access or is admin
        if not has_write_access(user):
            flash('Write access required to view albums', 'error')
            return redirect(url_for('user_profile.write_access_request'))
        
        # Get user's albums
        published_albums = Album.query.filter_by(user_id=user.id, is_visible=True).all()
        draft_albums = Album.query.filter_by(user_id=user.id, is_visible=False).all()
        
        return render_template('public/user/profile_list.html', 
                             user=user, 
                             profile=profile, 
                             stats=stats,
                             published_albums=published_albums,
                             draft_albums=draft_albums)
    
    return render_template('public/user/profile.html', 
                         user=user, 
                         profile=profile, 
                         stats=stats, 
                         active_tab=active_tab,
                         is_following=is_following)


@user_profile_bp.route('/api/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    """Follow or unfollow a user."""
    if current_user.id == user_id:
        return jsonify({'error': 'You cannot follow yourself'}), 400
    
    user_to_follow = User.query.get(user_id)
    if not user_to_follow:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already following
    is_following = current_user.following.filter_by(id=user_id).first() is not None
    
    if is_following:
        # Unfollow
        current_user.following.remove(user_to_follow)
        action = 'unfollowed'
    else:
        # Follow
        current_user.following.append(user_to_follow)
        action = 'followed'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'action': action,
        'follower_count': user_to_follow.followers.count()
    })


@user_profile_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile settings."""
    data = request.get_json()
    
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
    
    # Handle username change
    if 'username' in data and data['username'] != current_user.username:
        new_username = data['username'].strip()
        current_password = data.get('current_password', '')
        
        # Validate username format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]{3,20}$', new_username):
            return jsonify({'error': 'Username must be 3-20 characters long and can only contain letters, numbers, underscores, and hyphens'}), 400
        
        # Check if username is already taken
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'error': 'Username already in use'}), 400
        
        # Verify current password
        if not current_password:
            return jsonify({'error': 'Current password is required to change username'}), 400
        
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Update username
        old_username = current_user.username
        current_user.username = new_username
        
        # Update profile URL in response
        new_username_for_redirect = new_username
    
    # Update profile fields
    if 'pronouns' in data:
        profile.pronouns = data['pronouns']
    if 'short_bio' in data:
        profile.short_bio = data['short_bio']
    if 'location' in data:
        profile.location = data['location']
    if 'website' in data:
        profile.website = data['website']
    if 'social_links' in data:
        profile.social_links = data['social_links']
    
    # Update user fields
    if 'first_name' in data:
        current_user.first_name = data['first_name']
    if 'last_name' in data:
        current_user.last_name = data['last_name']
    if 'email' in data:
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'error': 'Email already in use'}), 400
        current_user.email = data['email']
    if 'bio' in data:
        current_user.bio = data['bio']
    if 'birthdate' in data:
        if data['birthdate']:
            try:
                current_user.birthdate = datetime.strptime(data['birthdate'], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({'error': 'Invalid birthdate format'}), 400
        else:
            current_user.birthdate = None
    
    db.session.commit()
    
    response_data = {'success': True, 'message': 'Profile updated successfully'}
    if 'new_username_for_redirect' in locals():
        response_data['new_username'] = new_username_for_redirect
    
    return jsonify(response_data)


@user_profile_bp.route('/api/username/check', methods=['POST'])
@login_required
def check_username_availability():
    """Check if a username is available."""
    data = request.get_json()
    username = data.get('username', '').strip()
    
    # Validate username format
    import re
    if not re.match(r'^[a-zA-Z0-9_-]{3,20}$', username):
        return jsonify({'available': False, 'error': 'Invalid username format'})
    
    # Check if username is already taken
    existing_user = User.query.filter_by(username=username).first()
    is_available = existing_user is None or existing_user.id == current_user.id
    
    return jsonify({'available': is_available})


@user_profile_bp.route('/user/<username>/upload-docx-story')
@login_required
def upload_docx_story(username):
    """User's DOCX story upload page."""
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('main.home'))
    
    # Only allow users to access their own upload page
    if current_user.id != user.id:
        flash('You can only access your own upload page', 'error')
        return redirect(url_for('user_profile.upload_docx_story', username=current_user.username))
    
    # Check write access
    if not has_write_access(user):
        flash('You need write access to upload stories', 'error')
        return redirect(url_for('user_profile.user_profile', username=user.username))
    
    # Get category groups for the form
    from models import CategoryGroup
    category_groups = CategoryGroup.query.filter_by(is_active=True).order_by(CategoryGroup.display_order, CategoryGroup.name).all()
    
    # Get today's date
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    
    return render_template('public/user/upload_docx_story.html', 
                         user=user, 
                         category_groups=category_groups,
                         today=today)


@user_profile_bp.route('/api/user/news', methods=['POST'])
@login_required
def create_user_news_api():
    """Create a new news/story by a regular user with write access.
    Accepts form-data with the same fields as admin `/api/news`.
    """
    # Permission: must have write access
    if not has_write_access(current_user):
        return jsonify({"error": "Write access required"}), 403

    data = request.form

    # Required fields
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    category_id_str = (data.get('category') or '').strip()
    date_str = (data.get('date') or '').strip()  # yyyy-mm-dd

    missing = []
    if not title: missing.append('title')
    if not content: missing.append('content')
    if not category_id_str: missing.append('category')
    if not date_str: missing.append('date')
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Parse category
    try:
        category_id = int(category_id_str)
    except ValueError:
        return jsonify({"error": f"Invalid category id: {category_id_str}"}), 400
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"error": "Category not found"}), 400

    # Parse date
    try:
        from datetime import datetime, timezone
        try:
            news_date = datetime.fromisoformat(date_str)
        except ValueError:
            news_date = datetime.strptime(date_str, "%Y-%m-%d")
        if news_date.tzinfo is None:
            news_date = news_date.replace(tzinfo=timezone.utc)
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD or ISO"}), 400

    # Optional fields
    tagar = (data.get('tagar') or '').strip()
    age_rating = (data.get('age_rating') or '').strip() or 'SU'
    writer = (data.get('writer') or '').strip() or current_user.username
    external_source = (data.get('external_source') or '').strip()
    is_premium = (data.get('is_premium') in ("on", "true", "1", True))
    prize = int((data.get('prize') or 0)) if (data.get('prize') or '').isdigit() else 0
    prize_coin_type = (data.get('prize_coin_type') or 'any')
    image_id = data.get('image_id') or None
    is_visible = str(data.get('is_visible', 'false')).lower() == 'true'

    # Create News owned by current user (not main news)
    news = News(
        title=title,
        content=content,
        tagar=tagar,
        date=news_date,
        category_id=category.id,
        user_id=current_user.id,
        writer=writer,
        external_source=external_source,
        is_premium=is_premium,
        is_news=False,
        is_main_news=False,
        is_visible=is_visible,
        prize=prize,
        prize_coin_type=prize_coin_type,
        image_id=int(image_id) if image_id and str(image_id).isdigit() else None,
    )

    db.session.add(news)
    db.session.commit()

    return jsonify({
        "success": True,
        "id": news.id,
        "is_visible": news.is_visible,
        "redirect_url": url_for('user_profile.user_stories', username=current_user.username)
    }), 201


@user_profile_bp.route('/api/user/upload-docx-story', methods=['POST'])
@login_required
def upload_docx_story_api():
    """API endpoint for uploading DOCX stories."""
    try:
        # Check if user has write access
        if not has_write_access(current_user):
            return jsonify({'success': False, 'error': 'You need write access to upload stories'}), 403
        
        # Get form data
        file = request.files.get('file')
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category')
        date_str = request.form.get('date')
        age_rating = request.form.get('age_rating', '')
        writer = request.form.get('writer', '').strip()
        external_source = request.form.get('external_source', '').strip()
        is_visible = request.form.get('is_visible', 'true').lower() == 'true'  # Default to visible if not specified
        
        # Validate required fields
        if not file:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        if not file.filename.lower().endswith('.docx'):
            return jsonify({'success': False, 'error': 'Only DOCX files are allowed'}), 400
        
        if not category_id:
            return jsonify({'success': False, 'error': 'Category is required'}), 400
        
        if not date_str:
            return jsonify({'success': False, 'error': 'Date is required'}), 400
        
        # Parse date
        try:
            from datetime import datetime, timezone
            story_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format'}), 400
        
        # Get category
        from models import Category
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'success': False, 'error': 'Invalid category'}), 400
        
        # Process the DOCX file using the same logic as admin version
        try:
            # Check if mammoth is available
            try:
                import mammoth
                import io
                import re
            except ImportError:
                return jsonify({'success': False, 'error': 'DOCX processing library not available'}), 500
            
            # Read file bytes
            docx_bytes = file.read()
            if not docx_bytes:
                return jsonify({'success': False, 'error': 'Uploaded file is empty'}), 400
            
            # Convert .docx to HTML using mammoth, then strip to text
            result = mammoth.convert_to_html(io.BytesIO(docx_bytes))
            html = (result.value or "").strip()
            
            # Prefer first <h1>/<h2> as title if title not provided
            heading_match = re.search(r"<h[12][^>]*>(.*?)</h[12]>", html, re.IGNORECASE | re.DOTALL)
            derived_title = None
            if heading_match:
                derived_title = re.sub(r"<[^>]+>", "", heading_match.group(1)).strip()
            
            # Extract possible metadata lines from early paragraphs
            tag_patterns = [r"\bTag(?:ar)?\s*:\s*(?P<value>.+)", r"\bKata\s*Kunci\s*:\s*(?P<value>.+)"]
            meta_description = None
            tags_value = None
            summary_value = None
            
            # Find first few paragraphs
            paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.IGNORECASE | re.DOTALL)
            cleaned_paragraphs = []
            for idx, p in enumerate(paragraphs[:8]):
                # Plain text for checks
                p_text = re.sub(r"<[^>]+>", "", p).strip()
                if not tags_value:
                    for pat in tag_patterns:
                        m = re.search(pat, p_text, re.IGNORECASE)
                        if m:
                            try:
                                tags_value = m.group('value').strip()
                            except IndexError:
                                tags_value = m.group(m.lastindex).strip() if m.lastindex else None
                            break
                # Summary line like "Ringkasan:" or "Ringkasan -"
                if summary_value is None:
                    sm = re.search(r"^\s*Ringkasan\s*[:\-]\s*(?P<sum>.+)$", p_text, re.IGNORECASE)
                    if sm:
                        summary_value = sm.group('sum').strip()
                if not meta_description and len(p_text) >= 40 and not re.search(r"\b(Tag(ar)?|Kata\s*Kunci)\s*:", p_text, re.IGNORECASE):
                    meta_description = p_text
                cleaned_paragraphs.append(p_text)
            
            # Remove explicit metadata and title from HTML content
            content_html = html
            
            # Remove tags line paragraph
            if tags_value:
                content_html = re.sub(r"<p[^>]*>[^<]*?(Tag(?:ar)?|Kata\s*Kunci)\s*:[\s\S]*?</p>", "", content_html, flags=re.IGNORECASE)
                content_html = re.sub(r"<div[^>]*>[^<]*?(Tag(?:ar)?|Kata\s*Kunci)\s*:[\s\S]*?</div>", "", content_html, flags=re.IGNORECASE)
                content_html = re.sub(r"[^<]*?(Tag(?:ar)?|Kata\s*Kunci)\s*:[\s\S]*?(?=<[^>]*>)", "", content_html, flags=re.IGNORECASE)
                content_html = re.sub(r"<span[^>]*>[^<]*?(Tag(?:ar)?|Kata\s*Kunci)\s*:[\s\S]*?</span>", "", content_html, flags=re.IGNORECASE)
                content_html = re.sub(r"<strong[^>]*>[^<]*?(Tag(?:ar)?|Kata\s*Kunci)\s*:[\s\S]*?</strong>", "", content_html, flags=re.IGNORECASE)
                content_html = re.sub(r"<b[^>]*>[^<]*?(Tag(?:ar)?|Kata\s*Kunci)\s*:[\s\S]*?</b>", "", content_html, flags=re.IGNORECASE)
                content_html = re.sub(r"(?:<[^>]*>)?[^<]*?(Tag(?:ar)?|Kata\s*Kunci)\s*:[\s\S]*?(?:</[^>]*>)?", "", content_html, flags=re.IGNORECASE)
            
            # Remove summary line paragraph
            if summary_value:
                content_html = re.sub(r"<p[^>]*>\s*<strong>\s*Ringkasan\s*[:\-]\s*</strong>\s*[\s\S]*?</p>", "", content_html, flags=re.IGNORECASE)
                content_html = re.sub(r"<p[^>]*>\s*Ringkasan\s*[:\-][\s\S]*?</p>", "", content_html, flags=re.IGNORECASE)
            
            # Remove the first short guidance line if template text present
            content_html = re.sub(r"<p[^>]*>\s*Ringkasan\s+singkat[\s\S]*?</p>", "", content_html, flags=re.IGNORECASE)
            
            # Remove the first H1/H2 title if present to avoid duplicating in content
            try:
                if heading_match:
                    content_html = re.sub(r"\s*<h[12][^>]*>[\s\S]*?</h[12]>\s*", "", content_html, count=1, flags=re.IGNORECASE)
            except Exception:
                pass
            
            # Normalize empty paragraphs and excessive breaks
            content_html = re.sub(r"<p[^>]*>\s*(?:&nbsp;|\u00A0|\s)*</p>", "", content_html, flags=re.IGNORECASE)
            content_html = re.sub(r"(\s*<br\s*/?>\s*){3,}", "<br><br>", content_html, flags=re.IGNORECASE)
            
            # Convert HTML to Markdown for better content formatting
            def html_to_markdown(html_content):
                """Convert HTML to Markdown format with improved formatting"""
                if not html_content:
                    return ""
                
                markdown = html_content
                
                # Clean up HTML entities first
                markdown = markdown.replace('&quot;', '"')
                markdown = markdown.replace('&amp;', '&')
                markdown = markdown.replace('&lt;', '<')
                markdown = markdown.replace('&gt;', '>')
                markdown = markdown.replace('&nbsp;', ' ')
                markdown = markdown.replace('\u00A0', ' ')
                
                # Headings
                markdown = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n\n# \1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n\n## \1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n\n### \1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n\n#### \1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<h5[^>]*>(.*?)</h5>', r'\n\n##### \1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<h6[^>]*>(.*?)</h6>', r'\n\n###### \1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                
                # Bold and italic
                markdown = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', markdown, flags=re.IGNORECASE | re.DOTALL)
                
                # Links
                markdown = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', markdown, flags=re.IGNORECASE | re.DOTALL)
                
                # Lists
                markdown = re.sub(r'<ul[^>]*>(.*?)</ul>', r'\n\1\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<ol[^>]*>(.*?)</ol>', r'\n\1\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                
                # Paragraphs and line breaks
                markdown = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<br\s*/?>', r'\n', markdown, flags=re.IGNORECASE)
                
                # Blockquotes
                markdown = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'\n> \1\n\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                
                # Code blocks
                markdown = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', markdown, flags=re.IGNORECASE | re.DOTALL)
                markdown = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', markdown, flags=re.IGNORECASE | re.DOTALL)
                
                # Remove any remaining HTML tags
                markdown = re.sub(r'<[^>]+>', '', markdown)
                
                # Clean up whitespace and formatting
                markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
                markdown = re.sub(r' +', ' ', markdown)
                markdown = re.sub(r'\n +', '\n', markdown)
                markdown = re.sub(r' +\n', '\n', markdown)
                
                # Ensure proper spacing around headings
                markdown = re.sub(r'([^\n])\n#', r'\1\n\n#', markdown)
                markdown = re.sub(r'([^\n])\n##', r'\1\n\n##', markdown)
                markdown = re.sub(r'([^\n])\n###', r'\1\n\n###', markdown)
                
                # Clean up list formatting
                markdown = re.sub(r'\n- ([^\n]+)\n([^-])', r'\n- \1\n\n\2', markdown)
                
                return markdown.strip()
            
            # Convert HTML to Markdown
            content_markdown = html_to_markdown(content_html)
            
            # Clean up tag content from markdown
            if tags_value:
                content_markdown = re.sub(r'^\*\*Tag(?:ar)?/Kata Kunci:\*\*.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^\*\*Tag(?:ar)?:\*\*.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^\*\*Kata Kunci:\*\*.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^Tag(?:ar)?/Kata Kunci:.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^Tag(?:ar)?:.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^Kata Kunci:.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                
                # Remove specific tag line patterns
                content_markdown = re.sub(r'^\*\*Tag(?:ar)?/Kata Kunci:\*\*.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^\*\*Tag(?:ar)?:\*\*.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^\*\*Kata Kunci:\*\*.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^Tag(?:ar)?/Kata Kunci:.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^Tag(?:ar)?:.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^Kata Kunci:.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                
                # Remove lines that contain tag information but are not part of actual content
                content_markdown = re.sub(r'^.*?\*\*Tag(?:ar)?/Kata Kunci:\*\*.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                content_markdown = re.sub(r'^.*?Tag(?:ar)?/Kata Kunci:.*$', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                
                # Remove the tag line that appears at the beginning of content
                if tags_value:
                    tag_pattern = re.escape(tags_value.strip())
                    content_markdown = re.sub(rf'^{tag_pattern}\s*\n', '', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
                    content_markdown = re.sub(rf'^{tag_pattern}\s*\n\n', '\n\n', content_markdown, flags=re.IGNORECASE | re.MULTILINE)
            
            # Clean up any resulting empty lines
            content_markdown = re.sub(r'\n{3,}', '\n\n', content_markdown)
            content_markdown = content_markdown.strip()
            
            # Also create a plain text fallback
            plain_text = re.sub(r"<br\s*/?>", "\n", content_html)
            plain_text = re.sub(r"<[^>]+>", "", plain_text)
            content_text = re.sub(r"\n{3,}", "\n\n", plain_text).strip()
            
            # Use the processed title
            final_title = title or derived_title or (file.filename.rsplit(".", 1)[0])
            
            # Create the story with processed content
            from models import News
            story = News(
                title=final_title.strip(),
                content=content_markdown or content_html or content_text,
                tagar=tags_value or None,
                date=story_date,
                read_count=0,
                category_id=category.id,
                is_news=False,  # This is a story, not news
                is_premium=False,
                is_main_news=False,
                is_visible=is_visible,
                is_archived=False,
                user_id=current_user.id,
                writer=writer if writer else current_user.username,
                external_source=external_source if external_source else None,
                age_rating=age_rating if age_rating else 'SU',
                prize=0,
                prize_coin_type='any'
            )
            
            db.session.add(story)
            db.session.commit()
            
            # Set meta description if available
            try:
                if hasattr(story, 'meta_description'):
                    if summary_value:
                        story.meta_description = summary_value[:500]
                    elif meta_description:
                        story.meta_description = meta_description[:500]
            except Exception:
                pass
            
            # Calculate SEO score
            story.seo_score = story.calculate_seo_score()
            story.last_seo_audit = datetime.now(timezone.utc)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Error processing DOCX file: {str(e)}'}), 500
        
        return jsonify({
            'success': True, 
            'message': 'Story uploaded successfully',
            'redirect_url': url_for('user_profile.user_stories', username=current_user.username)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@user_profile_bp.route('/user/<username>/library')
@login_required
def user_library(username):
    """User's library page."""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only allow users to view their own library
    if current_user.id != user.id:
        flash('You can only view your own library', 'error')
        return redirect(url_for('user_profile.user_library', username=current_user.username))
    
    # Get library items with content details
    library_items = db.session.query(UserLibrary, News, Album).outerjoin(
        News, db.and_(UserLibrary.content_type == 'news', UserLibrary.content_id == News.id)
    ).outerjoin(
        Album, db.and_(UserLibrary.content_type == 'album', UserLibrary.content_id == Album.id)
    ).filter(UserLibrary.user_id == user.id).order_by(UserLibrary.added_at.desc()).all()
    
    # Get reading history with content details
    reading_history = db.session.query(ReadingHistory, News, Album).outerjoin(
        News, db.and_(ReadingHistory.content_type == 'news', ReadingHistory.content_id == News.id)
    ).outerjoin(
        Album, db.and_(ReadingHistory.content_type == 'album', ReadingHistory.content_id == Album.id)
    ).filter(ReadingHistory.user_id == user.id).order_by(ReadingHistory.last_read_at.desc()).all()
    
    # Get user's own albums
    own_albums = Album.query.filter_by(user_id=user.id, is_visible=True).order_by(Album.created_at.desc()).all()
    
    # Get active tab from URL parameter
    active_tab = request.args.get('tab', 'your-list')
    
    # Debug output
    print(f"DEBUG: Library items count: {len(library_items)}")
    print(f"DEBUG: Reading history count: {len(reading_history)}")
    print(f"DEBUG: Own albums count: {len(own_albums)}")
    print(f"DEBUG: Active tab: {active_tab}")
    
    return render_template('public/user/library.html', 
                         user=user, 
                         library_items=library_items,
                         reading_history=reading_history,
                         own_albums=own_albums,
                         active_tab=active_tab)


@user_profile_bp.route('/user/<username>/stories/create')
@login_required
def create_user_story(username):
    """Create a new story for users with write access."""
    # Check if user is trying to create story for themselves
    if current_user.username != username:
        flash('You can only create stories for your own account', 'error')
        return redirect(url_for('user_profile.user_profile', username=current_user.username))
    
    # Check if user has write access
    # Admin tier users always have write access, regardless of write_access field
    if not current_user.is_admin_tier() and not current_user.write_access:
        flash('Write access required to create stories', 'error')
        return redirect(url_for('user_profile.write_access_request'))
    
    # Optional prefill id for editing
    news_id = request.args.get('news_id', type=int)
    
    # Get categories for the dropdown
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    
    return render_template('public/user/create_story.html', 
                         user=current_user, 
                         news_id=news_id,
                         categories=categories)


@user_profile_bp.route('/user/<username>/stories')
@login_required
def user_stories(username):
    """User's stories page."""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only allow users to view their own stories
    if current_user.id != user.id:
        flash('You can only view your own stories', 'error')
        return redirect(url_for('user_profile.user_stories', username=current_user.username))
    
    # Check write access
    if not has_write_access(current_user):
        flash('Write access required to view stories', 'error')
        return redirect(url_for('user_profile.write_access_request'))
    
    # Get published and draft stories
    published_stories = News.query.filter_by(user_id=user.id, is_visible=True).order_by(News.created_at.desc()).all()
    draft_stories = News.query.filter_by(user_id=user.id, is_visible=False).order_by(News.created_at.desc()).all()
    
    return render_template('public/user/stories.html', 
                         user=user, 
                         published_stories=published_stories,
                         draft_stories=draft_stories)


@user_profile_bp.route('/user/<username>/stats')
@login_required
def user_stats(username):
    """User's analytics page."""
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Only allow users to view their own stats
    if current_user.id != user.id:
        flash('You can only view your own stats', 'error')
        return redirect(url_for('user_profile.user_stats', username=current_user.username))
    
    # Get or create stats
    stats = UserStats.query.filter_by(user_id=user.id).first()
    if not stats:
        stats = UserStats(user_id=user.id)
        db.session.add(stats)
        db.session.commit()
    
    # Update stats
    stats.update_stats()
    db.session.commit()
    
    return render_template('public/user/stats.html', 
                         user=user, 
                         stats=stats)


@user_profile_bp.route('/user/<username>/settings')
@login_required
def user_settings(username):
    """User's settings page."""
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('main.home'))
    
    # Only allow users to view their own settings
    if current_user.id != user.id:
        flash('You can only view your own settings', 'error')
        return redirect(url_for('user_profile.user_settings', username=current_user.username))
    
    # Get or create user profile
    profile = UserProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    
    return render_template('public/user/profile_settings.html', user=user, profile=profile)

@user_profile_bp.route('/write-access-request')
@login_required
def write_access_request():
    """Write access request page."""
    return render_template('public/user/write_access_request.html')


@user_profile_bp.route('/api/write-access/request', methods=['POST'])
@login_required
def request_write_access():
    """Submit a write access request."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check if user already has write access
        if current_user.write_access:
            return jsonify({'error': 'You already have write access'}), 400
        
        # Check if user already has a pending request
        existing_request = WriteAccessRequest.query.filter_by(
            user_id=current_user.id, 
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({'error': 'You already have a pending request'}), 400
        
        # Create new request
        new_request = WriteAccessRequest(
            user_id=current_user.id,
            request_reason=data.get('reason', ''),
            portfolio_links=data.get('portfolio_links', ''),
            experience_description=data.get('experience', '')
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Write access request submitted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to submit request: {str(e)}'}), 500


@user_profile_bp.route('/api/write-access-requests/<int:request_id>')
@login_required
def get_write_access_request(request_id):
    """Get a specific write access request."""
    if not current_user.is_admin_tier():
        return jsonify({'error': 'Access denied'}), 403
    
    request_obj = WriteAccessRequest.query.get_or_404(request_id)
    
    return jsonify({
        'success': True,
        'request': request_obj.to_dict()
    })


@user_profile_bp.route('/api/write-access-requests/<int:request_id>/review', methods=['POST'])
@login_required
def review_write_access_request(request_id):
    """Review a write access request (approve/reject)."""
    if not current_user.is_admin_tier():
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    decision = data.get('decision')  # 'approved' or 'rejected'
    admin_notes = data.get('admin_notes', '')
    
    if decision not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid decision'}), 400
    
    request_obj = WriteAccessRequest.query.get_or_404(request_id)
    
    if request_obj.status != 'pending':
        return jsonify({'error': 'Request has already been reviewed'}), 400
    
    # Update the request
    request_obj.status = decision
    request_obj.admin_notes = admin_notes
    request_obj.reviewed_by_id = current_user.id
    request_obj.reviewed_at = datetime.utcnow()
    
    # If approved, grant write access to the user
    if decision == 'approved':
        request_obj.user.write_access = True
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Request {decision} successfully'
    })


@user_profile_bp.route('/api/write-access-requests')
@login_required
def get_write_access_requests():
    """Get all write access requests with filtering."""
    if not current_user.is_admin_tier():
        return jsonify({'error': 'Access denied'}), 403
    
    status_filter = request.args.get('status', '')
    search_term = request.args.get('search', '')
    date_filter = request.args.get('date_filter', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = WriteAccessRequest.query.join(WriteAccessRequest.user)
    
    # Apply filters
    if status_filter:
        query = query.filter(WriteAccessRequest.status == status_filter)
    
    if search_term:
        query = query.filter(
            db.or_(
                User.username.contains(search_term),
                User.email.contains(search_term),
                WriteAccessRequest.request_reason.contains(search_term)
            )
        )
    
    # Date filtering
    if date_filter == 'today':
        today = datetime.now().date()
        query = query.filter(db.func.date(WriteAccessRequest.requested_at) == today)
    elif date_filter == 'week':
        week_ago = datetime.now() - timedelta(days=7)
        query = query.filter(WriteAccessRequest.requested_at >= week_ago)
    elif date_filter == 'month':
        month_ago = datetime.now() - timedelta(days=30)
        query = query.filter(WriteAccessRequest.requested_at >= month_ago)
    
    # Pagination
    pagination = query.order_by(WriteAccessRequest.requested_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    requests = [req.to_dict() for req in pagination.items]
    
    # Get statistics
    stats = {
        'total_pending': WriteAccessRequest.query.filter_by(status='pending').count(),
        'approved_today': WriteAccessRequest.query.filter(
            WriteAccessRequest.status == 'approved',
            db.func.date(WriteAccessRequest.reviewed_at) == datetime.now().date()
        ).count(),
        'rejected_today': WriteAccessRequest.query.filter(
            WriteAccessRequest.status == 'rejected',
            db.func.date(WriteAccessRequest.reviewed_at) == datetime.now().date()
        ).count(),
    }
    
    return jsonify({
        'success': True,
        'requests': requests,
        'pagination': {
            'page': page,
            'pages': pagination.pages,
            'per_page': per_page,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        },
        'stats': stats
    })


@user_profile_bp.route('/api/library/add', methods=['POST'])
@login_required
def add_to_library():
    """Add content to user's library."""
    data = request.get_json()
    content_type = data.get('content_type')  # 'news' or 'album'
    content_id = data.get('content_id')
    
    if not content_type or not content_id:
        return jsonify({'error': 'Missing content_type or content_id'}), 400
    
    if content_type not in ['news', 'album']:
        return jsonify({'error': 'Invalid content_type'}), 400
    
    # Check if already in library
    existing = UserLibrary.query.filter_by(
        user_id=current_user.id,
        content_type=content_type,
        content_id=content_id
    ).first()
    
    if existing:
        return jsonify({'error': 'Already in library'}), 400
    
    # Add to library
    library_item = UserLibrary(
        user_id=current_user.id,
        content_type=content_type,
        content_id=content_id
    )
    
    db.session.add(library_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Added to library'})


@user_profile_bp.route('/api/library/remove', methods=['POST'])
@login_required
def remove_from_library():
    """Remove content from user's library."""
    data = request.get_json()
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    
    if not content_type or not content_id:
        return jsonify({'error': 'Missing content_type or content_id'}), 400
    
    # Find and remove from library
    library_item = UserLibrary.query.filter_by(
        user_id=current_user.id,
        content_type=content_type,
        content_id=content_id
    ).first()
    
    if not library_item:
        return jsonify({'error': 'Not in library'}), 404
    
    db.session.delete(library_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Removed from library'})


@user_profile_bp.route('/api/library/check', methods=['GET'])
@login_required
def check_library_status():
    """Check if content is in user's library."""
    content_type = request.args.get('content_type')
    content_id = request.args.get('content_id')
    
    if not content_type or not content_id:
        return jsonify({'error': 'Missing content_type or content_id'}), 400
    
    try:
        content_id = int(content_id)
    except ValueError:
        return jsonify({'error': 'Invalid content_id'}), 400
    
    # Check if in library
    library_item = UserLibrary.query.filter_by(
        user_id=current_user.id,
        content_type=content_type,
        content_id=content_id
    ).first()
    
    return jsonify({'in_library': library_item is not None})


@user_profile_bp.route('/api/reading-history/record', methods=['POST'])
@login_required
def record_reading():
    """Record reading activity."""
    data = request.get_json()
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    
    if not content_type or not content_id:
        return jsonify({'error': 'Missing content_type or content_id'}), 400
    
    # Find existing reading history
    history_item = ReadingHistory.query.filter_by(
        user_id=current_user.id,
        content_type=content_type,
        content_id=content_id
    ).first()
    
    if history_item:
        # Update existing record
        history_item.read_count += 1
        history_item.last_read_at = datetime.utcnow()
    else:
        # Create new record
        history_item = ReadingHistory(
            user_id=current_user.id,
            content_type=content_type,
            content_id=content_id,
            read_count=1
        )
        db.session.add(history_item)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Reading recorded'})


@user_profile_bp.route('/api/albums/<int:album_id>/request-deletion', methods=['POST'])
@login_required
def request_album_deletion_user(album_id):
    """Request deletion of an album (user-facing API)."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    album = Album.query.get_or_404(album_id)
    
    # Check if user owns this album
    if album.user_id != current_user.id:
        return jsonify({"error": "You can only request deletion of your own albums"}), 403

    # Check if already requested
    if album.deletion_requested:
        return jsonify({"error": "Deletion already requested for this album"}), 400

    try:
        album.deletion_requested = True
        album.deletion_requested_at = datetime.utcnow()
        album.deletion_requested_by = current_user.id
        db.session.commit()
        
        current_app.logger.info(
            f"Album deletion requested: '{album.title}' (ID: {album_id}) by user {current_user.username}"
        )
        return jsonify({"message": "Deletion request submitted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error requesting album deletion ID {album_id} by {current_user.username}: {e}"
        )
        return jsonify({"error": "Failed to submit deletion request"}), 500



@user_profile_bp.route('/user/<username>/following')
def user_following(username):
    """User's following/followers page with tabs."""
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('main.home'))
    
    # Get active tab
    active_tab = request.args.get('tab', 'following')
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if active_tab == 'following':
        pagination = user.following.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        total_following = user.following.count()
        total_followers = user.followers.count()
    else:  # followers
        pagination = user.followers.paginate(page=page, per_page=per_page, error_out=False)
        users = pagination.items
        total_following = user.following.count()
        total_followers = user.followers.count()
    
    current_following_ids = set()
    if current_user.is_authenticated:
        current_following_ids = set([u.id for u in current_user.following.all()])
    
    return render_template(
        'public/user/follow_list.html',
        user=user,
        users=users,
        type=active_tab,
        total_following=total_following,
        total_followers=total_followers,
        page=page,
        per_page=per_page,
        total=pagination.total,
        pages=pagination.pages,
        has_prev=pagination.has_prev,
        has_next=pagination.has_next,
        prev_page=pagination.prev_num if pagination.has_prev else None,
        next_page=pagination.next_num if pagination.has_next else None,
        current_following_ids=current_following_ids,
        active_tab=active_tab
    )
