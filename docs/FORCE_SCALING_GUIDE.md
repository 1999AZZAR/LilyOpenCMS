# Force Scaling System Guide

## Overview

The Force Scaling System automatically detects browser/system zoom levels and ensures consistent page appearance across different scaling settings. It forces the page to display at 100% scale when the browser zoom is set above 100%, while preserving user preferences when zoom is 100% or less.

## How It Works

### Detection Methods

The system uses multiple methods to detect the current scaling level:

1. **Visual Viewport API** (Primary) - Most accurate method for modern browsers
2. **Device Pixel Ratio** (Fallback) - Works on older browsers
3. **CSS Transform Detection** (Fallback) - Manual calculation using DOM elements

### Scaling Logic

- **Above 100%**: Forces scaling back to 100% using CSS transforms
- **100% or less**: Keeps user's preferred scaling unchanged
- **Dynamic updates**: Monitors for changes and adjusts automatically

## Features

### Automatic Detection
- Detects browser zoom changes in real-time
- Responds to window resize events
- Handles orientation changes on mobile devices
- Monitors focus and visibility changes

### Smart Scaling
- Only applies force scaling when necessary (above 100%)
- Preserves user accessibility preferences (100% or less)
- Uses CSS transforms for smooth scaling
- Maintains proper element positioning

### Event System
- Dispatches custom events for scaling changes
- Provides debugging information
- Allows external components to react to scaling changes

## Usage

### Automatic Initialization

The system automatically initializes when the page loads. No manual setup required.

### Manual Control

```javascript
// Get current scale
const currentScale = window.forceScalingController.getCurrentScale();

// Check if scaling is forced
const isForced = window.forceScalingController.isScalingForced();

// Manually force a specific scale
window.forceScalingController.forceScale(1.5);

// Refresh detection
window.forceScalingController.refresh();
```

### Event Listening

```javascript
// Listen for scaling changes
document.addEventListener('forceScalingChanged', function(event) {
    const { action, fromScale, toScale, isForced } = event.detail;
    
    if (action === 'forced') {
        console.log('Scaling was forced from', fromScale, 'to', toScale);
    } else if (action === 'reset') {
        console.log('Scaling was reset to user preference');
    }
});
```

## CSS Classes

### Body Classes

- `.force-scaled` - Applied when force scaling is active
- `.debug-scaling` - For debugging (add manually)

### Element Exclusion

Add the class `force-scale-exclude` to elements that should not be affected by force scaling:

```html
<div class="force-scale-exclude">
    This element will not be affected by force scaling
</div>
```

## Browser Support

### Fully Supported
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### Partially Supported
- Internet Explorer 11 (fallback methods only)
- Older mobile browsers (basic functionality)

## Testing

### Test Page
Visit `/force-scaling-test` to test the functionality:

1. Change browser zoom (Ctrl/Cmd + Plus/Minus)
2. Observe the scale information updates
3. Check that content remains properly sized
4. Verify force scaling behavior

### Debug Mode
Add the `debug-scaling` class to the body element for visual debugging:

```javascript
document.body.classList.add('debug-scaling');
```

## Configuration

### Disabling Force Scaling

To disable force scaling for specific pages, add this script before the force-scaling.js:

```html
<script>
    window.DISABLE_FORCE_SCALING = true;
</script>
```

### Custom Threshold

To change the threshold (default: 100%), add this script:

```html
<script>
    window.FORCE_SCALING_THRESHOLD = 1.2; // 120%
</script>
```

## Troubleshooting

### Common Issues

1. **Content appears too small**
   - Check if force scaling is being applied unnecessarily
   - Verify the detection threshold is correct

2. **Layout breaks with scaling**
   - Ensure CSS uses relative units (rem, em, %)
   - Check for fixed positioning issues

3. **Performance issues**
   - Force scaling is optimized for performance
   - Check for conflicting CSS transforms

### Debug Information

Enable console logging to see detailed information:

```javascript
// Check current state
console.log('Current scale:', window.forceScalingController.getCurrentScale());
console.log('Is forced:', window.forceScalingController.isScalingForced());

// Monitor events
document.addEventListener('forceScalingChanged', console.log);
```

## Best Practices

### CSS Guidelines

1. **Use relative units** (rem, em, %) instead of fixed pixels
2. **Avoid fixed positioning** when possible
3. **Test with different zoom levels** during development
4. **Consider accessibility** - don't override user preferences unnecessarily

### JavaScript Guidelines

1. **Listen for scaling events** when building custom components
2. **Test with force scaling enabled and disabled**
3. **Use the provided API** instead of manual scaling calculations
4. **Handle edge cases** for older browsers

## Performance Considerations

- Force scaling uses CSS transforms for optimal performance
- Event listeners are optimized to prevent excessive updates
- ResizeObserver is used when available for efficient monitoring
- Transform origin is set to 'top left' for consistent behavior

## Accessibility

The system respects user accessibility preferences:
- Does not override zoom levels of 100% or less
- Maintains proper focus indicators
- Preserves screen reader compatibility
- Supports high contrast mode

## Future Enhancements

Potential improvements for future versions:
- User preference storage
- Custom scaling algorithms
- Better mobile device support
- Integration with CSS container queries
