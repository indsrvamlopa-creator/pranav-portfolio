from django.contrib import messages
from django.shortcuts import redirect, render

from .models import (
    Category, ClientLogo, ContactMessage, Highlight, ProcessStep, Project,
    Service, SiteSettings, Stat, Testimonial, Tool,
)
from .notify import notify_new_message


def home(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()
        if name and email and message:
            msg = ContactMessage.objects.create(
                name=name[:120],
                email=email[:254],
                project_type=request.POST.get("project_type", "").strip()[:60],
                budget=request.POST.get("budget", "").strip()[:60],
                message=message,
            )
            notify_new_message(msg)   # emails it to you via Brevo
            messages.success(request, "Thanks! Your message landed. I'll get back to you within 24 hours.")
        else:
            messages.error(request, "Please fill in your name, email and message.")
        return redirect("/#contact")

    projects = list(Project.objects.filter(is_active=True).select_related("category"))
    used = {p.category_id for p in projects}
    categories = [c for c in Category.objects.filter(is_active=True) if c.id in used]

    tools = list(Tool.objects.filter(is_active=True))
    group_labels = dict(Tool.GROUPS)
    tool_groups = []
    for t in tools:
        if t.group not in [g[0] for g in tool_groups]:
            tool_groups.append((t.group, group_labels.get(t.group, t.group)))

    context = {
        "site": SiteSettings.load(),
        "stats": Stat.objects.filter(is_active=True),
        "services": Service.objects.filter(is_active=True),
        "tools": tools,
        "tool_groups": tool_groups,
        "orbit_inner": tools[0::2][:6],   # tools split over two orbit rings
        "orbit_outer": tools[1::2][:8],
        "process": ProcessStep.objects.filter(is_active=True),
        "highlights": Highlight.objects.filter(is_active=True),
        "testimonials": Testimonial.objects.filter(is_active=True),
        "clients": ClientLogo.objects.filter(is_active=True),
        "projects": projects,
        "categories": categories,
        "has_samples": any(p.is_sample for p in projects),
    }
    return render(request, "portfolio/home.html", context)


def media_serve(request, path):
    """Development-only media server that understands HTTP Range requests,
    so uploaded videos can be seeked/scrubbed (Django's built-in one can't).
    In production your web server (nginx, etc.) serves /media/ directly."""
    import mimetypes
    import os
    import re

    from django.conf import settings
    from django.http import FileResponse, Http404, HttpResponse
    from django.utils._os import safe_join

    try:
        full = safe_join(settings.MEDIA_ROOT, path)
    except Exception:
        raise Http404
    if not os.path.isfile(full):
        raise Http404
    size = os.path.getsize(full)
    ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
    m = re.match(r"bytes=(\d*)-(\d*)$", request.headers.get("Range", "").strip())
    if not m or (m.group(1) == "" and m.group(2) == ""):
        resp = FileResponse(open(full, "rb"), content_type=ctype)
        resp["Accept-Ranges"] = "bytes"
        return resp
    if m.group(1) == "":                      # suffix range: last N bytes
        start, end = max(0, size - int(m.group(2))), size - 1
    else:
        start = int(m.group(1))
        end = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
    if start >= size or start > end:
        resp = HttpResponse(status=416)
        resp["Content-Range"] = f"bytes */{size}"
        return resp
    with open(full, "rb") as f:
        f.seek(start)
        data = f.read(end - start + 1)
    resp = HttpResponse(data, status=206, content_type=ctype)
    resp["Content-Range"] = f"bytes {start}-{end}/{size}"
    resp["Accept-Ranges"] = "bytes"
    resp["Content-Length"] = str(len(data))
    return resp
