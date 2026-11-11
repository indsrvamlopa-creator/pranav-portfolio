from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    AboutSettings, Category, ClientLogo, ContactMessage, ContactSettings, HeadingSettings,
    HeroSettings, Highlight, ProcessStep, Project, Service, Stat, Testimonial, Tool,
)

admin.site.site_header = "Pranav · Portfolio"
admin.site.site_title = "Pranav Admin"
admin.site.index_title = "Dashboard"
admin.site.site_url = "/"
admin.site.enable_nav_sidebar = False   # cleaner screens
admin.site.unregister(Group)            # not needed for a personal site


def _thumb(url, video=False, size=56):
    if not url:
        return format_html('<span class="pf-thumb pf-thumb--empty" style="width:{0}px;height:{0}px">—</span>', size)
    if video:
        return format_html('<video class="pf-thumb" src="{}#t=0.5" muted preload="metadata" style="height:{}px"></video>', url, size)
    return format_html('<img class="pf-thumb" src="{}" style="height:{}px">', url, size)


def _on_off(value):
    return format_html('<span class="pf-pill {}">{}</span>', "pf-pill--on" if value else "pf-pill--off",
                       "Visible" if value else "Hidden")


class PlainTitleMixin:
    """Show 'Projects' instead of Django's 'Select project to change'."""
    def changelist_view(self, request, extra_context=None):
        title = str(self.model._meta.verbose_name_plural)
        return super().changelist_view(request, {**(extra_context or {}), "title": title[:1].upper() + title[1:]})


class FriendlyAdmin(PlainTitleMixin, admin.ModelAdmin):
    """Shared behaviour: simple lists, show/hide actions, friendly messages."""
    list_per_page = 50
    actions = ["show_on_site", "hide_from_site"]
    save_on_top = False

    @admin.action(description="👁  Show selected on website")
    def show_on_site(self, request, queryset):
        n = queryset.update(is_active=True)
        self.message_user(request, f"{n} item(s) are now visible on your website.", messages.SUCCESS)

    @admin.action(description="🙈  Hide selected from website")
    def hide_from_site(self, request, queryset):
        n = queryset.update(is_active=False)
        self.message_user(request, f"{n} item(s) are now hidden from your website.", messages.SUCCESS)

    @admin.display(description="On website")
    def status(self, obj):
        return _on_off(obj.is_active)


# ---------------------------------------------------------------------------
# Website settings — four short pages instead of one long one
# ---------------------------------------------------------------------------
class SingletonAdmin(admin.ModelAdmin):
    save_message = "Saved! Your changes are live on the website."

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.load()
        info = (self.model._meta.app_label, self.model._meta.model_name)
        return redirect(reverse("admin:%s_%s_change" % info, args=[obj.pk]))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = {**(extra_context or {}), "show_save_and_continue": False, "show_save_and_add_another": False,
                         "show_delete": False, "show_history": False,
                         "title": self.model._meta.verbose_name, "subtitle": None}
        return super().change_view(request, object_id, form_url, extra_context)

    def response_change(self, request, obj):
        self.message_user(request, self.save_message, messages.SUCCESS)
        return HttpResponseRedirect(request.path)


@admin.register(HeroSettings)
class HeroSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ("Your name", {"fields": (("name", "title"),)}),
        ("Big headline", {
            "description": "Shown as:  <b>Line 1</b> <i>Gold word</i>  /  <b>Line 2</b> <i>Outline word</i>",
            "fields": (("hero_line1", "hero_gold"), ("hero_line2", "hero_outline")),
        }),
        ("Showreel video", {
            "description": "Upload an MP4 file <b>or</b> paste a YouTube / Vimeo / Google Drive link. "
                           "A “Watch Showreel” button appears on the home page.",
            "fields": ("showreel_file", "showreel_url"),
        }),
        ("Background video (optional)", {
            "description": "A short, silent clip that loops behind the headline. Keep it small (under 15 MB).",
            "fields": ("hero_bg_video",),
        }),
        ("Availability & quick facts", {
            "fields": (("is_available", "availability_text"), ("based_in", "specialty", "response_time")),
        }),
        ("Scrolling gold banner", {"fields": ("marquee_items",)}),
        ("Google search text", {"classes": ("collapse",), "fields": ("seo_description",)}),
    )


