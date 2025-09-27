# WildDocs Frontend Structure

This document explains the organized frontend structure for the WildDocs Django application.

## 📁 Directory Structure

```
frontend/
├── layouts/          # Base layout templates
│   └── base.html     # Main layout with navigation, footer, scripts
├── pages/            # Page-specific templates
│   ├── home.html     # Homepage template
│   └── login.html    # Login page template
├── static/           # Static assets
│   ├── css/
│   │   └── main.css  # Main stylesheet
│   ├── js/
│   │   └── main.js   # Main JavaScript file
│   ├── images/       # Image assets
│   └── fonts/        # Custom fonts
└── base.html         # Simple base extending layouts/base.html
```

## 🎨 Layouts

### `layouts/base.html`
The main layout template that includes:
- HTML structure and meta tags
- Bootstrap CSS framework
- Custom CSS (main.css)
- Navigation component
- Toast notifications for Django messages
- Footer
- JavaScript libraries and custom scripts

**Features:**
- Responsive navigation with authentication states
- Toast notification system
- SEO-optimized meta tags
- Font Awesome icons support
- Modern CSS variables and styling

## 📄 Pages

### `pages/home.html`
Landing page template featuring:
- Hero section with call-to-action
- Features showcase
- Step-by-step process explanation
- Available documents list

### `pages/login.html` 
Login page template with:
- Two-column layout (form + info panel)
- Form validation
- Password visibility toggle
- Responsive design

## 🎨 Static Assets

### CSS (`static/css/main.css`)
- CSS custom properties (variables)
- Modern component styling
- Responsive design utilities
- Animation keyframes
- Toast notification styles

### JavaScript (`static/js/main.js`)
- Toast notification system
- Form validation
- Page transitions
- AJAX utilities
- Loading spinner utilities
- Global error handling

## 🚀 Usage

### Creating New Pages
1. Create your template in `frontend/pages/`
2. Extend `layouts/base.html`
3. Use appropriate blocks:
   - `{% block title %}` - Page title
   - `{% block content %}` - Main content
   - `{% block extra_css %}` - Additional CSS
   - `{% block extra_js %}` - Additional JavaScript

### Example Page Template
```html
{% extends "layouts/base.html" %}

{% block title %}Your Page - WildDocs{% endblock %}

{% block content %}
<div class="container">
    <h1>Your Page Content</h1>
</div>
{% endblock %}

{% block extra_css %}
<style>
    /* Page-specific styles */
</style>
{% endblock %}

{% block extra_js %}
<script>
    // Page-specific JavaScript
</script>
{% endblock %}
```

### Adding Static Assets
- **CSS**: Add files to `static/css/` and link in templates
- **JavaScript**: Add files to `static/js/` and include in templates  
- **Images**: Add to `static/images/` and reference with `{% static 'images/filename.jpg' %}`

### Using JavaScript Utilities
The main.js file provides global utilities:

```javascript
// Show toast notification
WildDocs.showToast('Success message!', 'success');

// Loading spinner
WildDocs.LoadingSpinner.show(buttonElement);
WildDocs.LoadingSpinner.hide(buttonElement, 'Original Text');

// AJAX requests
const data = await WildDocs.Ajax.get('/api/endpoint/');
await WildDocs.Ajax.post('/api/endpoint/', {key: 'value'});

// Utility functions
const formatted = WildDocs.Utils.formatDate('2025-09-27');
const debounced = WildDocs.Utils.debounce(myFunction, 300);
```

## 🔧 Configuration

### Django Settings
Make sure your `settings.py` includes:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "frontend",
        ],
        'APP_DIRS': True,
        # ... other settings
    },
]

STATICFILES_DIRS = [
    BASE_DIR / "frontend/static",
]
```

## 📱 Features

- ✅ Responsive design (mobile-first)
- ✅ Modern CSS with custom properties
- ✅ Toast notification system
- ✅ Form validation
- ✅ Loading states
- ✅ AJAX utilities
- ✅ Error handling
- ✅ SEO optimization
- ✅ Accessibility features

## 🎯 Best Practices

1. **Consistent Structure**: Always extend `layouts/base.html`
2. **Semantic HTML**: Use proper HTML5 elements
3. **Progressive Enhancement**: Core functionality works without JavaScript
4. **Mobile First**: Design for mobile, enhance for desktop
5. **Performance**: Minimize HTTP requests, optimize images
6. **Accessibility**: Include ARIA labels and keyboard navigation