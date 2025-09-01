/**
 * Force Scaling Controller
 * Detects browser/system scaling and forces it to 100% if above 100%
 * Keeps user's preferred scaling if it's 100% or less
 */

class ForceScalingController {
    constructor() {
        this.currentScale = 1;
        this.targetScale = 1;
        this.isForced = false;
        this.originalTransform = '';
        this.originalZoom = '';
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.start());
        } else {
            this.start();
        }
    }
    
    start() {
        this.detectCurrentScale();
        this.applyScaling();
        this.setupEventListeners();
        this.setupResizeObserver();
    }
    
    detectCurrentScale() {
        // Method 1: Check zoom level using visualViewport API (most accurate)
        if (window.visualViewport) {
            this.currentScale = window.visualViewport.scale;
        }
        // Method 2: Check devicePixelRatio (fallback)
        else if (window.devicePixelRatio) {
            this.currentScale = window.devicePixelRatio;
        }
        // Method 3: Check zoom using CSS transform (fallback)
        else {
            this.currentScale = this.getZoomFromTransform();
        }
        
        console.log('Force Scaling: Detected scale:', this.currentScale);
    }
    
    getZoomFromTransform() {
        // Try to detect zoom from CSS transform
        const testElement = document.createElement('div');
        testElement.style.position = 'absolute';
        testElement.style.top = '0';
        testElement.style.left = '0';
        testElement.style.width = '100px';
        testElement.style.height = '100px';
        testElement.style.visibility = 'hidden';
        document.body.appendChild(testElement);
        
        const rect = testElement.getBoundingClientRect();
        const scale = rect.width / 100;
        
        document.body.removeChild(testElement);
        return scale;
    }
    
    applyScaling() {
        // Only force scaling if current scale is above 100%
        if (this.currentScale > 1.0) {
            this.forceScaleTo100();
        } else {
            this.resetToUserScale();
        }
    }
    
    forceScaleTo100() {
        if (this.isForced) return; // Already applied
        
        console.log('Force Scaling: Forcing scale to 100% (current:', this.currentScale, ')');
        
        // Store original values
        this.originalTransform = document.body.style.transform;
        this.originalZoom = document.body.style.zoom;
        
        // Calculate the scale factor needed to bring it back to 100%
        this.targetScale = 1 / this.currentScale;
        
        // Apply scaling using CSS transform
        document.body.style.transform = `scale(${this.targetScale})`;
        document.body.style.transformOrigin = 'top left';
        document.body.style.width = `${100 / this.targetScale}%`;
        document.body.style.height = `${100 / this.targetScale}%`;
        
        // Also try zoom as fallback for older browsers
        if (this.targetScale !== 1) {
            document.body.style.zoom = this.targetScale;
        }
        
        this.isForced = true;
        
        // Add a class to body for CSS targeting
        document.body.classList.add('force-scaled');
        
        // Dispatch custom event
        this.dispatchScalingEvent('forced', this.currentScale, this.targetScale);
    }
    
    resetToUserScale() {
        if (!this.isForced) return; // Not currently forced
        
        console.log('Force Scaling: Resetting to user scale (current:', this.currentScale, ')');
        
        // Restore original values
        document.body.style.transform = this.originalTransform;
        document.body.style.zoom = this.originalZoom;
        document.body.style.width = '';
        document.body.style.height = '';
        document.body.style.transformOrigin = '';
        
        this.isForced = false;
        this.targetScale = 1;
        
        // Remove class
        document.body.classList.remove('force-scaled');
        
        // Dispatch custom event
        this.dispatchScalingEvent('reset', this.currentScale, 1);
    }
    
    setupEventListeners() {
        // Listen for zoom changes
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', () => {
                this.handleScaleChange();
            });
        }
        
        // Listen for window resize (fallback)
        window.addEventListener('resize', () => {
            setTimeout(() => this.handleScaleChange(), 100);
        });
        
        // Listen for orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.handleScaleChange(), 500);
        });
        
        // Listen for focus events (user might have changed zoom)
        window.addEventListener('focus', () => {
            setTimeout(() => this.handleScaleChange(), 100);
        });
        
        // Listen for visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                setTimeout(() => this.handleScaleChange(), 100);
            }
        });
    }
    
    setupResizeObserver() {
        // Use ResizeObserver to detect size changes
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver(() => {
                this.handleScaleChange();
            });
            
            resizeObserver.observe(document.body);
        }
    }
    
    handleScaleChange() {
        const previousScale = this.currentScale;
        this.detectCurrentScale();
        
        // Only apply changes if scale actually changed
        if (Math.abs(this.currentScale - previousScale) > 0.01) {
            console.log('Force Scaling: Scale changed from', previousScale, 'to', this.currentScale);
            this.applyScaling();
        }
    }
    
    dispatchScalingEvent(action, fromScale, toScale) {
        const event = new CustomEvent('forceScalingChanged', {
            detail: {
                action: action,
                fromScale: fromScale,
                toScale: toScale,
                isForced: this.isForced,
                timestamp: Date.now()
            }
        });
        
        document.dispatchEvent(event);
    }
    
    // Public methods for external control
    getCurrentScale() {
        return this.currentScale;
    }
    
    isScalingForced() {
        return this.isForced;
    }
    
    forceScale(scale) {
        if (scale <= 1.0) {
            this.resetToUserScale();
        } else {
            this.currentScale = scale;
            this.forceScaleTo100();
        }
    }
    
    // Method to manually refresh scaling detection
    refresh() {
        this.handleScaleChange();
    }
}

// Initialize the scaling controller
let forceScalingController;

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        forceScalingController = new ForceScalingController();
    });
} else {
    forceScalingController = new ForceScalingController();
}

// Make it globally available
window.ForceScalingController = ForceScalingController;
window.forceScalingController = forceScalingController;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ForceScalingController;
}
