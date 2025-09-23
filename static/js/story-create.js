/**
 * Story Creation Main JavaScript
 * Handles the core functionality for creating and editing stories
 */

(function() {
    'use strict';
    
    // Global configuration
    window.STORY_CREATE_CONFIG = {
        endpoints: {
            news: '/api/news',
            images: '/api/images'
        },
        maxWaitMs: 2000,
        maxAttempts: 100
    };
    
    // Utility functions
    const Utils = {
        // Wait for DOM to be ready
        ready: function(fn) {
            if (document.readyState !== 'loading') {
                fn();
            } else {
                document.addEventListener('DOMContentLoaded', fn);
            }
        },
        
        // Get news ID from various sources
        getNewsId: function() {
            const rawId = document.getElementById('news-id')?.value || null;
            const metaEl = document.getElementById('news-meta');
            let metaId = null;
            if (metaEl && metaEl.textContent) {
                try { 
                    metaId = JSON.parse(metaEl.textContent) || null; 
                } catch (e) {}
            }
            return rawId || metaId;
        },
        
        // Set element value if element exists and value is valid
        setIf: function(el, val) { 
            if (el && val != null && String(val).length) el.value = val; 
        },
        
        // Show toast notification
        showToast: function(message, type = 'info') {
            console.log('Toast:', message, type);
            
            const toast = document.createElement('div');
            toast.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white z-50 transform transition-all duration-300 translate-x-full`;
            
            switch (type) {
                case 'error':
                    toast.classList.add('bg-red-500');
                    break;
                case 'success':
                    toast.classList.add('bg-green-500');
                    break;
                case 'warning':
                    toast.classList.add('bg-yellow-500');
                    break;
                default:
                    toast.classList.add('bg-blue-500');
            }
            
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.classList.remove('translate-x-full');
            }, 100);
            
            setTimeout(() => {
                toast.classList.add('translate-x-full');
                setTimeout(() => {
                    if (document.body.contains(toast)) {
                        document.body.removeChild(toast);
                    }
                }, 300);
            }, 3000);
        }
    };
    
    // Field mapping system
    const FieldMapper = {
        mappings: {
            'story-title': 'news-title',
            'story-category': 'news-category', 
            'story-tags': 'news-tagar',
            'story-writer': 'news-writer',
            'story-age-rating': 'news-age-rating',
            'story-external-source': 'news-external-source',
            'story-date': 'news-date',
            'story-content': 'news-content',
            'story-image-id': 'news-image-id'
        },
        
        init: function() {
            console.log('Setting up field ID mapping for user story form...');
            
            Object.entries(this.mappings).forEach(([storyId, newsId]) => {
                const storyField = document.getElementById(storyId);
                if (storyField) {
                    this.mapField(storyId, newsId, storyField);
                }
            });
            
            this.mapForm();
            console.log('Field ID mapping complete - admin JS should now work with user form');
        },
        
        mapField: function(storyId, newsId, storyField) {
            // Special handling for category and content fields
            if (storyId === 'story-category') {
                this.replaceField(storyId, newsId, storyField, 'category');
            } else if (storyId === 'story-content') {
                this.replaceField(storyId, newsId, storyField, 'content');
            } else {
                this.createHiddenField(storyId, newsId, storyField);
            }
        },
        
        replaceField: function(storyId, newsId, storyField, name) {
            const newsField = storyField.cloneNode(true);
            newsField.id = newsId;
            newsField.name = name;
            
            storyField.parentNode.replaceChild(newsField, storyField);
            
            // Update the label to point to the new field
            const label = document.querySelector(`label[for="${storyId}"]`);
            if (label) {
                label.setAttribute('for', newsId);
            }
            
            console.log(`Replaced ${storyId} with ${newsId} for ${name}`);
        },
        
        createHiddenField: function(storyId, newsId, storyField) {
            const newsField = document.createElement('input');
            newsField.type = 'hidden';
            newsField.id = newsId;
            newsField.name = storyField.name;
            newsField.value = storyField.value;
            
            storyField.parentNode.insertBefore(newsField, storyField.nextSibling);
            
            // Sync values when story field changes
            storyField.addEventListener('input', function() {
                newsField.value = this.value;
            });
            
            storyField.addEventListener('change', function() {
                newsField.value = this.value;
            });
            
            // For checkboxes, sync checked state
            if (storyField.type === 'checkbox') {
                storyField.addEventListener('change', function() {
                    newsField.value = this.checked ? 'true' : 'false';
                });
            }
            
            console.log(`Mapped ${storyId} -> ${newsId}`);
        },
        
        mapForm: function() {
            const storyForm = document.getElementById('create-story-form');
            if (storyForm) {
                storyForm.id = 'add-news-form';
                storyForm.setAttribute('novalidate', 'novalidate');
                console.log('Mapped form ID: create-story-form -> add-news-form (novalidate)');
            }
        }
    };
    
    // Data fetching and caching
    const DataManager = {
        prefetchedArticle: null,
        
        fetchArticleFast: async function(id) {
            if (this.prefetchedArticle) return this.prefetchedArticle;
            const resp = await fetchWithCSRF(`${window.STORY_CREATE_CONFIG.endpoints.news}/${id}`);
            if (!resp.ok) return null;
            const data = await resp.json();
            this.prefetchedArticle = data;
            return data;
        },
        
        waitForCategoryOptions: async function(selectId = 'news-category', maxWaitMs = 2000) {
            const start = Date.now();
            return new Promise((resolve) => {
                const tick = () => {
                    const sel = document.getElementById(selectId);
                    if (sel && sel.options && sel.options.length > 1) {
                        resolve(sel);
                        return;
                    }
                    if (Date.now() - start > maxWaitMs) {
                        resolve(sel);
                        return;
                    }
                    setTimeout(tick, 100);
                };
                tick();
            });
        }
    };
    
    // Form prefill functionality
    const FormPrefill = {
        earlyPrefill: async function() {
            const newsId = Utils.getNewsId();
            if (!newsId) return;
            
            const a = await DataManager.fetchArticleFast(newsId);
            if (!a) return;
            
            // Title: set both possible IDs to avoid waiting for mapping
            Utils.setIf(document.getElementById('news-title') || document.getElementById('story-title'), a.title || '');
            Utils.setIf(document.getElementById('news-writer') || document.getElementById('story-writer'), a.writer || '');
            Utils.setIf(document.getElementById('news-tagar') || document.getElementById('story-tags'), a.tagar || '');
            Utils.setIf(document.getElementById('news-external-source') || document.getElementById('story-external-source'), a.external_source || '');
            
            if (a.date) Utils.setIf(document.getElementById('news-date') || document.getElementById('story-date'), a.date.substring(0,10));
            if (a.age_rating) Utils.setIf(document.getElementById('news-age-rating') || document.getElementById('story-age-rating'), a.age_rating);
        },
        
        prefillEditIfNeeded: async function() {
            try {
                const newsId = Utils.getNewsId();
                if (!newsId) {
                    console.log('No newsId found - skipping prefill (create mode)');
                    return; // create mode
                }

                console.log('NewsId found - prefilling edit data:', newsId);
                const data = DataManager.prefetchedArticle || await DataManager.fetchArticleFast(newsId);
                if (!data) {
                    console.warn('No data found for newsId:', newsId);
                    return;
                }

                this.prefillBasicFields(data);
                this.prefillCategory(data);
                this.prefillImage(data);
                this.prefillContent(data);
                this.updateHeaderTexts();
            } catch (e) {
                console.warn('Prefill edit failed:', e);
            }
        },
        
        prefillBasicFields: function(data) {
            // Title (set both visible and hidden mapped fields)
            const storyTitleEl = document.getElementById('story-title');
            const newsTitleEl = document.getElementById('news-title');
            if (storyTitleEl && data.title) storyTitleEl.value = data.title;
            if (newsTitleEl && data.title) newsTitleEl.value = data.title;

            // Date (convert ISO to yyyy-mm-dd)
            const dateEl = document.getElementById('news-date');
            if (dateEl && data.date) {
                try { dateEl.value = data.date.substring(0, 10); } catch (e) {}
            }

            // Age rating
            const ageEl = document.getElementById('news-age-rating');
            if (ageEl && data.age_rating) ageEl.value = data.age_rating;

            // Writer
            const writerEl = document.getElementById('news-writer');
            if (writerEl && data.writer) writerEl.value = data.writer;

            // External source
            const extEl = document.getElementById('news-external-source');
            if (extEl && data.external_source) extEl.value = data.external_source;

            // Tags
            const tagsEl = document.getElementById('news-tagar');
            if (tagsEl && data.tagar) tagsEl.value = data.tagar;
        },
        
        prefillCategory: async function(data) {
            const categoryEl = await DataManager.waitForCategoryOptions('news-category');
            if (categoryEl && data.category_id) {
                categoryEl.value = String(data.category_id);
                const evt = new Event('change', { bubbles: true });
                categoryEl.dispatchEvent(evt);
            }
        },
        
        prefillImage: function(data) {
            const imgIdInput = document.getElementById('news-image-id');
            const preview = document.getElementById('featured-preview-create');
            const noImagePlaceholder = document.getElementById('no-image-placeholder');
            
            if (data.header_image) {
                if (imgIdInput && data.header_image.id) imgIdInput.value = data.header_image.id;
                if (preview && data.header_image.url) {
                    preview.src = data.header_image.url;
                    preview.classList.remove('hidden');
                    if (noImagePlaceholder) noImagePlaceholder.classList.add('hidden');
                }
            }
        },
        
        prefillContent: function(data) {
            const setContent = () => {
                const content = data.content || '';
                // Try SimpleMDE
                if (window.addSimplemde && window.addSimplemde.codemirror) {
                    try { window.addSimplemde.codemirror.setValue(content); return; } catch (e) {}
                } else if (window.SimpleMDE && window.SimpleMDE.instances && window.SimpleMDE.instances.length > 0) {
                    try { window.SimpleMDE.instances[0].value(content); return; } catch (e) {}
                }
                // Fallback
                const ta = document.getElementById('news-content') || document.getElementById('story-content');
                if (ta) ta.value = content;
            };
            
            if (window.addSimplemde || (window.SimpleMDE && window.SimpleMDE.instances && window.SimpleMDE.instances.length > 0)) {
                setContent();
            } else {
                setTimeout(setContent, 300);
            }
        },
        
        updateHeaderTexts: function() {
            const h1 = document.querySelector('h1.text-3xl');
            if (h1) h1.textContent = 'Edit Cerita';
            const titleBlock = document.getElementById('create-story-title');
            if (titleBlock) titleBlock.textContent = 'Edit Cerita';
        }
    };
    
    // SimpleMDE integration with enhanced content management
    const EditorManager = {
        waitForSimpleMDE: function(callback, maxAttempts = 100) {
            let attempts = 0;
            const checkInterval = setInterval(() => {
                attempts++;
                
                if (window.addSimplemde && window.addSimplemde.codemirror) {
                    clearInterval(checkInterval);
                    console.log('✅ SimpleMDE found after', attempts, 'attempts via addSimplemde.codemirror');
                    callback();
                } else if (window.addSimplemde && window.addSimplemde.simplemde && window.addSimplemde.simplemde.codemirror) {
                    clearInterval(checkInterval);
                    console.log('✅ SimpleMDE found after', attempts, 'attempts via addSimplemde.simplemde.codemirror');
                    callback();
                } else if (window.SimpleMDE && window.SimpleMDE.instances && window.SimpleMDE.instances.length > 0) {
                    clearInterval(checkInterval);
                    console.log('✅ SimpleMDE instances found after', attempts, 'attempts');
                    callback();
                } else if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    console.warn('⚠️ SimpleMDE not found after', maxAttempts, 'attempts - will use fallback methods');
                    callback();
                }
                
                if (attempts % 10 === 0) {
                    console.log(`Checking SimpleMDE... attempt ${attempts}/${maxAttempts}`);
                }
            }, 100);
        },
        
        initialize: function() {
            this.waitForSimpleMDE(() => {
                console.log('SimpleMDE is ready, initializing functionality...');
                
                // Check if we're in create mode or edit mode
                const newsId = Utils.getNewsId();
                const isCreateMode = !newsId;
                
                if (isCreateMode) {
                    console.log('Create mode detected - ensuring clean content editor');
                    // Force clear content editor in create mode
                    this.forceClearContentEditor();
                } else {
                    console.log('Edit mode detected - prefilling content');
                    FormPrefill.prefillEditIfNeeded();
                }
                
                this.testEditorAvailability();
                this.setupContentClearing();
            });
        },
        
        testEditorAvailability: function() {
            console.log('Testing editor availability...');
            
            if (window.addSimplemde && window.addSimplemde.codemirror) {
                console.log('✅ addSimplemde.codemirror available');
            } else if (window.addSimplemde && window.addSimplemde.simplemde) {
                console.log('✅ addSimplemde.simplemde available');
            } else if (window.SimpleMDE && window.SimpleMDE.instances) {
                console.log('✅ SimpleMDE.instances available:', window.SimpleMDE.instances.length);
            } else {
                console.log('⚠️ No SimpleMDE found, will use textarea fallback');
            }
            
            const textarea = document.getElementById('news-content') || document.getElementById('story-content');
            if (textarea) {
                console.log('✅ Textarea fallback available:', textarea.id);
            } else {
                console.log('❌ No textarea fallback available');
            }
        },
        
        setupContentClearing: function() {
            // Add keyboard shortcut for clearing content (Ctrl+Shift+C)
            document.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
                    e.preventDefault();
                    this.clearContentEditor();
                }
            });
            
            console.log('Content clearing shortcuts and handlers set up');
        },
        
        clearContentEditor: function(showToast = true) {
            console.log('🧹 Clearing content editor...');
            
            let cleared = false;
            
            // Try to clear SimpleMDE editor
            if (window.addSimplemde && window.addSimplemde.codemirror) {
                try {
                    window.addSimplemde.codemirror.setValue('');
                    cleared = true;
                    console.log('✅ Content cleared via addSimplemde.codemirror');
                } catch (e) {
                    console.warn('Failed to clear via addSimplemde.codemirror:', e);
                }
            } else if (window.addSimplemde && window.addSimplemde.simplemde && window.addSimplemde.simplemde.codemirror) {
                try {
                    window.addSimplemde.simplemde.codemirror.setValue('');
                    cleared = true;
                    console.log('✅ Content cleared via addSimplemde.simplemde.codemirror');
                } catch (e) {
                    console.warn('Failed to clear via addSimplemde.simplemde.codemirror:', e);
                }
            } else if (window.SimpleMDE && window.SimpleMDE.instances && window.SimpleMDE.instances.length > 0) {
                try {
                    window.SimpleMDE.instances[0].value('');
                    cleared = true;
                    console.log('✅ Content cleared via SimpleMDE.instances');
                } catch (e) {
                    console.warn('Failed to clear via SimpleMDE.instances:', e);
                }
            }
            
            // Fallback to textarea
            const textarea = document.getElementById('news-content') || document.getElementById('story-content');
            if (textarea) {
                textarea.value = '';
                cleared = true;
                console.log('✅ Content cleared via textarea fallback');
            }
            
            // Also clear any CodeMirror instances that might exist
            if (window.CodeMirror && window.CodeMirror.instances) {
                window.CodeMirror.instances.forEach((cm, index) => {
                    try {
                        cm.setValue('');
                        console.log(`✅ Content cleared via CodeMirror instance ${index}`);
                        cleared = true;
                    } catch (e) {
                        console.warn(`Failed to clear CodeMirror instance ${index}:`, e);
                    }
                });
            }
            
            if (cleared && showToast) {
                Utils.showToast('Konten editor telah dibersihkan', 'info');
            }
            
            return cleared;
        },
        
        // Aggressive content clearing for create mode
        forceClearContentEditor: function() {
            console.log('🔥 Force clearing content editor for create mode...');
            
            // Clear multiple times with different methods
            this.clearContentEditor(false);
            
            // Try again after a short delay
            setTimeout(() => {
                this.clearContentEditor(false);
            }, 100);
            
            // Try again after another delay
            setTimeout(() => {
                this.clearContentEditor(false);
            }, 500);
            
            console.log('✅ Force clear completed');
        },
        
        getContentValue: function() {
            // Try to get content from SimpleMDE editor first
            if (window.addSimplemde && window.addSimplemde.codemirror) {
                try {
                    return window.addSimplemde.codemirror.getValue() || '';
                } catch (e) {}
            } else if (window.addSimplemde && window.addSimplemde.simplemde && window.addSimplemde.simplemde.codemirror) {
                try {
                    return window.addSimplemde.simplemde.codemirror.getValue() || '';
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
        
        setContentValue: function(content) {
            console.log('📝 Setting content value:', content ? `${content.length} characters` : 'empty');
            
            // Try to set content in SimpleMDE editor first
            if (window.addSimplemde && window.addSimplemde.codemirror) {
                try {
                    window.addSimplemde.codemirror.setValue(content || '');
                    return true;
                } catch (e) {
                    console.warn('Failed to set content via addSimplemde.codemirror:', e);
                }
            } else if (window.addSimplemde && window.addSimplemde.simplemde && window.addSimplemde.simplemde.codemirror) {
                try {
                    window.addSimplemde.simplemde.codemirror.setValue(content || '');
                    return true;
                } catch (e) {
                    console.warn('Failed to set content via addSimplemde.simplemde.codemirror:', e);
                }
            } else if (window.SimpleMDE && window.SimpleMDE.instances && window.SimpleMDE.instances.length > 0) {
                try {
                    window.SimpleMDE.instances[0].value(content || '');
                    return true;
                } catch (e) {
                    console.warn('Failed to set content via SimpleMDE.instances:', e);
                }
            }
            
            // Fallback to textarea
            const textarea = document.getElementById('news-content') || document.getElementById('story-content');
            if (textarea) {
                textarea.value = content || '';
                return true;
            }
            
            return false;
        }
    };
    
    // Form context management
    const FormContext = {
        init: function() {
            const form = document.getElementById('add-news-form');
            if (form) {
                const userContextInput = document.createElement('input');
                userContextInput.type = 'hidden';
                userContextInput.name = 'user_context';
                userContextInput.value = window.CURRENT_USERNAME || '';
                form.appendChild(userContextInput);
                console.log('Added user context to form');
            }
        }
    };
    
    // Enhanced form reset and zeroing system
    const FormReset = {
        init: function() {
            this.setupResetButtons();
            this.setupKeyboardShortcuts();
            
            // Ensure clean state in create mode
            const newsId = Utils.getNewsId();
            const isCreateMode = !newsId;
            if (isCreateMode) {
                console.log('Create mode - ensuring clean form state');
                // Force clear content editor multiple times to ensure it's clean
                setTimeout(() => {
                    if (window.StoryCreateEditorManager) {
                        window.StoryCreateEditorManager.forceClearContentEditor();
                    }
                }, 1000);
            }
            
            console.log('Form reset system initialized');
        },
        
        setupResetButtons: function() {
            // Wire up manual buttons from HTML
            const clearContentBtnManual = document.getElementById('clear-content-btn-manual');
            if (clearContentBtnManual) {
                clearContentBtnManual.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.clearContentWithConfirmation();
                });
                console.log('Wired up manual clear content button');
            }
            
            const resetFormBtn = document.getElementById('reset-form-btn');
            if (resetFormBtn) {
                resetFormBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.resetFormWithConfirmation();
                });
                console.log('Wired up manual reset form button');
            }
            
            // Add clear content button to the editor toolbar if it doesn't exist (fallback)
            const toolbar = document.getElementById('custom-toolbar');
            if (toolbar && !document.getElementById('clear-content-btn') && !clearContentBtnManual) {
                const clearBtn = document.createElement('button');
                clearBtn.type = 'button';
                clearBtn.id = 'clear-content-btn';
                clearBtn.className = 'bg-card border border-border text-foreground p-2 rounded-lg hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-300';
                clearBtn.setAttribute('aria-label', 'Bersihkan konten');
                clearBtn.title = 'Bersihkan konten (Ctrl+Shift+C)';
                clearBtn.innerHTML = '<i class="fa fa-eraser" aria-hidden="true"></i>';
                
                clearBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.clearContentWithConfirmation();
                });
                
                toolbar.appendChild(clearBtn);
                console.log('Added fallback clear content button to toolbar');
            }
        },
        
        setupKeyboardShortcuts: function() {
            document.addEventListener('keydown', (e) => {
                // Ctrl+Shift+R for full form reset
                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'R') {
                    e.preventDefault();
                    this.resetFormWithConfirmation();
                }
                
                // Ctrl+Shift+N for new story (reset to create mode)
                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'N') {
                    e.preventDefault();
                    this.resetToCreateMode();
                }
            });
        },
        
        clearContentWithConfirmation: function() {
            const currentContent = EditorManager.getContentValue();
            if (!currentContent || currentContent.trim() === '') {
                Utils.showToast('Konten sudah kosong', 'info');
                return;
            }
            
            if (confirm('Apakah Anda yakin ingin menghapus semua konten? Tindakan ini tidak dapat dibatalkan.')) {
                EditorManager.clearContentEditor(true);
                // Clear any validation errors for content
                if (window.StoryFormValidation) {
                    window.StoryFormValidation.clearFieldError('content');
                }
            }
        },
        
        resetFormWithConfirmation: function() {
            if (confirm('Apakah Anda yakin ingin mereset seluruh form? Semua data yang belum disimpan akan hilang.')) {
                this.resetForm();
                Utils.showToast('Form telah direset', 'success');
            }
        },
        
        resetToCreateMode: function() {
            if (confirm('Apakah Anda yakin ingin memulai cerita baru? Semua data yang belum disimpan akan hilang.')) {
                this.resetForm();
                this.updateUIForCreateMode();
                Utils.showToast('Mode buat cerita baru diaktifkan', 'success');
            }
        },
        
        resetForm: function() {
            console.log('🔄 Resetting entire form...');
            
            // Reset all form fields
            this.resetBasicFields();
            this.resetContentEditor();
            this.resetImageSelection();
            this.resetValidation();
            this.resetStepNavigation();
            
            console.log('✅ Form reset complete');
        },
        
        resetBasicFields: function() {
            // Reset title
            const titleField = document.getElementById('news-title') || document.getElementById('story-title');
            if (titleField) titleField.value = '';
            
            // Reset category
            const categoryField = document.getElementById('news-category');
            if (categoryField) categoryField.value = '';
            
            // Reset date
            const dateField = document.getElementById('news-date');
            if (dateField) {
                // Set to today's date
                const today = new Date().toISOString().split('T')[0];
                dateField.value = today;
            }
            
            // Reset age rating
            const ageRatingField = document.getElementById('news-age-rating');
            if (ageRatingField) ageRatingField.value = '';
            
            // Reset writer (to current user)
            const writerField = document.getElementById('news-writer');
            if (writerField) writerField.value = window.CURRENT_USERNAME || '';
            
            // Reset tags
            const tagsField = document.getElementById('news-tagar');
            if (tagsField) tagsField.value = '';
            
            // Reset external source
            const externalSourceField = document.getElementById('news-external-source');
            if (externalSourceField) externalSourceField.value = '';
            
            console.log('✅ Basic fields reset');
        },
        
        resetContentEditor: function() {
            EditorManager.clearContentEditor(false);
            console.log('✅ Content editor reset');
        },
        
        resetImageSelection: function() {
            // Reset image ID
            const imageIdField = document.getElementById('news-image-id') || document.getElementById('story-image-id');
            if (imageIdField) imageIdField.value = '';
            
            // Reset image preview
            const preview = document.getElementById('featured-preview-create');
            const noImagePlaceholder = document.getElementById('no-image-placeholder');
            
            if (preview) {
                preview.src = '';
                preview.classList.add('hidden');
            }
            
            if (noImagePlaceholder) {
                noImagePlaceholder.classList.remove('hidden');
            }
            
            console.log('✅ Image selection reset');
        },
        
        resetValidation: function() {
            if (window.StoryFormValidation) {
                window.StoryFormValidation.clearAllErrors();
            }
            console.log('✅ Validation reset');
        },
        
        resetStepNavigation: function() {
            if (window.StoryStepNavigation) {
                window.StoryStepNavigation.goToStep(1);
            }
            console.log('✅ Step navigation reset to step 1');
        },
        
        updateUIForCreateMode: function() {
            // Update page title and headers
            const h1 = document.querySelector('h1.text-3xl');
            if (h1) h1.textContent = 'Tulis Cerita Baru';
            
            const titleBlock = document.getElementById('create-story-title');
            if (titleBlock) titleBlock.textContent = 'Buat Cerita';
            
            // Update page title
            document.title = 'Tulis Cerita Baru';
            
            // Clear news ID if in edit mode
            const newsIdField = document.getElementById('news-id');
            if (newsIdField) newsIdField.value = '';
            
            console.log('✅ UI updated for create mode');
        },
        
        // Public API
        clearContent: function() {
            this.clearContentWithConfirmation();
        },
        
        resetToNew: function() {
            this.resetToCreateMode();
        },
        
        resetAll: function() {
            this.resetFormWithConfirmation();
        }
    };
    
    // Ultra-early title prefill (only for edit mode)
    (function() {
        try {
            const metaEl = document.getElementById('news-meta');
            if (!metaEl || !metaEl.textContent) {
                console.log('No news-meta found - create mode detected');
                return;
            }
            const id = JSON.parse(metaEl.textContent);
            if (!id) {
                console.log('No newsId in meta - create mode detected');
                return;
            }
            console.log('NewsId found in meta - edit mode detected:', id);
            fetchWithCSRF(`/api/news/${id}`).then(r => r.ok ? r.json() : null).then(a => {
                if (!a) return;
                const setIf = (el, val) => { if (el && val != null && String(val).length) el.value = val; };
                const visibleTitle = document.getElementById('story-title') || document.getElementById('news-title');
                setIf(visibleTitle, a.title || '');
                const hiddenTitle = document.getElementById('news-title');
                if (hiddenTitle && hiddenTitle !== visibleTitle) setIf(hiddenTitle, a.title || '');
                const h1 = document.querySelector('h1.text-3xl'); if (h1) h1.textContent = 'Edit Cerita';
                const t2 = document.getElementById('create-story-title'); if (t2) t2.textContent = 'Edit Cerita';
            }).catch(()=>{});
        } catch(e) {
            console.log('Ultra-early prefill failed - likely create mode:', e);
        }
    })();
    
    // Initialize everything when DOM is ready
    Utils.ready(function() {
        console.log('Initializing story creation system...');
        
        // Check mode first
        const newsId = Utils.getNewsId();
        const isCreateMode = !newsId;
        console.log('Mode detected:', isCreateMode ? 'CREATE' : 'EDIT', 'newsId:', newsId);
        
        // Initialize field mapping
        FieldMapper.init();
        
        // Initialize form context
        FormContext.init();
        
        // Initialize editor
        EditorManager.initialize();
        
        // Initialize form reset system
        FormReset.init();
        
        // Early prefill (only for edit mode)
        if (!isCreateMode) {
            FormPrefill.earlyPrefill();
        } else {
            console.log('Create mode - skipping early prefill');
            // Ensure content is clean in create mode with force clear
            setTimeout(() => {
                if (window.StoryCreateEditorManager) {
                    window.StoryCreateEditorManager.forceClearContentEditor();
                }
            }, 500);
        }
        
        console.log('Story creation system initialized');
    });
    
    // Export utilities for other modules
    window.StoryCreateUtils = Utils;
    window.StoryCreateDataManager = DataManager;
    window.StoryCreateFormPrefill = FormPrefill;
    window.StoryCreateEditorManager = EditorManager;
    window.StoryCreateFormReset = FormReset;
    
})();
