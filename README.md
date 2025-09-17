# Blog App — Comments (Wagtail + django-comments-xtd)

This app integrates blog pages with django-comments-xtd to provide a WordPress-like commenting experience, fully embedded into Wagtail (frontend comments + Wagtail Admin moderation panel with modal editing).

## Overview
- Frontend: comment list + form embedded on each `BlogPage` (toggle per page).
- Backend: Wagtail Admin menu "Komentar Blog" lists comments with actions:
  - Edit in modal (AJAX).
  - Publish/Unpublish, Remove/Restore (AJAX), then auto-refresh.
- Powered by `django-comments-xtd` for threaded comments, email confirmations, moderation, and anti-spam features.

## Requirements
- Django 5.x
- Wagtail 6.x/7.x
- django-comments-xtd
- django.contrib.sites enabled with a valid `SITE_ID`.

## Installation & Configuration

1) Base settings
- File: `Runutin/settings/base.py`
  - Ensure these apps are installed (already configured in this project):
    - `django.contrib.sites`
    - `django_comments`
    - `django_comments_xtd`
  - Set the Sites framework:
    - `SITE_ID = 1` (and configure the Site in Django admin to match your domain)

2) Blog app settings
- File: `apps/blog/settings.py`
  - Use django-comments-xtd as comments backend:
    - `COMMENTS_APP = "django_comments_xtd"`
  - Optional advanced settings (already present):
    - `COMMENTS_XTD_CONFIRM_EMAIL = True` (email confirmation prior to publish)
    - `COMMENTS_XTD_MAX_THREAD_LEVEL = 3` (threading depth)
    - `COMMENTS_XTD_LIST_PAGINATE_BY = 10`
    - `COMMENTS_XTD_FORM_CLASS = "django_comments_xtd.forms.XtdCommentForm"`
    - Anti-spam & email: `COMMENTS_XTD_SALT`, `COMMENTS_XTD_FROM_EMAIL`, `COMMENTS_XTD_CONTACT_EMAIL`
    - Per-model options for BlogPage: flagging, like/dislike, etc.

3) URLs
- File: `Runutin/urls.py`
  - Include django-comments-xtd endpoints:
    - `path("comments/", include("django_comments_xtd.urls")),`
  - Wagtail Admin is served at `/admin/` as usual, Django Admin is at `/django-admin/`.

4) Models
- File: `apps/blog/models.py`
  - `BlogPage` has:
    - `enable_comments = models.BooleanField(default=True, help_text="Aktifkan komentar pada halaman ini")`
    - `get_absolute_url(self)` returns `self.url` (required by comments framework for object URLs).
  - The field is exposed via `settings_panels` so editors can toggle per page.

5) Templates (frontend)
- File: `apps/blog/templates/blog/blog_page.html`
  - Load tags: `{% load comments %}` (and `{% load comments_xtd %}` if needed)
  - Render comments when `page.enable_comments` is True:
    - `{% render_comment_list for page %}`
    - `{% render_comment_form for page %}`
- You may override django-comments-xtd templates under `templates/django_comments_xtd/` for custom list/form markup.

6) Wagtail Admin Integration
- File: `apps/blog/wagtail_hooks.py`
  - Admin menu item "Komentar Blog" → `/admin/comments/`
  - `comments_admin_view` lists `XtdComment` items related to `BlogPage` with columns: Artikel, Komentator, Komentar, Tanggal, Status, Aksi.
  - Modal editing:
    - `comment_edit_view` (GET = partial form, POST = save via JSON).
    - Template partial: `apps/blog/templates/blog/admin/comment_form.html` (styled with Wagtail components).
  - Quick actions (AJAX):
    - `comments/<int:pk>/toggle-public/` (publish/unpublish)
    - `comments/<int:pk>/toggle-removed/` (remove/restore)
  - Explorer page listing badge (optional): `register_page_listing_buttons` shows a comment count per page.

## Usage
- In Wagtail admin, open a `BlogPage` → Settings tab → toggle "Aktifkan komentar".
- On the frontend, visit the blog page and submit a comment.
- Moderation:
  - Wagtail Admin → "Komentar Blog" to review all comments.
  - Use dropdown "Aksi" per baris untuk Edit/Publish/Unpublish/Remove/Restore.
  - Edit opens a modal; save updates immediately; quick actions auto-refresh the table.

## Email & Anti-Spam (recommended)
- Configure email backend in your environment:
  - `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, SMTP creds, etc.
- Update `COMMENTS_XTD_FROM_EMAIL`, `COMMENTS_XTD_CONTACT_EMAIL` and `COMMENTS_XTD_SALT` (use a secure random value in production).
- Optionally enable captcha or honeypot if needed.

## Development Notes
- Run migrations:
  - `python manage.py makemigrations && python manage.py migrate`
- If using DB-backed cache (Wagtail uses cache for site paths), create cache table:
  - `python manage.py createcachetable`
- Demo data (if available):
  - `python manage.py load_initial_data`

## Customization
- Change threading depth: `COMMENTS_XTD_MAX_THREAD_LEVEL`.
- Override templates under `templates/django_comments_xtd/`.
- Adjust the admin listing (columns, filters, pagination) in `comments_admin_view` template `apps/blog/templates/blog/admin/comments.html`.
- Add bulk actions (approve multiple) as needed.

## Troubleshooting
- Duplicate Sites error: ensure `django.contrib.sites` is installed only once across settings includes.
- Unknown template tags like `render_xtdcomment_*`: use standard tags `{% render_comment_list %}`, `{% render_comment_form %}`, and ensure `{% load comments %}` is present.
- Admin URL reverse errors for django-comments-xtd: we use a custom Wagtail admin view instead; access Django admin at `/django-admin/` if you need the raw model admin.
- Wagtail hook signature errors (unexpected `user` kwarg): make sure `register_page_listing_buttons` accepts `**kwargs` and optional `user` arg.

## Files touched in this integration
- `Runutin/settings/base.py` — apps + `SITE_ID`.
- `Runutin/urls.py` — `comments/` include.
- `apps/blog/settings.py` — `COMMENTS_APP` and XTD settings.
- `apps/blog/models.py` — `enable_comments`, `get_absolute_url`.
- `apps/blog/templates/blog/blog_page.html` — render comments.
- `apps/blog/templates/blog/admin/comments.html` — Wagtail admin listing + dropdown actions + modal JS.
- `apps/blog/templates/blog/admin/comment_form.html` — Wagtail-styled modal form.
- `apps/blog/wagtail_hooks.py` — hooks, admin URLs, views, AJAX endpoints.

---
If you need additional features (captcha, moderation queue UI, threaded display on frontend, filters/pagination in admin), open an issue or ping the maintainers.