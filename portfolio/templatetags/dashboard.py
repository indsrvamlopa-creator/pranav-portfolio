from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..models import ContactMessage, Project, Service, SiteSettings, Testimonial

register = template.Library()

# Simple line icons (24×24, stroke = currentColor)
ICONS = {
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "film": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M7 4v16M17 4v16M2 9h5M2 15h5M17 9h5M17 15h5"/>',
    "tag": '<path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
    "home": '<path d="M3 10.5L12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/>',
    "hash": '<path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18"/>',
    "monitor": '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "list": '<path d="M10 6h11M10 12h11M10 18h11M4 6h1v4M4 10h2M6 18H4c0-1 2-2 2-3s-1-1.5-2-1"/>',
    "award": '<circle cx="12" cy="8" r="6"/><path d="M8.2 13.4L7 22l5-3 5 3-1.2-8.6"/>',
    "type": '<path d="M4 7V4h16v3M9 20h6M12 4v16"/>',
    "star": '<path d="M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 6l-10 7L2 6"/>',
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2z"/>',
    "external": '<path d="M15 3h6v6M10 14L21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "video": '<path d="M22 8l-6 4 6 4V8z"/><rect x="2" y="6" width="14" height="12" rx="2"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>',
}


@register.simple_tag
def icon(name, size=18):
    return mark_safe(
        f'<svg class="pf-i" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS.get(name, "")}</svg>'
    )


def _u(name, *args):
    return reverse(f"admin:{name}", args=args)


@register.simple_tag(takes_context=True)
def sidebar_nav(context):
    request = context.get("request")
    path = request.path if request else ""
    unread = ContactMessage.objects.filter(is_read=False).count()

    def item(label, icon_name, url, badge=None, exact=False):
        active = path == url if exact else path.startswith(url)
        return {"label": label, "icon": icon_name, "url": url, "badge": badge, "active": active}

    p = "portfolio_"
    return [
        {"title": None, "items": [item("Dashboard", "grid", _u("index"), exact=True)]},
        {"title": "Portfolio", "items": [
            item("Projects", "film", _u(p + "project_changelist")),
            item("Categories", "tag", _u(p + "category_changelist")),
        ]},
        {"title": "Website", "items": [
            item("Home & videos", "home", _u(p + "herosettings_changelist")),
            item("About me", "user", _u(p + "aboutsettings_changelist")),
            item("Services", "briefcase", _u(p + "service_changelist")),
            item("Numbers", "hash", _u(p + "stat_changelist")),
            item("Software skills", "monitor", _u(p + "tool_changelist")),
            item("Work process", "list", _u(p + "processstep_changelist")),
            item("Why choose me", "award", _u(p + "highlight_changelist")),
            item("Section titles", "type", _u(p + "headingsettings_changelist")),
        ]},
        {"title": "Reviews", "items": [
            item("Testimonials", "star", _u(p + "testimonial_changelist")),
            item("Clients & brands", "users", _u(p + "clientlogo_changelist")),
        ]},
        {"title": "Inbox", "items": [
            item("Messages", "mail", _u(p + "contactmessage_changelist"), badge=unread or None),
            item("Contact & social", "phone", _u(p + "contactsettings_changelist")),
        ]},
    ]


@register.simple_tag
def dashboard_data():
    site = SiteSettings.load()
    unread = ContactMessage.objects.filter(is_read=False).count()
    p = "portfolio_"
    checklist = [
        {"done": not Project.objects.filter(is_sample=True).exists(),
         "label": "Replace sample projects with your real work", "url": _u(p + "project_changelist")},
        {"done": bool(site.showreel_file or site.showreel_url),
         "label": "Upload your showreel video", "url": _u(p + "herosettings_change", 1)},
        {"done": bool(site.profile_photo), "label": "Add your profile photo", "url": _u(p + "aboutsettings_change", 1)},
        {"done": bool(site.instagram or site.youtube or site.behance or site.linkedin),
         "label": "Add your social media links", "url": _u(p + "contactsettings_change", 1)},
        {"done": Testimonial.objects.exists(), "label": "Add a client testimonial", "url": _u(p + "testimonial_add")},
    ]
    return {
        "site": site,
        "stats": [
            {"label": "Live projects", "value": Project.objects.filter(is_active=True).count(),
             "icon": "film", "url": _u(p + "project_changelist")},
            {"label": "Unread messages", "value": unread, "icon": "mail",
             "url": _u(p + "contactmessage_changelist") + "?is_read__exact=0", "alert": unread > 0},
            {"label": "Services", "value": Service.objects.filter(is_active=True).count(),
             "icon": "briefcase", "url": _u(p + "service_changelist")},
            {"label": "Testimonials", "value": Testimonial.objects.filter(is_active=True).count(),
             "icon": "star", "url": _u(p + "testimonial_changelist")},
        ],
        "checklist": checklist,
        "checklist_done": sum(1 for c in checklist if c["done"]),
        "checklist_total": len(checklist),
        "quick": [
            {"label": "Add a project", "hint": "Upload a video or paste a link", "icon": "plus", "url": _u(p + "project_add")},
            {"label": "Showreel & headline", "hint": "Home page and videos", "icon": "video", "url": _u(p + "herosettings_change", 1)},
            {"label": "Edit about me", "hint": "Photo, bio and CV", "icon": "user", "url": _u(p + "aboutsettings_change", 1)},
            {"label": "Add a testimonial", "hint": "A review from a client", "icon": "star", "url": _u(p + "testimonial_add")},
        ],
        "recent_projects": Project.objects.select_related("category")[:5],
        "recent_messages": ContactMessage.objects.all()[:5],
        "projects_url": _u(p + "project_changelist"),
        "messages_url": _u(p + "contactmessage_changelist"),
        "add_project_url": _u(p + "project_add"),
    }


@register.filter
def initial(value):
    return (str(value) or "?")[:1].upper()
