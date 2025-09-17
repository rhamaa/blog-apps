from django.urls import path

from .feeds import BlogFeed, CategoryBlogFeed

app_name = "blog"

urlpatterns = [
    path("rss/", BlogFeed(), name="blog_rss"),
    path("rss/category/<int:page_id>/", CategoryBlogFeed(), name="blog_category_rss"),
]