@admin.register(AboutSettings)
class AboutSettingsAdmin(SingletonAdmin):
    readonly_fields = ("photo_preview",)
    fieldsets = (
        ("Your photo", {"fields": ("profile_photo", "photo_preview")}),
        ("About text", {"fields": (("about_title", "about_gold"), "about_text", "about_tags")}),
        ("Badge on the photo", {"fields": (("badge_number", "badge_label"),)}),
        ("Resume / CV", {"description": "Upload a PDF to show a “Download CV” button.", "fields": ("resume",)}),
    )

    @admin.display(description="Current photo")
    def photo_preview(self, obj):
        return _thumb(obj.profile_photo.url if obj.profile_photo else "", size=160)


@admin.register(ContactSettings)
class ContactSettingsAdmin(SingletonAdmin):
    fieldsets = (
        ("How people reach you", {"fields": ("email", "phone", "whatsapp", "whatsapp_message", "location")}),
        ("Contact section text", {"fields": (("contact_title", "contact_gold"), "contact_intro")}),
        ("Contact form options", {
            "description": "Buttons visitors can tap in the form. One option per line.",
            "fields": (("project_types", "budgets"),),
        }),
        ("Social media", {
            "description": "Paste full links. Leave empty to hide.",
            "fields": (("instagram", "youtube"), ("behance", "linkedin"), ("vimeo", "twitter")),
        }),
    )


@admin.register(HeadingSettings)
class HeadingSettingsAdmin(SingletonAdmin):
    fieldsets = (
        (None, {
            "description": "Each title has a normal part and a <i>gold italic</i> part.",
            "fields": (("services_title", "services_gold"), ("work_title", "work_gold"),
                       ("skills_title", "skills_gold"), ("process_title", "process_gold"),
                       ("testimonials_title", "testimonials_gold"),
                       ("cta_title", "cta_gold"), "cta_button"),
        }),
    )


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
@admin.register(Project)
class ProjectAdmin(FriendlyAdmin):
    list_display = ("preview", "title", "category", "media_type", "featured", "is_active", "order")
    list_display_links = ("preview", "title")
    list_editable = ("featured", "is_active", "order")
    list_filter = ("category", "featured", "is_active")
    search_fields = ("title", "client", "tools", "description")
    readonly_fields = ("preview_large",)
    fieldsets = (
        ("1 · Project details", {"fields": ("title", ("category", "year"), "client", "description")}),
        ("2 · Video", {
            "description": "Upload a video file <b>or</b> paste a link (YouTube, Vimeo, Instagram, Google Drive). "
                           "YouTube links get a thumbnail automatically.",
            "fields": ("video_file", "video_url", "preview_on_hover"),
        }),
        ("3 · Cover image (optional)", {"fields": ("thumbnail", "thumbnail_url", "preview_large")}),
        ("4 · Extra info (optional)", {"classes": ("collapse",), "fields": ("role", "tools")}),
        ("5 · Display", {"fields": (("is_active", "featured"), "order")}),
    )

    @admin.display(description="")
    def preview(self, obj):
        if obj.image:
            return _thumb(obj.image)
        if obj.video_file:
            return _thumb(obj.video_file.url, video=True)
        return _thumb("")

    @admin.display(description="Current cover")
    def preview_large(self, obj):
        if obj.image:
            return _thumb(obj.image, size=180)
        if obj.video_file:
            return _thumb(obj.video_file.url, video=True, size=180)
        return "No cover yet — a gold placeholder is shown on the website."

    @admin.display(description="Video")
    def media_type(self, obj):
        if obj.video_file:
            return mark_safe('<span class="pf-pill pf-pill--gold">🎞 Uploaded</span>')
        if obj.video_url:
            return mark_safe('<span class="pf-pill pf-pill--gold">🔗 Link</span>')
        return mark_safe('<span class="pf-pill pf-pill--off">None</span>')

    def save_model(self, request, obj, form, change):
        obj.is_sample = False  # once edited, it's real content
        super().save_model(request, obj, form, change)


@admin.register(Category)
class CategoryAdmin(FriendlyAdmin):
    list_display = ("name", "project_count", "is_active", "order")
    list_editable = ("is_active", "order")
    fields = ("name", "slug", "is_active", "order")
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Projects")
    def project_count(self, obj):
        return obj.projects.count()


# ---------------------------------------------------------------------------
# Home page sections
# ---------------------------------------------------------------------------
@admin.register(Service)
class ServiceAdmin(FriendlyAdmin):
    list_display = ("title", "starting_price", "is_active", "order")
    list_editable = ("is_active", "order")
    fields = ("title", "description", "icon", "starting_price", "is_active", "order")


