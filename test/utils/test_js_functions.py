#!/usr/bin/env python3
"""
Test script to verify JavaScript functions are properly defined
"""
import re
import os

def test_users_management_js():
    """Test that users-management.js has the required functions"""
    js_file = '/home/azzar/project/LOC/LILYOPENCMS/static/js/users-management.js'

    if not os.path.exists(js_file):
        print(f"❌ File {js_file} does not exist")
        return False

    with open(js_file, 'r') as f:
        content = f.read()

    # Check for required functions
    required_functions = [
        'loadWriteAccessRequests',
        'renderWriteAccessRequests',
        'updateWriteAccessStats',
        'approveWriteAccess',
        'rejectWriteAccess',
        'viewWriteAccessRequest',
        'bulkApproveWriteAccess',
        'bulkRejectWriteAccess'
    ]

    missing_functions = []
    for func in required_functions:
        if f'async {func}(' not in content and f'{func}(' not in content:
            missing_functions.append(func)

    if missing_functions:
        print(f"❌ Missing functions: {missing_functions}")
        return False

    # Check for global functions
    global_functions = [
        'loadWriteAccessRequests()',
        'approveWriteAccessRequest(',
        'rejectWriteAccessRequest(',
        'viewWriteAccessRequest(',
        'bulkApproveWriteAccess()',
        'bulkRejectWriteAccess()'
    ]

    missing_globals = []
    for func in global_functions:
        if func not in content:
            missing_globals.append(func)

    if missing_globals:
        print(f"❌ Missing global functions: {missing_globals}")
        return False

    print("✅ All required JavaScript functions are present")
    return True

def test_template_references():
    """Test that template references the functions correctly"""
    template_file = '/home/azzar/project/LOC/LILYOPENCMS/templates/admin/settings/users_management.html'

    if not os.path.exists(template_file):
        print(f"❌ Template file {template_file} does not exist")
        return False

    with open(template_file, 'r') as f:
        content = f.read()

    # Check for function call in template
    if 'loadWriteAccessRequests()' not in content:
        print("❌ Template does not call loadWriteAccessRequests()")
        return False

    # Check for bulk action buttons
    if 'bulkApproveWriteAccess()' not in content:
        print("❌ Template does not have bulk approve button")
        return False

    if 'bulkRejectWriteAccess()' not in content:
        print("❌ Template does not have bulk reject button")
        return False

    print("✅ Template correctly references JavaScript functions")
    return True

if __name__ == '__main__':
    print("🧪 Testing JavaScript Functions...")

    js_ok = test_users_management_js()
    template_ok = test_template_references()

    if js_ok and template_ok:
        print("🎉 All tests passed! The write access functionality should work correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
