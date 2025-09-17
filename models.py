from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.search import index
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.db.models.functions import TruncMonth
from taggit.models import Tag
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from utils.models import BasePage
from django.core.validators import MinValueValidator, MaxValueValidator


class BlogIndexPage(BasePage):
    # Batasi child hanya BlogPage
    subpage_types = ["blog.BlogPage"]

    # Fitur RichText diperluas agar bisa embed dan inline code
    intro = RichTextField(blank=True, features=[
        "h2", "h3", "bold", "italic", "ol", "ul",
        "link", "document-link", "image", "embed", "code", "hr", "blockquote"
    ])

    content_panels = BasePage.content_panels + [
        FieldPanel('intro')
    ]

    # Settings controls for sidebar and behavior
    show_categories = models.BooleanField(default=True, help_text="Tampilkan widget Kategori (sibling BlogIndexPage)")
    show_recent = models.BooleanField(default=True, help_text="Tampilkan widget Terbaru")
    show_popular_tags = models.BooleanField(default=True, help_text="Tampilkan widget Tag Populer")
    show_archives = models.BooleanField(default=True, help_text="Tampilkan widget Arsip")
    show_rss = models.BooleanField(default=True, help_text="Tampilkan widget RSS")
    enable_search = models.BooleanField(default=True, help_text="Aktifkan form pencarian di index ini")
    posts_per_page = models.PositiveIntegerField(default=9, validators=[MinValueValidator(1), MaxValueValidator(60)], help_text="Jumlah posting per halaman")

    settings_panels = BasePage.settings_panels + [
        MultiFieldPanel([
            FieldPanel('enable_search'),
            FieldPanel('posts_per_page'),
        ], heading="Search & Pagination"),
        MultiFieldPanel([
            FieldPanel('show_categories'),
            FieldPanel('show_recent'),
            FieldPanel('show_popular_tags'),
            FieldPanel('show_archives'),
            FieldPanel('show_rss'),
        ], heading="Sidebar Widgets"),
    ]

    def get_context(self, request):
        # Update context to include published posts with search, tag filter, and pagination
        context = super().get_context(request)

        q = request.GET.get('q', '').strip()
        tag = request.GET.get('tag', '').strip()
        month_param = request.GET.get('month', '').strip()  # format: YYYY-MM
        page_number = request.GET.get('page', 1)

        # Query BlogPage descendants
        posts_qs = (
            BlogPage.objects.live()
            .descendant_of(self)
            .order_by('-date')
            .prefetch_related('tagged_items__tag')
        )

        if q and self.enable_search:
            # Use Wagtail Search API for better performance and relevance
            posts_qs = posts_qs.search(q)

        if tag:
            posts_qs = posts_qs.filter(tags__name=tag)

        # Filter by archive month
        if month_param:
            try:
                year_str, month_str = month_param.split('-')
                year_i, month_i = int(year_str), int(month_str)
                posts_qs = posts_qs.filter(date__year=year_i, date__month=month_i)
            except Exception:
                pass

        per_page = self.posts_per_page or 9
        paginator = Paginator(posts_qs, per_page)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        context.update({
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': paginator.num_pages > 1,
            'q': q,
            'active_tag': tag,
            'active_month': month_param,
        })

        # Sidebar data (conditionally computed)
        if self.show_recent:
            context['recent_posts'] = (
                BlogPage.objects.live()
                .descendant_of(self)
                .order_by('-date')
                .only('title', 'date')[:5]
            )

        if self.show_popular_tags:
            # Popular tags via BlogPageTag through (ClusterTaggableManager uses ParentalKey 'content_object')
            desc_qs = BlogPage.objects.live().descendant_of(self)
            popular_tags = (
                Tag.objects
                .filter(blog_blogpagetag_items__content_object__in=desc_qs)
                .annotate(num_times=Count('blog_blogpagetag_items'))
                .order_by('-num_times')[:10]
            )

            # Fallback ke popular tags global jika kategori ini belum punya tag
            if not popular_tags:
                global_desc = BlogPage.objects.live()
                popular_tags = (
                    Tag.objects
                    .filter(blog_blogpagetag_items__content_object__in=global_desc)
                    .annotate(num_times=Count('blog_blogpagetag_items'))
                    .order_by('-num_times')[:10]
                )

            context['popular_tags'] = popular_tags

        if self.show_archives:
            context['archives'] = (
                BlogPage.objects.live()
                .descendant_of(self)
                .annotate(month=TruncMonth('date'))
                .values('month')
                .annotate(count=Count('id'))
                .order_by('-month')
            )

        # Categories as sibling BlogIndexPage under same parent
        if self.show_categories:
            try:
                siblings = self.get_siblings(inclusive=True).live().specific()
                categories = [p for p in siblings if isinstance(p, BlogIndexPage)]
            except Exception:
                categories = []
            context['categories'] = categories
        context['active_category_id'] = self.id
        context['enable_search'] = self.enable_search
        context['show_rss'] = self.show_rss
        return context

class BlogPage(BasePage):
    # Hanya boleh berada di bawah BlogIndexPage
    parent_page_types = ["blog.BlogIndexPage"]

    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    # Aktifkan fitur RichText termasuk embed dan inline code
    body = RichTextField(blank=True, features=[
        "h2", "h3", "bold", "italic", "ol", "ul",
        "link", "document-link", "image", "embed", "code", "hr", "blockquote"
    ])
    
    # Wagtail search indexing fields
    search_fields = BasePage.search_fields + [
        index.SearchField('title', partial_match=True),
        index.SearchField('intro', partial_match=True),
    ]
    # Tags
    tags = ClusterTaggableManager(through='blog.BlogPageTag', blank=True)

    # Comments toggle
    enable_comments = models.BooleanField(default=True, help_text="Aktifkan komentar pada halaman ini")
    
    def get_absolute_url(self):
        """Required by django-comments-xtd for proper URL generation"""
        return self.url

    content_panels = BasePage.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        FieldPanel('body'),
        FieldPanel('tags'),
    ]

    settings_panels = BasePage.settings_panels + [
        FieldPanel('enable_comments'),
    ]


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage', related_name='tagged_items', on_delete=models.CASCADE
    )
