from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed
from wagtail.models import Site

from .models import BlogPage, BlogIndexPage


class BlogFeed(Feed):
    feed_type = Rss201rev2Feed
    title = "Runutin Blog"
    link = "/blog/"
    description = "RSS feed for the latest blog posts"

    def items(self):
        return BlogPage.objects.live().order_by("-date")[:20]

    def item_title(self, item: BlogPage):
        return item.title

    def item_description(self, item: BlogPage):
        # Prefer listing_summary from BasePage if available
        summary = getattr(item, "get_listing_summary", None)
        if callable(summary):
            return summary()
        return item.intro

    def item_link(self, item: BlogPage):
        # Build absolute URL using Wagtail's get_url_parts
        parts = item.get_url_parts()
        if parts:
            _site_id, root_url, url = parts
            return f"{root_url}{url}"
        # Fallback to relative URL
        return item.url or "/"


class CategoryBlogFeed(Feed):
    feed_type = Rss201rev2Feed

    def get_object(self, request, page_id: int):
        return BlogIndexPage.objects.get(id=page_id)

    def title(self, obj: BlogIndexPage):
        return f"Runutin Blog — {obj.title}"

    def link(self, obj: BlogIndexPage):
        return obj.url

    def description(self, obj: BlogIndexPage):
        return f"RSS feed for posts under {obj.title}"

    def items(self, obj: BlogIndexPage):
        return (
            BlogPage.objects.live().descendant_of(obj).order_by("-date")[:20]
        )

    def item_title(self, item: BlogPage):
        return item.title

    def item_description(self, item: BlogPage):
        summary = getattr(item, "get_listing_summary", None)
        if callable(summary):
            return summary()
        return item.intro

    def item_link(self, item: BlogPage):
        parts = item.get_url_parts()
        if parts:
            _site_id, root_url, url = parts
            return f"{root_url}{url}"
        return item.url or "/"
