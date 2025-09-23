/**
 * Story Creation Step Navigation
 * Handles the multi-step form navigation and validation
 */

(function() {
    'use strict';
    
    const StepNavigation = {
        currentStep: 1,
        elements: {
            step1Content: null,
            step2Content: null,
            step1Indicator: null,
            step2Indicator: null,
            nextStepBtn: null,
            prevStepBtn: null,
            cancelBtn: null
        },
        
        init: function() {
            console.log('Setting up step navigation...');
            
            this.cacheElements();
            this.setupEventListeners();
            this.setupKeyboardShortcuts();
            
            console.log('Step navigation setup complete!');
        },
        
        cacheElements: function() {
            this.elements.step1Content = document.getElementById('step-1-content');
            this.elements.step2Content = document.getElementById('step-2-content');
            this.elements.step1Indicator = document.getElementById('step-1-indicator');
            this.elements.step2Indicator = document.getElementById('step-2-indicator');
            this.elements.nextStepBtn = document.getElementById('next-step-btn');
            this.elements.prevStepBtn = document.getElementById('prev-step-btn');
            this.elements.cancelBtn = document.getElementById('cancel-edit-btn');
            
            console.log('Step elements found:', {
                step1Content: !!this.elements.step1Content,
                step2Content: !!this.elements.step2Content,
                step1Indicator: !!this.elements.step1Indicator,
                step2Indicator: !!this.elements.step2Indicator,
                nextStepBtn: !!this.elements.nextStepBtn,
                prevStepBtn: !!this.elements.prevStepBtn,
                cancelBtn: !!this.elements.cancelBtn
            });
        },
        
        setupEventListeners: function() {
            // Next step button
            if (this.elements.nextStepBtn) {
                console.log('Adding click listener to next step button');
                this.elements.nextStepBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('Next step button clicked');
                    this.showStep2();
                });
            } else {
                console.error('Next step button not found!');
            }
            
            // Previous step button
            if (this.elements.prevStepBtn) {
                console.log('Adding click listener to prev step button');
                this.elements.prevStepBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('Prev step button clicked');
                    this.showStep1();
                });
            } else {
                console.error('Prev step button not found!');
            }
            
            // Cancel button
            if (this.elements.cancelBtn) {
                console.log('Adding click listener to cancel button');
                this.elements.cancelBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleCancel();
                });
            } else {
                console.error('Cancel button not found!');
            }
            
            // Clear content and go back button
            const clearContentAndBackBtn = document.getElementById('clear-content-and-back-btn');
            if (clearContentAndBackBtn) {
                console.log('Adding click listener to clear content and back button');
                clearContentAndBackBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.clearContentAndGoToStep1();
                });
            } else {
                console.warn('Clear content and back button not found!');
            }
        },
        
        setupKeyboardShortcuts: function() {
            document.addEventListener('keydown', (e) => {
                // Ctrl/Cmd + Enter to go to next step (from details to content)
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    if (this.elements.step1Content && !this.elements.step1Content.classList.contains('hidden')) {
                        e.preventDefault();
                        this.showStep2();
                    }
                }
            });
        },
        
        showStep1: function() {
            console.log('Showing Step 1 (Details)');
            this.currentStep = 1;
            
            // Show/hide content
            if (this.elements.step1Content) this.elements.step1Content.classList.remove('hidden');
            if (this.elements.step2Content) this.elements.step2Content.classList.add('hidden');
            
            // Update indicators
            this.updateIndicators(1);
            
            // Update labels
            this.updateStepLabels(1);
            
            // Clear any validation errors when going back to step 1
            if (window.StoryFormValidation) {
                window.StoryFormValidation.clearAllErrors();
            }
        },
        
        showStep2: function() {
            console.log('Showing Step 2 (Content)');
            
            // Validate required fields in step 1
            if (!this.validateStep1()) {
                return;
            }
            
            this.currentStep = 2;
            
            // Show/hide content
            if (this.elements.step1Content) this.elements.step1Content.classList.add('hidden');
            if (this.elements.step2Content) this.elements.step2Content.classList.remove('hidden');
            
            // Update indicators
            this.updateIndicators(2);
            
            // Update labels
            this.updateStepLabels(2);
        },
        
        validateStep1: function() {
            const titleInput = document.getElementById('news-title');
            const categoryInput = document.getElementById('news-category');
            const dateInput = document.getElementById('news-date');
            const ageRatingInput = document.getElementById('news-age-rating');
            
            const title = titleInput ? titleInput.value.trim() : '';
            const category = categoryInput ? categoryInput.value : '';
            const date = dateInput ? dateInput.value : '';
            const ageRating = ageRatingInput ? ageRatingInput.value : '';
            
            console.log('Validation check:', { 
                title: title, 
                category: category,
                date: date,
                ageRating: ageRating
            });
            
            if (!title) {
                this.showValidationError('Judul artikel harus diisi', titleInput);
                return false;
            }
            
            if (!category) {
                this.showValidationError('Kategori harus dipilih', categoryInput);
                return false;
            }
            
            if (!date) {
                this.showValidationError('Tanggal publikasi harus diisi', dateInput);
                return false;
            }
            
            if (!ageRating) {
                this.showValidationError('Rating usia konten harus dipilih', ageRatingInput);
                return false;
            }
            
            return true;
        },
        
        showValidationError: function(message, inputElement) {
            // Use the toast function from the main module if available
            if (window.StoryCreateUtils && window.StoryCreateUtils.showToast) {
                window.StoryCreateUtils.showToast(message, 'error');
            } else {
                // Fallback to alert
                alert(message);
            }
            
            if (inputElement) {
                inputElement.focus();
            }
        },
        
        updateIndicators: function(activeStep) {
            if (activeStep === 1) {
                if (this.elements.step1Indicator) {
                    this.elements.step1Indicator.classList.remove('bg-muted', 'text-muted-foreground');
                    this.elements.step1Indicator.classList.add('bg-primary', 'text-primary-foreground');
                }
                
                if (this.elements.step2Indicator) {
                    this.elements.step2Indicator.classList.remove('bg-primary', 'text-primary-foreground');
                    this.elements.step2Indicator.classList.add('bg-muted', 'text-muted-foreground');
                }
            } else if (activeStep === 2) {
                if (this.elements.step1Indicator) {
                    this.elements.step1Indicator.classList.remove('bg-primary', 'text-primary-foreground');
                    this.elements.step1Indicator.classList.add('bg-muted', 'text-muted-foreground');
                }
                
                if (this.elements.step2Indicator) {
                    this.elements.step2Indicator.classList.remove('bg-muted', 'text-muted-foreground');
                    this.elements.step2Indicator.classList.add('bg-primary', 'text-primary-foreground');
                }
            }
        },
        
        updateStepLabels: function(activeStep) {
            const step1Label = document.querySelector('#step-1-indicator + span');
            const step2Label = document.querySelector('#step-2-indicator + span');
            
            if (activeStep === 1) {
                if (step1Label) {
                    step1Label.classList.remove('text-muted-foreground');
                    step1Label.classList.add('text-foreground');
                }
                
                if (step2Label) {
                    step2Label.classList.remove('text-foreground');
                    step2Label.classList.add('text-muted-foreground');
                }
            } else if (activeStep === 2) {
                if (step1Label) {
                    step1Label.classList.remove('text-foreground');
                    step1Label.classList.add('text-muted-foreground');
                }
                
                if (step2Label) {
                    step2Label.classList.remove('text-muted-foreground');
                    step2Label.classList.add('text-foreground');
                }
            }
        },
        
        handleCancel: function() {
            const fallbackUrl = window.location.origin + '/user/stories';
            
            // Prefer going back if there is a referrer, otherwise go to user stories
            if (document.referrer && document.referrer !== window.location.href) {
                try { 
                    window.history.back(); 
                    return; 
                } catch (_) {}
            }
            
            window.location.href = fallbackUrl;
        },
        
        clearContentAndGoToStep1: function() {
            if (confirm('Apakah Anda yakin ingin menghapus konten dan kembali ke detail? Konten yang belum disimpan akan hilang.')) {
                // Clear content editor
                if (window.StoryCreateEditorManager) {
                    window.StoryCreateEditorManager.clearContentEditor(false);
                }
                
                // Clear content validation errors
                if (window.StoryFormValidation) {
                    window.StoryFormValidation.clearFieldError('content');
                }
                
                // Go to step 1
                this.showStep1();
                
                // Show feedback
                if (window.StoryCreateUtils && window.StoryCreateUtils.showToast) {
                    window.StoryCreateUtils.showToast('Konten telah dihapus dan kembali ke detail', 'info');
                }
            }
        },
        
        // Public API
        goToStep: function(stepNumber) {
            if (stepNumber === 1) {
                this.showStep1();
            } else if (stepNumber === 2) {
                this.showStep2();
            }
        },
        
        getCurrentStep: function() {
            return this.currentStep;
        },
        
        isStepValid: function(stepNumber) {
            if (stepNumber === 1) {
                return this.validateStep1();
            }
            return true; // Step 2 doesn't have validation yet
        }
    };
    
    // Initialize when DOM is ready
    function init() {
        if (document.readyState !== 'loading') {
            StepNavigation.init();
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                StepNavigation.init();
            });
        }
    }
    
    // Export for global access
    window.StoryStepNavigation = StepNavigation;
    
    // Auto-initialize
    init();
    
})();
