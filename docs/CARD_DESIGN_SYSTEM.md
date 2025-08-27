# Card Design System

## Overview

The Card Design System allows administrators to choose from 4 different visual styles for news cards displayed on the news page (`/news`). This system provides flexibility in presenting content while maintaining consistency across the site.

## Available Card Designs

### 1. Classic (Default)
- **Style**: Traditional card layout with clean borders and subtle shadows
- **Features**: 
  - Standard rounded corners
  - Subtle hover effects with lift animation
  - Clean typography and spacing
  - Familiar design pattern for users
- **Best for**: General news websites, blogs, and content-focused sites

### 2. Modern - Refined Standard
- **Style**: Vertical card with refined modern styling
- **Features**:
  - Clean vertical layout with rounded corners
  - Rounded badges with uppercase text and letter spacing
  - Premium gradient badges for premium content
  - Smooth hover effects with lift animation
  - Professional typography with hover color transitions
- **Best for**: Modern news websites, professional layouts, and refined aesthetics

### 3. Minimal - Minimalist & Centered
- **Style**: Centered content design with larger image
- **Features**:
  - Larger image (224px height) for visual impact
  - Centered text alignment throughout
  - Rounded badges with accent colors
  - Clean, distraction-free layout
  - Smooth hover effects with subtle lift
- **Best for**: Content-focused sites, reading platforms, and minimalist designs

### 4. Featured - Elegant Horizontal
- **Style**: Compact horizontal layout with side image
- **Features**:
  - Horizontal layout with image taking 1/3 width
  - Compact content area with smaller text
  - Destructive-colored badges for news content
  - Efficient space usage
  - Smooth hover effects with lift animation
- **Best for**: Compact news feeds, space-efficient layouts, and modern interfaces

## How to Change Card Design

### Via Admin Interface

1. **Navigate to Brand Management**:
   - Go to Admin Dashboard
   - Click on "Settings" in the sidebar
   - Select "Brand Identity Management"

2. **Find the Card Design Section**:
   - Scroll down to the "News Card Design" section
   - You'll see 4 cards representing each design option

3. **Select a Design**:
   - Click the "Set as Active" button on your preferred design
   - The system will update immediately
   - You'll see a success toast notification

4. **Verify Changes**:
   - Visit the news page (`/news`) to see the new design in action
   - The changes apply to all news cards on the page

### Via API (Programmatic)

```python
from models import BrandIdentity

# Get brand identity
brand_info = BrandIdentity.query.first()

# Update card design
brand_info.card_design = 'modern'  # Options: 'classic', 'modern', 'minimal', 'featured'
db.session.commit()
```

## Technical Implementation

### Database Schema

The card design preference is stored in the `brand_identity` table:

```sql
ALTER TABLE brand_identity 
ADD COLUMN card_design VARCHAR(50) DEFAULT 'classic';
```

### Model Changes

The `BrandIdentity` model includes:

```python
class BrandIdentity(db.Model):
    # ... existing fields ...
    card_design = db.Column(db.String(50), nullable=True, default="classic")
    
    def to_dict(self):
        return {
            # ... existing fields ...
            "card_design": getattr(self, 'card_design', None) or "classic",
        }
```

### Frontend Implementation

#### CSS Classes

Each design has its own CSS class:

```css
.news-card.classic { /* Classic design styles */ }
.news-card.modern { /* Modern design styles */ }
.news-card.minimal { /* Minimal design styles */ }
.news-card.featured { /* Featured design styles */ }
```

#### JavaScript Integration

The card design is applied dynamically in `news-search.js`:

```javascript
function createNewsCard(newsItem) {
    const card = document.createElement('article');
    
    // Get card design from brand settings
    const cardDesign = window.brandInfo?.card_design || 'classic';
    card.className = `news-card ${cardDesign} bg-card rounded-lg border border-border overflow-hidden fade-in`;
    
    // ... rest of card creation
}
```

#### Template Integration

Brand info is passed to the frontend via the news template:

```html
<script>
// Pass brand info to JavaScript
window.brandInfo = {{ brand_info.to_dict() | tojson | safe }};
</script>
```

## Customization

### Adding New Card Designs

To add a new card design:

1. **Add CSS Styles** in `static/css/news.css`:
   ```css
   .news-card.your-design {
       /* Your custom styles */
   }
   ```

2. **Update the Model** to include the new option:
   ```python
   # In models.py, update the comment to include your new design
   card_design = db.Column(db.String(50), nullable=True, default="classic")  # 'classic', 'modern', 'minimal', 'featured', 'your-design'
   ```

3. **Add Admin Interface** in `templates/admin/settings/brand_management.html`:
   ```html
   <!-- Your Design Card -->
   <div class="bg-white border border-gray-200 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 p-6">
       <h3>Your Design</h3>
       <form id="form-card-your-design">
           <input type="hidden" name="card_design" value="your-design">
           <button type="submit">Set as Active</button>
       </form>
   </div>
   ```

4. **Update JavaScript** in `static/js/brand-management.js`:
   ```javascript
   // Add form handler
   handleCardDesignForm('form-card-your-design');
   ```

### Modifying Existing Designs

To modify an existing design, simply update the CSS in `static/css/news.css`. The changes will apply immediately to all cards using that design.

## Best Practices

### Design Considerations

1. **Consistency**: All designs should maintain consistent spacing and typography
2. **Accessibility**: Ensure sufficient color contrast and readable text sizes
3. **Performance**: Keep CSS animations lightweight and smooth
4. **Responsiveness**: All designs should work well on mobile devices

### Content Guidelines

1. **Image Quality**: Use high-quality images that work well with all design variants
2. **Text Length**: Keep titles and excerpts at reasonable lengths
3. **Badge Usage**: Use badges consistently across all designs

## Troubleshooting

### Common Issues

1. **Design Not Updating**:
   - Clear browser cache
   - Check if the brand_info is being passed correctly
   - Verify the card_design value in the database

2. **CSS Not Loading**:
   - Check if `news.css` is being loaded
   - Verify CSS class names match between HTML and CSS

3. **JavaScript Errors**:
   - Check browser console for errors
   - Verify `window.brandInfo` is available
   - Ensure `news-search.js` is loaded after brand info

### Debug Mode

To debug card design issues:

```javascript
// In browser console
console.log('Brand Info:', window.brandInfo);
console.log('Card Design:', window.brandInfo?.card_design);
```

## Migration Notes

### Database Migration

The card design system requires a database migration:

```bash
python migrations/add_card_design_field.py
```

### Default Values

- Existing installations will default to 'classic' design
- New installations will also default to 'classic' design
- The default can be changed by modifying the model's default value

## Future Enhancements

Potential future improvements:

1. **Per-Category Designs**: Allow different designs for different content categories
2. **User Preferences**: Let users choose their preferred card design
3. **A/B Testing**: Test different designs for engagement metrics
4. **Custom Themes**: Allow custom color schemes for each design
5. **Animation Options**: Provide different animation styles for each design

## Support

For issues or questions about the card design system:

1. Check the troubleshooting section above
2. Review the CSS and JavaScript files for errors
3. Verify database migration was successful
4. Test with different browsers and devices
