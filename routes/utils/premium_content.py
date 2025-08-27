"""
Premium Content Utility Functions

This module provides utilities for handling premium content filtering,
content truncation, and premium status checking.
"""

import re
from typing import Tuple, Optional
from flask import current_app
from flask_login import current_user


def is_premium_user() -> bool:
    """
    Check if the current user has active premium access.
    
    Returns:
        bool: True if user has active premium subscription, False otherwise
    """
    if not current_user.is_authenticated:
        return False
    
    return current_user.has_active_premium_subscription()


def should_show_premium_content(content_is_premium: bool) -> bool:
    """
    Determine if premium content should be shown to the current user.
    
    Args:
        content_is_premium (bool): Whether the content is marked as premium
        
    Returns:
        bool: True if content should be shown, False if it should be truncated
    """
    if not content_is_premium:
        return True  # Non-premium content is always shown
    
    return is_premium_user()


def truncate_markdown_content(content: str, max_words: int = 150) -> Tuple[str, bool]:
    """
    Truncate markdown content to a specified number of words while preserving markdown structure.
    
    Args:
        content (str): The markdown content to truncate
        max_words (int): Maximum number of words to show
        
    Returns:
        Tuple[str, bool]: (truncated_content, was_truncated)
    """
    if not content:
        return "", False
    
    # Split content into words while preserving markdown structure
    words = re.findall(r'\S+|\n+', content)
    
    if len(words) <= max_words:
        return content, False
    
    # Take first max_words words
    truncated_words = words[:max_words]
    
    # Reconstruct content
    truncated_content = ''.join(truncated_words)
    
    # Add ellipsis if content was truncated
    if truncated_content and not truncated_content.endswith('\n'):
        truncated_content += '...'
    
    return truncated_content, True


def process_premium_content(content: str, is_premium_content: bool, max_words: int = 150) -> Tuple[str, bool, bool]:
    """
    Process content based on premium status and user access.
    
    Args:
        content (str): The original content
        is_premium_content (bool): Whether the content is premium
        max_words (int): Maximum words to show for non-premium users
        
    Returns:
        Tuple[str, bool, bool]: (processed_content, is_truncated, show_premium_notice)
    """
    if not should_show_premium_content(is_premium_content):
        # User doesn't have premium access for premium content
        truncated_content, was_truncated = truncate_markdown_content(content, max_words)
        return truncated_content, was_truncated, True
    
    # User has access to full content
    return content, False, False


def get_premium_content_stats(content: str, is_premium_content: bool) -> dict:
    """
    Get statistics about premium content processing.
    
    Args:
        content (str): The original content
        is_premium_content (bool): Whether the content is premium
        
    Returns:
        dict: Statistics about the content
    """
    if not content:
        return {
            'total_words': 0,
            'total_chars': 0,
            'is_premium': is_premium_content,
            'user_has_access': should_show_premium_content(is_premium_content)
        }
    
    words = re.findall(r'\S+', content)
    chars = len(content)
    
    return {
        'total_words': len(words),
        'total_chars': chars,
        'is_premium': is_premium_content,
        'user_has_access': should_show_premium_content(is_premium_content)
    }


def generate_premium_notice_html(content_type: str = "artikel") -> str:
    """
    Generate HTML for premium content notice.
    
    Args:
        content_type (str): Type of content (artikel, bab, etc.)
        
    Returns:
        str: HTML for premium notice
    """
    return f"""
    <div class="premium-content-notice bg-gradient-to-r from-primary/10 to-secondary/10 border border-primary/20 rounded-lg p-6 my-6">
        <div class="flex items-center gap-3 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-6 h-6 text-primary">
                <path fill-rule="evenodd" d="M5.166 2.621v.858c-1.035.148-2.059.33-3.071.543a.75.75 0 00-.584.859 6.937 6.937 0 006.222 6.222.75.75 0 00.859-.584 48.332 48.332 0 001.243-5.034 48.332 48.332 0 005.034-1.243.75.75 0 00.584-.859 6.937 6.937 0 00-6.222-6.222.75.75 0 00-.859.584 48.332 48.332 0 00-1.243 5.034zM13.5 2.25a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM13.5 6.75a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0V7.5a.75.75 0 01.75-.75zM13.5 11.25a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0V12a.75.75 0 01.75-.75z" clip-rule="evenodd" />
            </svg>
            <h3 class="text-lg font-semibold text-foreground">Konten Premium</h3>
        </div>
        <p class="text-muted-foreground mb-4">Untuk membaca {content_type} ini secara lengkap, Anda memerlukan langganan premium.</p>
        <div class="flex flex-wrap gap-3">
            <a href="/premium" class="button button-primary">
                Berlangganan Premium
            </a>
            <a href="/login" class="button button-outline">
                Login
            </a>
        </div>
    </div>
    """


def create_content_mask_html(content_id: str, content_type: str = "artikel") -> str:
    """
    Create HTML for content mask overlay.
    
    Args:
        content_id (str): Unique identifier for the content
        content_type (str): Type of content
        
    Returns:
        str: HTML for content mask
    """
    return f"""
    <div id="content-mask-{content_id}" class="content-mask-overlay">
        <div class="content-mask-backdrop"></div>
        <div class="content-mask-content">
            <div class="content-mask-icon">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-12 h-12">
                    <path fill-rule="evenodd" d="M5.166 2.621v.858c-1.035.148-2.059.33-3.071.543a.75.75 0 00-.584.859 6.937 6.937 0 006.222 6.222.75.75 0 00.859-.584 48.332 48.332 0 001.243-5.034 48.332 48.332 0 005.034-1.243.75.75 0 00.584-.859 6.937 6.937 0 00-6.222-6.222.75.75 0 00-.859.584 48.332 48.332 0 00-1.243 5.034zM13.5 2.25a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM13.5 6.75a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0V7.5a.75.75 0 01.75-.75zM13.5 11.25a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0V12a.75.75 0 01.75-.75z" clip-rule="evenodd" />
                </svg>
            </div>
            <h3 class="text-xl font-semibold text-foreground mb-2">Konten Premium</h3>
            <p class="text-muted-foreground text-center mb-4">Untuk membaca {content_type} ini secara lengkap, Anda memerlukan langganan premium.</p>
            <div class="flex flex-col sm:flex-row gap-3 justify-center">
                <a href="/premium" class="button button-primary">
                    Berlangganan Premium
                </a>
                <a href="/login" class="button button-outline">
                    Login
                </a>
            </div>
        </div>
    </div>
    """ 