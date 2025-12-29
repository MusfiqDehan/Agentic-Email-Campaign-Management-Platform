/**
 * Newsletter Subscription Handler
 * 
 * Handles form submission, API integration, and user feedback
 * for the public newsletter subscription form.
 */

(function() {
    'use strict';

    // DOM Elements
    const form = document.getElementById('newsletter-form');
    const submitBtn = document.getElementById('submit-btn');
    const emailInput = document.getElementById('email');
    const firstNameInput = document.getElementById('first_name');
    const lastNameInput = document.getElementById('last_name');
    const websiteInput = document.getElementById('website'); // Honeypot
    const toggleOptional = document.getElementById('toggle-optional');
    const optionalContent = document.getElementById('optional-content');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');
    const successText = document.getElementById('success-text');
    const errorText = document.getElementById('error-text');

    // State
    let isSubmitting = false;

    /**
     * Initialize the newsletter form
     */
    function init() {
        // Check if config is loaded
        if (typeof NEWSLETTER_CONFIG === 'undefined') {
            console.error('Newsletter config not loaded. Make sure config.js is included before newsletter.js');
            return;
        }

        // Validate configuration
        if (NEWSLETTER_CONFIG.LIST_TOKEN === 'YOUR_SUBSCRIPTION_TOKEN_HERE') {
            console.warn('⚠️ Newsletter: Please update LIST_TOKEN in config.js with your actual subscription token');
        }

        // Setup event listeners
        setupEventListeners();

        // Hide optional fields if disabled
        if (!NEWSLETTER_CONFIG.FEATURES.showOptionalFields) {
            const optionalFields = document.getElementById('optional-fields');
            if (optionalFields) {
                optionalFields.style.display = 'none';
            }
        }

        console.log('✅ Newsletter form initialized');
    }

    /**
     * Setup all event listeners
     */
    function setupEventListeners() {
        // Form submission
        form.addEventListener('submit', handleSubmit);

        // Optional fields toggle
        if (toggleOptional && optionalContent) {
            toggleOptional.addEventListener('click', toggleOptionalFields);
        }

        // Clear error on input
        emailInput.addEventListener('input', () => {
            hideMessages();
        });

        // Email validation on blur
        emailInput.addEventListener('blur', () => {
            if (emailInput.value && !isValidEmail(emailInput.value)) {
                showError(NEWSLETTER_CONFIG.MESSAGES.invalidEmail);
            }
        });
    }

    /**
     * Toggle optional fields visibility
     */
    function toggleOptionalFields() {
        const isActive = toggleOptional.classList.toggle('active');
        optionalContent.classList.toggle('show', isActive);
    }

    /**
     * Handle form submission
     */
    async function handleSubmit(event) {
        event.preventDefault();

        // Prevent double submission
        if (isSubmitting) return;

        // Get form data
        const email = emailInput.value.trim();
        const firstName = firstNameInput ? firstNameInput.value.trim() : '';
        const lastName = lastNameInput ? lastNameInput.value.trim() : '';
        const website = websiteInput ? websiteInput.value.trim() : ''; // Honeypot

        // Validate email
        if (!email) {
            showError('Please enter your email address.');
            emailInput.focus();
            return;
        }

        if (!isValidEmail(email)) {
            showError(NEWSLETTER_CONFIG.MESSAGES.invalidEmail);
            emailInput.focus();
            return;
        }

        // Start submission
        setLoading(true);
        hideMessages();

        try {
            const response = await subscribeToNewsletter({
                list_token: NEWSLETTER_CONFIG.LIST_TOKEN,
                email: email,
                first_name: firstName,
                last_name: lastName,
                website: website, // Honeypot - server will detect if filled
            });

            handleSuccess(response);
        } catch (error) {
            handleError(error);
        } finally {
            setLoading(false);
        }
    }

    /**
     * Make API request to subscribe
     */
    async function subscribeToNewsletter(data) {
        const response = await fetch(NEWSLETTER_CONFIG.API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify(data),
        });

        // Parse response
        const result = await response.json();

        // Handle different status codes
        if (!response.ok) {
            const error = new Error(result.error || result.message || 'Request failed');
            error.status = response.status;
            error.details = result.details || result.errors;
            throw error;
        }

        return result;
    }

    /**
     * Handle successful subscription
     */
    function handleSuccess(response) {
        let message = NEWSLETTER_CONFIG.MESSAGES.success;

        // Customize message based on response
        if (response.status === 'pending_confirmation') {
            message = NEWSLETTER_CONFIG.MESSAGES.successWithConfirmation;
        } else if (response.status === 'updated') {
            message = NEWSLETTER_CONFIG.MESSAGES.alreadySubscribed;
        }

        // Update success message
        successText.textContent = message;

        // Show success message
        showSuccess();

        // Optionally hide form
        if (NEWSLETTER_CONFIG.FEATURES.hideFormOnSuccess) {
            form.style.display = 'none';
        } else {
            // Clear form
            form.reset();
            
            // Close optional fields if open
            if (toggleOptional && toggleOptional.classList.contains('active')) {
                toggleOptional.classList.remove('active');
                optionalContent.classList.remove('show');
            }
        }

        // Track conversion (if analytics is available)
        trackConversion('newsletter_subscribe', {
            status: response.status,
            double_opt_in: response.double_opt_in,
        });
    }

    /**
     * Handle subscription error
     */
    function handleError(error) {
        console.error('Subscription error:', error);

        let message = NEWSLETTER_CONFIG.MESSAGES.error;

        // Customize based on error
        if (error.status === 429) {
            message = NEWSLETTER_CONFIG.MESSAGES.rateLimited;
        } else if (error.status === 404) {
            message = 'This signup form is no longer active.';
        } else if (error.details) {
            // Extract first error message from details
            const firstError = Object.values(error.details)[0];
            if (Array.isArray(firstError)) {
                message = firstError[0];
            } else if (typeof firstError === 'string') {
                message = firstError;
            }
        }

        showError(message);
    }

    /**
     * Show success message
     */
    function showSuccess() {
        hideMessages();
        successMessage.classList.add('show');

        if (NEWSLETTER_CONFIG.FEATURES.animateSuccess) {
            successMessage.style.animation = 'none';
            successMessage.offsetHeight; // Trigger reflow
            successMessage.style.animation = null;
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        hideMessages();
        errorText.textContent = message;
        errorMessage.classList.add('show');
    }

    /**
     * Hide all messages
     */
    function hideMessages() {
        successMessage.classList.remove('show');
        errorMessage.classList.remove('show');
    }

    /**
     * Set loading state
     */
    function setLoading(loading) {
        isSubmitting = loading;
        submitBtn.disabled = loading;
        submitBtn.classList.toggle('loading', loading);
        emailInput.disabled = loading;
        
        if (firstNameInput) firstNameInput.disabled = loading;
        if (lastNameInput) lastNameInput.disabled = loading;
    }

    /**
     * Validate email format
     */
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Track conversion for analytics
     */
    function trackConversion(eventName, data) {
        // Google Analytics 4
        if (typeof gtag === 'function') {
            gtag('event', eventName, data);
        }

        // Facebook Pixel
        if (typeof fbq === 'function') {
            fbq('track', 'Lead', data);
        }

        // Custom analytics
        if (typeof window.analytics === 'object' && typeof window.analytics.track === 'function') {
            window.analytics.track(eventName, data);
        }

        console.log('📊 Conversion tracked:', eventName, data);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
