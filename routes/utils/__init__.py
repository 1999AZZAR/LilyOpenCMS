"""
Routes Utils Package

This package contains utility modules for the routes system.
"""

from .permission_manager import (
    can_access_admin,
    can_manage_users,
    can_manage_content,
    can_manage_categories,
    can_manage_settings,
    can_manage_roles,
    can_manage_ads,
    can_moderate_comments,
    can_manage_ratings,
    can_access_analytics,
    can_manage_legal,
    can_manage_brand,
    can_manage_seo,
    has_permission,
    has_any_permission,
    has_all_permissions,
    get_user_role_display,
    get_user_permissions_summary,
    is_superuser,
    is_admin,
    is_admin_tier,
    has_custom_role,
    PermissionManager
)

from .role_manager import (
    RoleManager,
    get_user_role_display as get_user_role_display_role,
    can_assign_roles,
    can_assign_custom_roles,
    get_available_roles,
    get_available_custom_roles,
    get_role_statistics
)

__all__ = [
    # Permission management
    'can_access_admin',
    'can_manage_users',
    'can_manage_content', 
    'can_manage_categories',
    'can_manage_settings',
    'can_manage_roles',
    'can_manage_ads',
    'can_moderate_comments',
    'can_manage_ratings',
    'can_access_analytics',
    'can_manage_legal',
    'can_manage_brand',
    'can_manage_seo',
    'has_permission',
    'has_any_permission',
    'has_all_permissions',
    'get_user_role_display',
    'get_user_permissions_summary',
    'is_superuser',
    'is_admin',
    'is_admin_tier',
    'has_custom_role',
    'PermissionManager',
    
    # Role management
    'RoleManager',
    'get_user_role_display_role',
    'can_assign_roles',
    'can_assign_custom_roles',
    'get_available_roles',
    'get_available_custom_roles',
    'get_role_statistics'
]
