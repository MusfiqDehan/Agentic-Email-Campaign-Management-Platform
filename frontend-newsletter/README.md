# Newsletter Landing Page

A beautiful, responsive landing page for collecting newsletter subscriptions, integrated with the Email Campaign Management Platform's public subscribe API.

## Quick Start

### 1. Get Your Subscription Token

Each contact list in your backend has a unique `subscription_token`. You can find it by:

**Option A: Django Admin**
1. Go to your Django admin panel
2. Navigate to Campaigns > Contact Lists
3. Find your list and copy the `subscription_token`

**Option B: API**
```bash
# Get all contact lists (requires authentication)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/campaigns/contact-lists/
```

**Option C: Database**
```sql
SELECT id, name, subscription_token 
FROM campaigns_contactlist 
WHERE is_active = true;
```

### 2. Configure the Landing Page

Edit `config.js` with your settings:

```javascript
const NEWSLETTER_CONFIG = {
    // Your backend API URL
    API_URL: 'http://localhost:8000/api/v1/campaigns/public/subscribe/',
    
    // Your contact list's subscription token
    LIST_TOKEN: 'your-64-character-subscription-token-here',
    
    // ...
};
```

### 3. Open the Landing Page

Simply open `index.html` in your browser, or serve it with any static file server:

```bash
# Python
python -m http.server 8080

# Node.js (npx)
npx serve .

# PHP
php -S localhost:8080
```

Then visit `http://localhost:8080`

## Files

| File | Description |
|------|-------------|
| `index.html` | Main landing page with newsletter form |
| `styles.css` | All styling (responsive, animations) |
| `config.js` | Configuration (API URL, token, messages) |
| `newsletter.js` | Form handling and API integration |

## Features

### 🎨 Beautiful Design
- Modern, gradient-based design
- Smooth animations and transitions
- Floating cards and visual elements
- Fully responsive (mobile, tablet, desktop)

### 🔒 Spam Protection
- **Honeypot field**: Hidden `website` field that bots auto-fill
- **Rate limiting**: Backend limits to 30 requests/min per IP
- **Validation**: Client and server-side email validation

### 🌐 CORS Support
- Works from any domain (cross-origin requests enabled)
- Proper preflight handling for OPTIONS requests

### 📊 Analytics Ready
- Built-in support for Google Analytics 4
- Facebook Pixel integration
- Custom analytics tracking

## API Integration

### Request Format

```javascript
POST /api/v1/campaigns/public/subscribe/
Content-Type: application/json

{
    "list_token": "abc123...",      // Required - identifies your contact list
    "email": "user@example.com",     // Required
    "first_name": "John",            // Optional
    "last_name": "Doe",              // Optional
    "phone": "+1234567890",          // Optional
    "custom_fields": {},             // Optional - JSON object
    "website": ""                    // Honeypot - must be empty
}
```

### Response Format

**Success (201 Created or 200 OK):**
```json
{
    "message": "Successfully subscribed",
    "status": "subscribed",          // or "pending_confirmation", "updated"
    "double_opt_in": false
}
```

**Error (400 Bad Request):**
```json
{
    "error": "Invalid data",
    "details": {
        "email": ["Enter a valid email address."]
    }
}
```

**Rate Limited (429 Too Many Requests):**
```json
{
    "detail": "Request was throttled."
}
```

## Customization

### Change Colors

Edit the CSS variables in `styles.css`:

```css
:root {
    --primary-500: #6366F1;  /* Main brand color */
    --primary-600: #4F46E5;  /* Hover state */
    --purple-500: #8B5CF6;   /* Gradient end */
    /* ... */
}
```

### Change Text

Edit the HTML in `index.html`:
- Hero title and description
- Feature cards
- Trust indicators

### Custom Messages

Edit `config.js`:

```javascript
MESSAGES: {
    success: 'Welcome aboard! 🎉',
    successWithConfirmation: 'Check your email to confirm.',
    // ...
}
```

## Deployment

### Static Hosting (Recommended)

Upload all 4 files to:
- **Netlify**: Drag & drop to deploy
- **Vercel**: `vercel deploy`
- **GitHub Pages**: Push to `gh-pages` branch
- **AWS S3**: Upload files, enable static hosting
- **Cloudflare Pages**: Connect your repo

### Embed in Existing Site

Copy the form HTML and include the CSS/JS files, or use an iframe:

```html
<iframe 
    src="https://your-landing-page.com" 
    width="100%" 
    height="600" 
    frameborder="0">
</iframe>
```

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    NEWSLETTER SUBSCRIPTION FLOW                  │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────┐                              ┌──────────────────┐
  │   LANDING    │                              │    BACKEND API   │
  │     PAGE     │                              │   (Django DRF)   │
  └──────┬───────┘                              └────────┬─────────┘
         │                                               │
         │  1. User visits landing page                  │
         │  ◄────────────────────────────────            │
         │                                               │
         │  2. User fills form (email, name)             │
         │  ─────────────────────────────────►           │
         │                                               │
         │  3. JavaScript validates input                │
         │  ◄────────────────────────────────            │
         │                                               │
         │  4. POST /public/subscribe/                   │
         │  ─────────────────────────────────►           │
         │     {                                         │
         │       list_token: "abc...",                   │
         │       email: "user@example.com",              │
         │       first_name: "John",                     │
         │       website: ""  // honeypot                │
         │     }                                         │
         │                                               │
         │                           5. Server validates │
         │                              - Check honeypot │
         │                              - Rate limiting  │
         │                              - Email format   │
         │                              - List exists    │
         │                                               │
         │                           6. Create/update    │
         │                              Contact record   │
         │                                               │
         │  7. Response                                  │
         │  ◄─────────────────────────────────           │
         │     {                                         │
         │       message: "Successfully subscribed",     │
         │       status: "subscribed",                   │
         │       double_opt_in: false                    │
         │     }                                         │
         │                                               │
         │  8. Show success message                      │
         │  ◄────────────────────────────────            │
         │                                               │
         │  9. Track conversion (analytics)              │
         │  ─────────────────────────────────►           │
         │                                               │
  ┌──────┴───────┐                              ┌────────┴─────────┐
  │    USER      │                              │    DATABASE      │
  │   BROWSER    │                              │   (PostgreSQL)   │
  └──────────────┘                              └──────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                        IF DOUBLE OPT-IN                         │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │  10. System sends confirmation email                            │
  │  11. User clicks confirmation link                              │
  │  12. Contact status: PENDING → ACTIVE                           │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### CORS Errors
Make sure your backend's `PublicCORSMixin` is applied to the view, or configure global CORS settings.

### 404 Not Found
- Check the `API_URL` in `config.js`
- Ensure the campaigns app URLs are mounted at `/api/v1/campaigns/`

### Invalid List Token
- Verify the `LIST_TOKEN` matches a `subscription_token` in your database
- Check the list is active (`is_active=True`, `is_deleted=False`)

### Rate Limited
- Wait 1 minute before retrying
- The limit is 30 requests/minute per IP

## License

MIT License - feel free to use and modify for your projects.
