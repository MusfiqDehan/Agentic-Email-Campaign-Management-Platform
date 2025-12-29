/**
 * Newsletter Configuration
 * 
 * Update these values to connect to your backend API.
 */
const NEWSLETTER_CONFIG = {
    // API endpoint for the public subscribe endpoint
    API_URL: 'http://localhost:8002/api/v1/campaigns/public/subscribe/',
    
    // The subscription token for your contact list
    // Each ContactList has a unique subscription_token
    LIST_TOKEN: 'h3W5q4gM1K2vc0v0NZgkeArVc3RjT9qVMGPMgSHJYEaIAJzolcMgz2fr51rh1d8t',
    
    // Optional: Custom success messages
    MESSAGES: {
        success: 'Welcome aboard! 🎉',
        successWithConfirmation: 'Please check your email to confirm your subscription.',
        alreadySubscribed: 'Thanks! Your information has been updated.',
        error: 'Something went wrong. Please try again.',
        invalidEmail: 'Please enter a valid email address.',
        rateLimited: 'Too many requests. Please wait a moment and try again.',
    },
    
    // Optional: Enable/disable features
    FEATURES: {
        showOptionalFields: true,  // Show first name, last name fields
        animateSuccess: true,      // Animate success message
        hideFormOnSuccess: false,  // Hide form after successful submission
    }
};

// Freeze config to prevent accidental modifications
Object.freeze(NEWSLETTER_CONFIG);
Object.freeze(NEWSLETTER_CONFIG.MESSAGES);
Object.freeze(NEWSLETTER_CONFIG.FEATURES);
