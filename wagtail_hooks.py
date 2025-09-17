from wagtail import hooks
from wagtail.admin import messages
from django.urls import reverse, path
from django.utils.html import format_html
from django_comments_xtd.models import XtdComment
from wagtail.admin.menu import MenuItem
from django.shortcuts import render, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseBadRequest
from django import forms


def comments_admin_view(request):
    """Custom admin view for managing comments"""
    # Get BlogPage content type
    try:
        blog_content_type = ContentType.objects.get(app_label='blog', model='blogpage')
        comments = XtdComment.objects.filter(content_type=blog_content_type).order_by('-submit_date')
    except ContentType.DoesNotExist:
        comments = XtdComment.objects.none()
    
    context = {
        'comments': comments,
        'title': 'Kelola Komentar Blog',
    }
    return render(request, 'blog/admin/comments.html', context)


@hooks.register('register_admin_urls')
def register_comments_admin_url():
    return [
        path('comments/', comments_admin_view, name='blog_comments_admin'),
        path('comments/<int:pk>/edit/', comment_edit_view, name='blog_comment_edit'),
        path('comments/<int:pk>/toggle-public/', comment_toggle_public, name='blog_comment_toggle_public'),
        path('comments/<int:pk>/toggle-removed/', comment_toggle_removed, name='blog_comment_toggle_removed'),
    ]


@hooks.register('register_admin_menu_item')
def register_comments_menu_item():
    return MenuItem(
        'Komentar Blog', 
        reverse('blog_comments_admin'),
        icon_name='comment',
        order=300
    )


@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, page_perms=None, is_parent=False, next_url=None, user=None, **kwargs):
    """Add comment count to page listing"""
    if hasattr(page, 'enable_comments') and page.enable_comments:
        comment_count = XtdComment.objects.filter(
            content_type__model='blogpage',
            object_pk=str(page.pk),
            is_public=True
        ).count()
        
        if comment_count > 0:
            yield format_html(
                '<span class="button button-small button-secondary" title="Jumlah komentar">'
                '<svg class="icon icon-comment" aria-hidden="true"><use href="#icon-comment"></use></svg> {}'
                '</span>',
                comment_count
            )


class CommentEditForm(forms.ModelForm):
    class Meta:
        model = XtdComment
        fields = [
            'user_name', 'user_email', 'user_url',
            'comment', 'is_public', 'is_removed'
        ]
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 5}),
        }


def comment_edit_view(request, pk: int):
    comment = get_object_or_404(XtdComment, pk=pk)
    if request.method == 'POST':
        form = CommentEditForm(request.POST, instance=comment)
        if form.is_valid():
            saved = form.save()
            return JsonResponse({
                'ok': True,
                'id': saved.pk,
                'user_name': saved.user_name,
                'user_email': saved.user_email,
                'comment': saved.comment,
                'is_public': saved.is_public,
                'is_removed': saved.is_removed,
                'submit_date': saved.submit_date.strftime('%d %b %Y %H:%M')
            })
        # return rendered form with errors
        html = render(request, 'blog/admin/comment_form.html', {'form': form, 'comment': comment}).content
        return HttpResponseBadRequest(html)

    # GET -> return form HTML fragment
    form = CommentEditForm(instance=comment)
    return render(request, 'blog/admin/comment_form.html', {'form': form, 'comment': comment})


def comment_toggle_public(request, pk: int):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    comment = get_object_or_404(XtdComment, pk=pk)
    comment.is_public = not comment.is_public
    # If setting to public, also ensure not removed
    if comment.is_public:
        comment.is_removed = False
    comment.save(update_fields=['is_public', 'is_removed'])
    return JsonResponse({
        'ok': True,
        'id': comment.pk,
        'is_public': comment.is_public,
        'is_removed': comment.is_removed,
        'submit_date': comment.submit_date.strftime('%d %b %Y %H:%M')
    })


def comment_toggle_removed(request, pk: int):
    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')
    comment = get_object_or_404(XtdComment, pk=pk)
    comment.is_removed = not comment.is_removed
    # If removed, also set public to False
    if comment.is_removed:
        comment.is_public = False
    comment.save(update_fields=['is_public', 'is_removed'])
    return JsonResponse({
        'ok': True,
        'id': comment.pk,
        'is_public': comment.is_public,
        'is_removed': comment.is_removed,
        'submit_date': comment.submit_date.strftime('%d %b %Y %H:%M')
    })


@hooks.register('after_create_page')
def send_comment_notification_on_page_create(request, page):
    """Optional: Send notification when new blog post is created"""
    if hasattr(page, 'enable_comments'):
        messages.success(
            request, 
            f'Halaman "{page.title}" berhasil dibuat. Komentar {"diaktifkan" if page.enable_comments else "dinonaktifkan"}.'
        )
