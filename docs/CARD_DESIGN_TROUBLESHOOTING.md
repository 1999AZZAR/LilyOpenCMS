# Card Design System - Troubleshooting Guide

## 🚨 Common Issues & Solutions

### Issue: Card Design Changes Get Stuck

**Symptoms:**
- Button shows "Updating..." but never completes
- Form becomes unresponsive after first change
- Multiple clicks don't work

**Root Cause:**
- Multiple event listeners attached to the same form
- JavaScript errors preventing form submission
- Network issues or API errors

**Solutions:**

1. **Refresh the Page**
   - Simple refresh (F5) often resolves event listener conflicts
   - Clears any stuck JavaScript state

2. **Check Browser Console**
   - Open Developer Tools (F12)
   - Look for JavaScript errors in Console tab
   - Run `debugCardDesign('form-card-classic')` to check form state

3. **Clear Browser Cache**
   - Hard refresh (Ctrl+F5 or Cmd+Shift+R)
   - Clear browser cache and cookies for the site

4. **Check Network Tab**
   - Open Developer Tools → Network tab
   - Try changing card design
   - Look for failed API requests to `/api/brand-identity/text`

### Issue: Card Design Not Applying to News Page

**Symptoms:**
- Admin shows design is changed
- News page still shows old design
- CSS classes not updating

**Status**: ✅ **FIXED** - The issue has been resolved with improved initialization and fresh data loading.

**Root Cause**: The route was explicitly passing `brand_info` to the template, overriding the context processor, and not using fresh data loading.

**Solutions:**

1. **Automatic Initialization** ✅
   - The page now automatically fetches the latest brand info on load
   - Brand info initialization happens before content loading
   - No manual intervention required

2. **Fresh Data Loading** ✅
   - Route now uses `db.session.expire_all()` and `db.session.refresh(brand_info)`
   - Context processor ensures latest data is always fetched
   - Template relies on context processor instead of route parameter

3. **Use Manual Refresh Button**
   - Click the refresh button (🔄) next to the search bar
   - This will fetch the latest brand info from the server

4. **Wait for Auto-Refresh**
   - The page automatically refreshes brand info every 30 seconds
   - Wait up to 30 seconds for changes to appear

5. **Check Real-time Updates**
   - If you have both admin and news pages open, changes should apply immediately
   - Check browser console for "Card design changed" messages

6. **Check Brand Info Loading**
   - Verify `window.brandInfo` exists in browser console
   - Check if `card_design` field is present

7. **Clear Frontend Cache**
   - Hard refresh the news page (Ctrl+F5)
   - Clear browser cache

8. **Check CSS Classes**
   - Inspect news cards in browser
   - Verify CSS class includes design name (e.g., `news-card modern`)

**Technical Details**:
- Fixed route in `routes/routes_public.py` to use fresh data loading
- Removed explicit `brand_info` parameter from template call
- Updated JavaScript initialization order in `static/js/news-search.js`
- Brand info is now initialized before content loading

### Issue: API Errors

**Symptoms:**
- Error messages in console
- 400 or 500 HTTP errors
- "Update failed" messages

**Solutions:**

1. **Check API Endpoint**
   - Verify `/api/brand-identity/text` is accessible
   - Check if `card_design` is in allowed fields

2. **Check CSRF Token**
   - Ensure CSRF token is present
   - Try refreshing the page to get new token

3. **Check Database**
   - Verify `card_design` column exists in `brand_identity` table
   - Run safe migration if needed

## 🔧 Debugging Commands

### Browser Console Commands

```javascript
// Check brand info
console.log(window.brandInfo);

// Debug specific form
debugCardDesign('form-card-classic');
debugCardDesign('form-card-modern');
debugCardDesign('form-card-minimal');
debugCardDesign('form-card-featured');

// Check all card design forms
document.querySelectorAll('[name="card_design"]').forEach(btn => {
  console.log('Form:', btn.closest('form').id, 'Value:', btn.value);
});

// Manually refresh brand info
refreshBrandInfo();

// Check current card design
console.log('Current card design:', window.brandInfo?.card_design);

// Force refresh news cards
window.refreshNewsCards();
```

### Database Verification

```sql
-- Check if card_design column exists
PRAGMA table_info(brand_identity);

-- Check current card design value
SELECT card_design FROM brand_identity LIMIT 1;

-- Update card design manually (if needed)
UPDATE brand_identity SET card_design = 'classic' WHERE id = 1;
```

## 🛠️ Manual Recovery Steps

### If System is Completely Stuck

1. **Database Reset**
   ```sql
   UPDATE brand_identity SET card_design = 'classic' WHERE id = 1;
   ```

2. **Clear Browser Data**
   - Clear all site data
   - Hard refresh all pages

3. **Check Server Logs**
   - Look for Python errors in server console
   - Check for API endpoint issues

### If CSS Classes Not Working

1. **Verify CSS File**
   - Check if `static/css/news.css` is loaded
   - Verify card design CSS classes exist

2. **Check Template**
   - Verify `templates/public/news.html` includes brand info
   - Check JavaScript integration

## 📋 System Health Checklist

- [ ] Database has `card_design` column
- [ ] API endpoint accepts `card_design` field
- [ ] Brand info is loaded in news template
- [ ] CSS classes are applied correctly
- [ ] JavaScript event handlers are working
- [ ] No console errors
- [ ] Network requests succeed

## 🆘 Getting Help

If issues persist:

1. **Collect Debug Info**
   - Browser console errors
   - Network tab requests
   - Current card design value from database

2. **Check Recent Changes**
   - Any recent code changes
   - Database migrations
   - Browser updates

3. **Test in Different Browser**
   - Try incognito/private mode
   - Test in different browser

## 🔄 Prevention Tips

1. **Avoid Rapid Clicks**
   - Wait for each change to complete
   - Don't click multiple times quickly

2. **Regular Maintenance**
   - Clear browser cache periodically
   - Keep browser updated

3. **Monitor Console**
   - Check for JavaScript errors regularly
   - Address warnings promptly

---

*Last Updated: 2025-08-23*
*For additional support, check the main Card Design System documentation.*