@admin.register(Stat)
class StatAdmin(FriendlyAdmin):
    list_display = ("label", "value", "suffix", "is_active", "order")
    list_editable = ("value", "suffix", "is_active", "order")
    fields = (("value", "suffix"), "label", "is_active", "order")


@admin.register(Tool)
class ToolAdmin(FriendlyAdmin):
    list_display = ("logo_preview", "name", "group", "level", "years", "is_active", "order")
    list_display_links = ("logo_preview", "name")
    list_editable = ("group", "level", "is_active", "order")
    list_filter = ("group", "is_active")
    fieldsets = (
        (None, {"fields": ("name", "group", "level", "years")}),
        ("Icon", {"description": "Upload the app logo, or leave empty to show the badge letters in gold.",
                  "fields": ("logo", "short")}),
        ("Display", {"fields": (("is_active", "order"),)}),
    )

    @admin.display(description="")
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="width:34px;height:34px;object-fit:contain;border-radius:8px">', obj.logo.url)
        return format_html('<span class="pf-tag pf-tag--gold" style="width:34px;height:34px;justify-content:center;border-radius:8px">{}</span>', obj.short)


@admin.register(ProcessStep)
class ProcessStepAdmin(FriendlyAdmin):
    list_display = ("title", "text", "is_active", "order")
    list_editable = ("is_active", "order")
    fields = ("title", "text", "is_active", "order")


@admin.register(Highlight)
class HighlightAdmin(FriendlyAdmin):
    list_display = ("icon", "title", "text", "is_active", "order")
    list_display_links = ("title",)
    list_editable = ("is_active", "order")
    fields = ("icon", "title", "text", "is_active", "order")


@admin.register(Testimonial)
class TestimonialAdmin(FriendlyAdmin):
    list_display = ("photo_preview", "name", "role", "stars_display", "is_active", "order")
    list_display_links = ("photo_preview", "name")
    list_editable = ("is_active", "order")
    fields = ("name", "role", "quote", "photo", "rating", "is_active", "order")

    @admin.display(description="")
    def photo_preview(self, obj):
        return _thumb(obj.photo.url if obj.photo else "", size=44)

    @admin.display(description="Rating")
    def stars_display(self, obj):
        return "★" * max(0, min(5, obj.rating))


@admin.register(ClientLogo)
class ClientLogoAdmin(FriendlyAdmin):
    list_display = ("logo_preview", "name", "is_active", "order")
    list_display_links = ("logo_preview", "name")
    list_editable = ("is_active", "order")
    fields = ("name", "logo", "url", "is_active", "order")

    @admin.display(description="")
    def logo_preview(self, obj):
        return _thumb(obj.logo.url if obj.logo else "", size=40)


# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------
@admin.register(ContactMessage)
class ContactMessageAdmin(PlainTitleMixin, admin.ModelAdmin):
    list_display = ("unread_dot", "name", "project_type", "budget", "short_message", "created", "reply")
    list_display_links = ("name",)
    list_filter = ("is_read", "project_type", "budget")
    search_fields = ("name", "email", "message")
    readonly_fields = ("name", "email_link", "project_type", "budget", "message", "created", "reply")
    fields = ("name", "email_link", "project_type", "budget", "message", "created", "reply")
    actions = ["mark_read", "mark_unread"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return obj is None  # opening a message is read-only

    def has_view_permission(self, request, obj=None):
        return True

    def change_view(self, request, object_id, form_url="", extra_context=None):
        ContactMessage.objects.filter(pk=object_id).update(is_read=True)
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.display(description="")
    def unread_dot(self, obj):
        return format_html('<span class="pf-dot {}" title="{}"></span>',
                           "" if obj.is_read else "pf-dot--new", "Read" if obj.is_read else "New")

    @admin.display(description="Message")
    def short_message(self, obj):
        return (obj.message[:70] + "…") if len(obj.message) > 70 else obj.message

    @admin.display(description="Email")
    def email_link(self, obj):
        return format_html('<a href="mailto:{0}">{0}</a>', obj.email)

    @admin.display(description="")
    def reply(self, obj):
        return format_html('<a class="pf-btn" href="mailto:{}?subject=Re:%20Your%20project%20enquiry">Reply ✉</a>', obj.email)

    @admin.action(description="Mark as read")
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark as unread")
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
