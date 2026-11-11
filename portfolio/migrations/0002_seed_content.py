"""Fill the site with starter content. Everything here can be edited or deleted in /admin."""
from django.db import migrations

STATS = [(150, "+", "Projects Delivered"), (50, "+", "Happy Clients"), (10, "M+", "Views Generated"), (3, "+", "Years Experience")]

SERVICES = [
    ("film", "Video Editing", "Story-first cuts with rhythm, pacing and emotion — from raw footage to a finished piece people watch till the end."),
    ("phone", "Reels & Shorts", "Scroll-stopping vertical edits built for Instagram, YouTube Shorts and TikTok, with hooks in the first 2 seconds."),
    ("palette", "Color Grading", "Cinematic looks and consistent skin tones that give every frame a mood and a signature style."),
    ("spark", "Motion Graphics", "Animated titles, kinetic typography, logo reveals and lower thirds that make content feel premium."),
    ("pen", "Graphic Design", "Posters, social creatives, brand kits and YouTube thumbnails designed to grab attention and get clicks."),
    ("wave", "Sound Design", "Music sync, SFX, clean dialogue and mixing — because great video is 50% audio."),
]

TOOLS = [("Premiere Pro", "Pr", 95), ("After Effects", "Ae", 88), ("DaVinci Resolve", "Dv", 85), ("Photoshop", "Ps", 92),
         ("Illustrator", "Ai", 80), ("CapCut", "Cc", 90), ("Canva", "Cv", 90), ("Figma", "Fg", 75)]

PROCESS = [
    ("Discover", "We talk about your goals, audience, references and deadline."),
    ("Plan", "Footage review, story structure and a clear creative direction."),
    ("Create", "Editing, grading, motion and sound come together into the first cut."),
    ("Refine", "Your feedback goes in, revisions until every frame feels right."),
    ("Deliver", "Export in every format you need — 4K, vertical, square — on time."),
]

HIGHLIGHTS = [
    ("⚡", "Fast Turnaround", "Reels in 24–48 hrs, long-form on schedule."),
    ("♾", "Revisions Included", "We refine until it feels exactly right."),
    ("◎", "Platform Ready", "16:9, 9:16, 1:1 — exported for every platform."),
    ("🔒", "Safe & Confidential", "Your footage and ideas stay private."),
]

CATEGORIES = [("Commercial", "commercial"), ("Reels & Shorts", "reels"), ("Music Video", "music"),
              ("Wedding & Events", "wedding"), ("YouTube", "youtube"), ("Motion Graphics", "motion"),
              ("Graphic Design", "design")]

SAMPLE_PROJECTS = [
    ("Midnight Drive", "commercial", "Automotive Brand", 2026, True, "Edit · Color · Sound", "Premiere Pro, DaVinci Resolve",
     "A moody night-time car commercial with speed ramps, anamorphic flares and a teal-gold grade."),
    ("Hook in 2 Seconds", "reels", "Creator Series", 2026, False, "Edit · Captions", "Premiere Pro, CapCut",
     "Fast-paced vertical edits with captions, zoom cuts and sound design built for retention."),
    ("Golden Hour Vows", "wedding", "Wedding Film", 2025, False, "Edit · Color", "Premiere Pro, DaVinci Resolve",
     "An emotional cinematic wedding highlight cut to music with warm film-style colour."),
    ("Neon Pulse", "music", "Independent Artist", 2025, True, "Edit · VFX · Color", "After Effects, Premiere Pro",
     "Beat-synced music video with glitch transitions, light leaks and stylised colour."),
    ("Brand in Motion", "motion", "Startup Launch", 2025, False, "Motion Design", "After Effects, Illustrator",
     "Logo animation and explainer graphics for a product launch campaign."),
    ("Click-Worthy Thumbnails", "design", "YouTube Channels", 2026, False, "Design", "Photoshop, Figma",
     "High-CTR thumbnail system and social creatives designed for consistent branding."),
    ("Long-Form Storytelling", "youtube", "Vlog Channel", 2026, False, "Edit · Graphics", "Premiere Pro, After Effects",
     "Full YouTube episodes with B-roll, motion titles, music and retention-focused pacing."),
]


def seed(apps, schema_editor):
    get = apps.get_model
    get("portfolio", "SiteSettings").objects.get_or_create(pk=1)

    for i, (v, s, l) in enumerate(STATS):
        get("portfolio", "Stat").objects.create(value=v, suffix=s, label=l, order=i)
    for i, (icon, t, d) in enumerate(SERVICES):
        get("portfolio", "Service").objects.create(icon=icon, title=t, description=d, order=i)
    for i, (n, s, lv) in enumerate(TOOLS):
        get("portfolio", "Tool").objects.create(name=n, short=s, level=lv, order=i)
    for i, (t, x) in enumerate(PROCESS):
        get("portfolio", "ProcessStep").objects.create(title=t, text=x, order=i)
    for i, (ic, t, x) in enumerate(HIGHLIGHTS):
        get("portfolio", "Highlight").objects.create(icon=ic, title=t, text=x, order=i)

    Category = get("portfolio", "Category")
    cats = {slug: Category.objects.create(name=name, slug=slug, order=i) for i, (name, slug) in enumerate(CATEGORIES)}
    for i, (title, cat, client, year, featured, role, tools, desc) in enumerate(SAMPLE_PROJECTS):
        get("portfolio", "Project").objects.create(
            title=title, category=cats[cat], client=client, year=year, featured=featured,
            role=role, tools=tools, description=desc, order=i, is_sample=True,
        )


def unseed(apps, schema_editor):
    for m in ["Stat", "Service", "Tool", "ProcessStep", "Highlight", "Project", "Category", "SiteSettings"]:
        apps.get_model("portfolio", m).objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("portfolio", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
