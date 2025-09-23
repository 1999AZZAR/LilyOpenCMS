/**
 * Story Creation Form Validation
 * Handles form validation, error handling, and user feedback
 */

(function() {
    'use strict';
    
    const FormValidation = {
        rules: {
            title: {
                required: true,
                minLength: 1,
                maxLength: 200,
                message: 'Judul artikel harus diisi'
            },
            category: {
                required: true,
                message: 'Kategori harus dipilih'
            },
            date: {
                required: true,
                message: 'Tanggal publikasi harus diisi'
            },
            ageRating: {
                required: true,
                message: 'Rating usia konten harus dipilih'
            },
            writer: {
                required: false,
                maxLength: 100,
                message: 'Nama penulis terlalu panjang'
            },
            tags: {
                required: false,
                maxLength: 500,
                message: 'Tag terlalu panjang'
            },
            externalSource: {
                required: false,
                pattern: /^https?:\/\/.+/,
                message: 'URL sumber eksternal tidak valid'
            },
            content: {
                required: true,
                minLength: 10,
                message: 'Konten cerita harus diisi minimal 10 karakter'
            }
        },
        
        errors: [],
        
        init: function() {
            console.log('Initializing form validation...');
            
            this.setupValidationListeners();
            this.setupFormSubmission();
            
            console.log('Form validation initialized');
        },
        
        setupValidationListeners: function() {
            // Real-time validation for key fields
            const titleField = document.getElementById('news-title') || document.getElementById('story-title');
            if (titleField) {
                titleField.addEventListener('blur', () => this.validateField('title', titleField.value));
                titleField.addEventListener('input', () => this.clearFieldError('title'));
            }
            
            const categoryField = document.getElementById('news-category');
            if (categoryField) {
                categoryField.addEventListener('change', () => this.validateField('category', categoryField.value));
            }
            
            const dateField = document.getElementById('news-date');
            if (dateField) {
                dateField.addEventListener('change', () => this.validateField('date', dateField.value));
            }
            
            const ageRatingField = document.getElementById('news-age-rating');
            if (ageRatingField) {
                ageRatingField.addEventListener('change', () => this.validateField('ageRating', ageRatingField.value));
            }
            
            const contentField = document.getElementById('news-content') || document.getElementById('story-content');
            if (contentField) {
                contentField.addEventListener('blur', () => this.validateField('content', contentField.value));
                contentField.addEventListener('input', () => this.clearFieldError('content'));
            }
            
            const writerField = document.getElementById('news-writer');
            if (writerField) {
                writerField.addEventListener('blur', () => this.validateField('writer', writerField.value));
                writerField.addEventListener('input', () => this.clearFieldError('writer'));
            }
            
            const tagsField = document.getElementById('news-tagar');
            if (tagsField) {
                tagsField.addEventListener('blur', () => this.validateField('tags', tagsField.value));
                tagsField.addEventListener('input', () => this.clearFieldError('tags'));
            }
            
            const externalSourceField = document.getElementById('news-external-source');
            if (externalSourceField) {
                externalSourceField.addEventListener('blur', () => this.validateField('externalSource', externalSourceField.value));
                externalSourceField.addEventListener('input', () => this.clearFieldError('externalSource'));
            }
        },
        
        setupFormSubmission: function() {
            const form = document.getElementById('add-news-form') || document.getElementById('create-story-form');
            if (form) {
                form.addEventListener('submit', (e) => {
                    if (!this.validateForm()) {
                        e.preventDefault();
                        this.showFormErrors();
                        return false;
                    }
                });
            }
        },
        
        validateForm: function() {
            console.log('Validating entire form...');
            this.errors = [];
            
            // Get all field values
            const formData = this.getFormData();
            
            // Validate each field
            Object.keys(this.rules).forEach(fieldName => {
                const value = formData[fieldName];
                this.validateField(fieldName, value);
            });
            
            const isValid = this.errors.length === 0;
            console.log('Form validation result:', isValid ? 'Valid' : 'Invalid', this.errors);
            
            return isValid;
        },
        
        getFormData: function() {
            return {
                title: (document.getElementById('news-title') || document.getElementById('story-title'))?.value?.trim() || '',
                category: document.getElementById('news-category')?.value || '',
                date: document.getElementById('news-date')?.value || '',
                ageRating: document.getElementById('news-age-rating')?.value || '',
                writer: document.getElementById('news-writer')?.value?.trim() || '',
                tags: document.getElementById('news-tagar')?.value?.trim() || '',
                externalSource: document.getElementById('news-external-source')?.value?.trim() || '',
                content: this.getContentValue()
            };
        },
        
        getContentValue: function() {
            // Use the centralized content getter from EditorManager if available
            if (window.StoryCreateEditorManager && window.StoryCreateEditorManager.getContentValue) {
                return window.StoryCreateEditorManager.getContentValue();
            }
            
            // Fallback to direct SimpleMDE access
            if (window.addSimplemde && window.addSimplemde.codemirror) {
                try {
                    return window.addSimplemde.codemirror.getValue() || '';
                } catch (e) {}
            } else if (window.SimpleMDE && window.SimpleMDE.instances && window.SimpleMDE.instances.length > 0) {
                try {
                    return window.SimpleMDE.instances[0].value() || '';
                } catch (e) {}
            }
            
            // Fallback to textarea
            const textarea = document.getElementById('news-content') || document.getElementById('story-content');
            return textarea?.value?.trim() || '';
        },
        
        validateField: function(fieldName, value) {
            const rule = this.rules[fieldName];
            if (!rule) return true;
            
            let isValid = true;
            let errorMessage = '';
            
            // Required validation
            if (rule.required && (!value || value.trim() === '')) {
                isValid = false;
                errorMessage = rule.message;
            }
            
            // Length validations
            if (isValid && value) {
                if (rule.minLength && value.length < rule.minLength) {
                    isValid = false;
                    errorMessage = `${rule.message} (minimal ${rule.minLength} karakter)`;
                }
                
                if (rule.maxLength && value.length > rule.maxLength) {
                    isValid = false;
                    errorMessage = `${rule.message} (maksimal ${rule.maxLength} karakter)`;
                }
            }
            
            // Pattern validation
            if (isValid && value && rule.pattern && !rule.pattern.test(value)) {
                isValid = false;
                errorMessage = rule.message;
            }
            
            // Date validation
            if (isValid && fieldName === 'date' && value) {
                const date = new Date(value);
                const today = new Date();
                if (date > today) {
                    isValid = false;
                    errorMessage = 'Tanggal publikasi tidak boleh di masa depan';
                }
            }
            
            // Update errors array
            if (!isValid) {
                this.addError(fieldName, errorMessage);
            } else {
                this.removeError(fieldName);
            }
            
            // Update UI
            this.updateFieldUI(fieldName, isValid, errorMessage);
            
            return isValid;
        },
        
        addError: function(fieldName, message) {
            const existingErrorIndex = this.errors.findIndex(error => error.field === fieldName);
            if (existingErrorIndex >= 0) {
                this.errors[existingErrorIndex].message = message;
            } else {
                this.errors.push({ field: fieldName, message: message });
            }
        },
        
        removeError: function(fieldName) {
            this.errors = this.errors.filter(error => error.field !== fieldName);
        },
        
        updateFieldUI: function(fieldName, isValid, errorMessage) {
            const field = this.getFieldElement(fieldName);
            if (!field) return;
            
            const fieldContainer = field.closest('.mb-4, .mb-6, div') || field.parentElement;
            
            // Remove existing error styling
            field.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
            field.classList.add('border-border', 'focus:border-primary', 'focus:ring-primary');
            
            // Remove existing error message
            const existingError = fieldContainer.querySelector('.field-error');
            if (existingError) {
                existingError.remove();
            }
            
            if (!isValid) {
                // Add error styling
                field.classList.remove('border-border', 'focus:border-primary', 'focus:ring-primary');
                field.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
                
                // Add error message
                const errorElement = document.createElement('p');
                errorElement.className = 'field-error text-red-500 text-xs mt-1';
                errorElement.textContent = errorMessage;
                fieldContainer.appendChild(errorElement);
            }
        },
        
        getFieldElement: function(fieldName) {
            const fieldMap = {
                title: document.getElementById('news-title') || document.getElementById('story-title'),
                category: document.getElementById('news-category'),
                date: document.getElementById('news-date'),
                ageRating: document.getElementById('news-age-rating'),
                writer: document.getElementById('news-writer'),
                tags: document.getElementById('news-tagar'),
                externalSource: document.getElementById('news-external-source'),
                content: document.getElementById('news-content') || document.getElementById('story-content')
            };
            
            return fieldMap[fieldName];
        },
        
        clearFieldError: function(fieldName) {
            this.removeError(fieldName);
            this.updateFieldUI(fieldName, true, '');
        },
        
        showFormErrors: function() {
            if (this.errors.length === 0) return;
            
            // Show first error as toast
            const firstError = this.errors[0];
            this.showErrorToast(firstError.message);
            
            // Focus on first error field
            const field = this.getFieldElement(firstError.field);
            if (field) {
                field.focus();
                field.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            
            // Log all errors
            console.log('Form validation errors:', this.errors);
        },
        
        showErrorToast: function(message) {
            if (window.StoryCreateUtils && window.StoryCreateUtils.showToast) {
                window.StoryCreateUtils.showToast(message, 'error');
            } else {
                alert(message);
            }
        },
        
        // Public API
        validateStep: function(stepNumber) {
            if (stepNumber === 1) {
                return this.validateStep1();
            } else if (stepNumber === 2) {
                return this.validateStep2();
            }
            return true;
        },
        
        validateStep1: function() {
            const formData = this.getFormData();
            let isValid = true;
            
            // Validate required fields for step 1
            const requiredFields = ['title', 'category', 'date', 'ageRating'];
            
            requiredFields.forEach(fieldName => {
                if (!this.validateField(fieldName, formData[fieldName])) {
                    isValid = false;
                }
            });
            
            return isValid;
        },
        
        validateStep2: function() {
            const formData = this.getFormData();
            return this.validateField('content', formData.content);
        },
        
        getErrors: function() {
            return this.errors;
        },
        
        clearAllErrors: function() {
            this.errors = [];
            Object.keys(this.rules).forEach(fieldName => {
                this.updateFieldUI(fieldName, true, '');
            });
        },
        
        // Enhanced content validation with better feedback
        validateContentWithFeedback: function() {
            const content = this.getContentValue();
            const isValid = this.validateField('content', content);
            
            if (!isValid) {
                // Show specific feedback for content validation
                const error = this.errors.find(e => e.field === 'content');
                if (error) {
                    this.showErrorToast(error.message);
                }
            }
            
            return isValid;
        },
        
        // Check if content has meaningful content (not just whitespace)
        hasMeaningfulContent: function() {
            const content = this.getContentValue();
            if (!content) return false;
            
            // Remove markdown formatting and check for actual text
            const plainText = content
                .replace(/#{1,6}\s+/g, '') // Remove headers
                .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
                .replace(/\*(.*?)\*/g, '$1') // Remove italic
                .replace(/`(.*?)`/g, '$1') // Remove inline code
                .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links
                .replace(/!\[([^\]]*)\]\([^)]+\)/g, '') // Remove images
                .replace(/^\s*[-*+]\s+/gm, '') // Remove list markers
                .replace(/^\s*\d+\.\s+/gm, '') // Remove numbered list markers
                .replace(/^\s*>\s+/gm, '') // Remove blockquotes
                .trim();
            
            return plainText.length >= 10;
        },
        
        // Enhanced content validation that considers meaningful content
        validateContentMeaningful: function() {
            if (!this.hasMeaningfulContent()) {
                this.addError('content', 'Konten harus memiliki setidaknya 10 karakter teks yang bermakna');
                this.updateFieldUI('content', false, 'Konten harus memiliki setidaknya 10 karakter teks yang bermakna');
                return false;
            }
            
            this.removeError('content');
            this.updateFieldUI('content', true, '');
            return true;
        }
    };
    
    // Initialize when DOM is ready
    function init() {
        if (document.readyState !== 'loading') {
            FormValidation.init();
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                FormValidation.init();
            });
        }
    }
    
    // Export for global access
    window.StoryFormValidation = FormValidation;
    
    // Auto-initialize
    init();
    
})();
