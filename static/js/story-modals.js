/**
 * Story Creation Modal Management
 * Handles opening/closing of modals and link insert interactions
 */

(function() {
  'use strict';

  const Modals = {
    init: function() {
      this.bindLinkModal();
      this.bindImageInsertModalClose();
      this.bindHeaderModalButtons();
    },

    // Link insert modal handlers
    openLinkInsertModal: function() {
      console.log('🔗 openLinkInsertModal called');
      const modal = document.getElementById('link-insert-modal');
      if (!modal) {
        console.error('❌ Link modal not found');
        return;
      }
      modal.classList.remove('hidden');
      const linkTextInput = document.getElementById('link-text');
      if (linkTextInput) linkTextInput.focus();
    },

    insertLink: function() {
      console.log('🔗 insertLink called');
      const linkText = document.getElementById('link-text')?.value.trim();
      const linkUrl = document.getElementById('link-url')?.value.trim();
      if (!linkUrl) {
        Modals.toast('URL harus diisi', 'error');
        return;
      }

      // Try to insert into SimpleMDE
      let cm = null;
      if (window.addSimplemde && window.addSimplemde.codemirror) {
        cm = window.addSimplemde.codemirror;
      } else if (window.SimpleMDE && window.SimpleMDE.instances && window.SimpleMDE.instances.length > 0) {
        cm = window.SimpleMDE.instances[0].codemirror;
      }

      if (cm) {
        const markdown = linkText ? `[${linkText}](${linkUrl})` : `[${linkUrl}](${linkUrl})`;
        cm.replaceSelection(markdown);
      } else {
        console.warn('SimpleMDE not available, cannot insert link');
      }

      // Close and clear
      const modal = document.getElementById('link-insert-modal');
      if (modal) modal.classList.add('hidden');
      const lt = document.getElementById('link-text'); if (lt) lt.value = '';
      const lu = document.getElementById('link-url'); if (lu) lu.value = '';
    },

    // Header image modal handlers
    openImageHeaderModalCreate: function() {
      console.log('Opening featured image modal...');
      const modal = document.getElementById('image-header-modal-create');
      if (!modal) return;
      modal.classList.remove('hidden');
      setTimeout(() => {
        if (window.loadAndDisplayHeaderImages) {
          window.loadAndDisplayHeaderImages(1);
        } else if (window.loadHeaderLibraryCreate) {
          window.loadHeaderLibraryCreate(1);
        }
      }, 100);
    },

    closeImageHeaderModalCreate: function() {
      console.log('Closing featured image modal...');
      const modal = document.getElementById('image-header-modal-create');
      if (modal) modal.classList.add('hidden');
    },

    // Helpers
    bindLinkModal: function() {
      window.openLinkInsertModal = Modals.openLinkInsertModal;
      window.insertLink = Modals.insertLink;

      const insertLinkBtn = document.getElementById('insert-link-btn');
      const cancelLinkBtn = document.getElementById('cancel-link-btn');

      if (insertLinkBtn) insertLinkBtn.addEventListener('click', Modals.insertLink);
      if (cancelLinkBtn) cancelLinkBtn.addEventListener('click', function() {
        const modal = document.getElementById('link-insert-modal');
        if (modal) modal.classList.add('hidden');
        console.log('🔗 Link modal closed via cancel button');
      });
    },

    bindImageInsertModalClose: function() {
      const closeImageInsertBtn = document.getElementById('close-image-insert-create');
      if (closeImageInsertBtn) {
        closeImageInsertBtn.addEventListener('click', function() {
          const modal = document.getElementById('image-insert-modal-create');
          if (modal) modal.classList.add('hidden');
          console.log('🖼️ Image insert modal closed');
        });
      }
    },

    bindHeaderModalButtons: function() {
      // Wire global functions
      window.openImageHeaderModalCreate = Modals.openImageHeaderModalCreate;
      window.closeImageHeaderModalCreate = Modals.closeImageHeaderModalCreate;

      // Open button (if present)
      const openBtn = document.getElementById('open-header-modal-btn');
      if (openBtn) {
        openBtn.addEventListener('click', function(e) {
          e.preventDefault();
          Modals.openImageHeaderModalCreate();
        });
      }

      // Close button inside modal may already have onclick in template, this is a safety binding
      const closeBtn = document.getElementById('header-image-close-create');
      if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
          e.preventDefault();
          Modals.closeImageHeaderModalCreate();
        });
      }
    },

    toast: function(message, type) {
      if (window.StoryCreateUtils && window.StoryCreateUtils.showToast) {
        window.StoryCreateUtils.showToast(message, type);
      } else {
        alert(message);
      }
    },
    
    // Clear content when closing modals if needed
    clearContentOnModalClose: function() {
      // This can be called when modals are closed to ensure clean state
      console.log('Modal closed - content state maintained');
    },
    
    // Enhanced modal state management
    ensureCleanModalState: function() {
      // Clear any temporary modal data when opening new modals
      const linkText = document.getElementById('link-text');
      const linkUrl = document.getElementById('link-url');
      
      if (linkText) linkText.value = '';
      if (linkUrl) linkUrl.value = '';
      
      console.log('Modal state cleaned');
    }
  };

  function init() {
    if (document.readyState !== 'loading') {
      Modals.init();
    } else {
      document.addEventListener('DOMContentLoaded', () => Modals.init());
    }
  }

  // Export
  window.StoryModals = Modals;

  // Auto-init
  init();
})();