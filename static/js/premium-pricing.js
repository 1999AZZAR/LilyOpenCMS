/*
Reusable Premium Pricing Module
- Handles premium checkbox toggle and prize input visibility
- Expects specific element IDs for premium checkbox, prize section, prize input, and coin type select
- Provides: PremiumPricing.init({ premiumId, prizeSectionId, prizeId, coinTypeId })
*/
(function (global) {
  'use strict';

  function $(id) { return document.getElementById(id); }

  function setupPremiumPricing(options) {
    const premiumCheckbox = $(options.premiumId);
    const prizeSection = $(options.prizeSectionId);
    const prizeInput = $(options.prizeId);
    const coinTypeSelect = $(options.coinTypeId);

    if (!premiumCheckbox || !prizeSection || !prizeInput || !coinTypeSelect) {
      console.warn('Premium pricing: Some required elements not found', options);
      return;
    }

    // Function to toggle prize input visibility
    function togglePrizeInput() {
      if (premiumCheckbox.checked) {
        prizeSection.classList.remove('hidden');
        prizeInput.setAttribute('required', 'true');
        prizeInput.setAttribute('aria-required', 'true');
        coinTypeSelect.setAttribute('required', 'true');
        coinTypeSelect.setAttribute('aria-required', 'true');
      } else {
        prizeSection.classList.add('hidden');
        prizeInput.removeAttribute('required');
        prizeInput.setAttribute('aria-required', 'false');
        coinTypeSelect.removeAttribute('required');
        coinTypeSelect.setAttribute('aria-required', 'false');
        // Reset prize to 0 when premium is unchecked
        prizeInput.value = '0';
        coinTypeSelect.value = 'any';
      }
    }

    // Add event listener
    premiumCheckbox.addEventListener('change', togglePrizeInput);

    // Initialize state on page load
    togglePrizeInput();

    // Return cleanup function
    return function cleanup() {
      premiumCheckbox.removeEventListener('change', togglePrizeInput);
    };
  }

  function init(options) {
    if (!options || typeof options !== 'object') {
      console.error('PremiumPricing.init requires an options object');
      return;
    }

    // Set default IDs if not provided
    const config = {
      premiumId: options.premiumId || 'is-premium',
      prizeSectionId: options.prizeSectionId || 'prize-input-section',
      prizeId: options.prizeId || 'prize',
      coinTypeId: options.coinTypeId || 'prize-coin-type'
    };

    // Wait for DOM to be ready
    function ready(fn) {
      if (document.readyState !== 'loading') {
        fn();
      } else {
        document.addEventListener('DOMContentLoaded', fn);
      }
    }

    ready(function() {
      return setupPremiumPricing(config);
    });
  }

  global.PremiumPricing = { init };
})(window);
