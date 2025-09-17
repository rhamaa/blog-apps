# Use django-comments-xtd as the comments app
COMMENTS_APP = "django_comments_xtd"

# Django-comments-xtd configuration for Wagtail
COMMENTS_XTD_CONFIRM_EMAIL = True  # Email confirmation before publishing
COMMENTS_XTD_MAX_THREAD_LEVEL = 3  # Maximum nesting level (0=flat, 1=one level, etc)
COMMENTS_XTD_LIST_PAGINATE_BY = 10  # Comments per page
COMMENTS_XTD_FORM_CLASS = "django_comments_xtd.forms.XtdCommentForm"

# Anti-spam settings
COMMENTS_XTD_SALT = b"your-secret-salt-here"  # Change this in production
COMMENTS_XTD_FROM_EMAIL = "noreply@runutin.com"  # Change to your domain
COMMENTS_XTD_CONTACT_EMAIL = "admin@runutin.com"  # Change to your email

# Moderation settings
COMMENTS_XTD_APP_MODEL_OPTIONS = {
    'blog.blogpage': {
        'allow_flagging': True,
        'allow_feedback': True,  # Like/dislike
        'show_feedback': True,
    }
}
