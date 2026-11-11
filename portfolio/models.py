from django.db import models
from django.utils.text import slugify


def _lines(text):
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _youtube_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0].split("&")[0]
    if "youtube.com/watch" in url and "v=" in url:
        return url.split("v=")[1].split("&")[0]
    for marker in ("youtube.com/shorts/", "youtube.com/embed/"):
        if marker in url:
            return url.split(marker)[1].split("?")[0].split("/")[0]
    return ""


def to_background_embed_url(url):
    """Muted, looping, control-free player URL so a link can autoplay like a background video.
    Only YouTube and Vimeo support this; other links return ''."""
    if not url:
        return ""
    vid = _youtube_id(url)
    if vid:
        return (f"https://www.youtube.com/embed/{vid}?autoplay=1&mute=1&loop=1&playlist={vid}"
                f"&controls=0&playsinline=1&modestbranding=1&rel=0&disablekb=1&iv_load_policy=3")
    if "vimeo.com/" in url:
        vid = url.split("?")[0].rstrip("/").split("/")[-1]
        if vid.isdigit():
            return f"https://player.vimeo.com/video/{vid}?background=1&autoplay=1&muted=1&loop=1"
    return ""


def to_embed_url(url):
    """Convert a YouTube / Vimeo / Drive / Instagram share link into an embeddable player URL."""
    if not url:
        return ""
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[1].split("?")[0].split("&")[0]
        return f"https://www.youtube.com/embed/{vid}?autoplay=1&rel=0"
    if "youtube.com/watch" in url and "v=" in url:
        vid = url.split("v=")[1].split("&")[0]
        return f"https://www.youtube.com/embed/{vid}?autoplay=1&rel=0"
    if "youtube.com/shorts/" in url:
        vid = url.split("shorts/")[1].split("?")[0]
        return f"https://www.youtube.com/embed/{vid}?autoplay=1&rel=0"
    if "vimeo.com/" in url and "player.vimeo.com" not in url:
        vid = url.split("?")[0].rstrip("/").split("/")[-1]
        return f"https://player.vimeo.com/video/{vid}?autoplay=1"
    if "drive.google.com/file/d/" in url:
        fid = url.split("/file/d/")[1].split("/")[0]
        return f"https://drive.google.com/file/d/{fid}/preview"
    if "instagram.com/" in url:
        for kind in ("reel", "p", "tv"):
            marker = f"instagram.com/{kind}/"
            if marker in url:
                code = url.split(marker)[1].split("/")[0].split("?")[0]
                return f"https://www.instagram.com/{kind}/{code}/embed"
    return url


class OrderedModel(models.Model):
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first")
    is_active = models.BooleanField("Show on site", default=True)

    class Meta:
        abstract = True
        ordering = ["order", "id"]


# ---------------------------------------------------------------------------
# Site-wide settings (only one row)
# ---------------------------------------------------------------------------
class SiteSettings(models.Model):
    # Identity
    name = models.CharField(max_length=60, default="Pranav")
    title = models.CharField("Job title", max_length=100, default="Video Editor & Designer")
    seo_description = models.CharField(
        max_length=300, blank=True,
        default="Pranav is a Video Editor & Designer crafting cinematic edits, reels, motion graphics and designs that create real impact.",
    )

    # Hero
    hero_line1 = models.CharField("Headline line 1", max_length=40, default="Crafting")
    hero_gold = models.CharField("Headline gold word", max_length=40, default="Frames,")
    hero_line2 = models.CharField("Headline line 2", max_length=40, default="Creating")
    hero_outline = models.CharField("Headline outline word", max_length=40, default="Impact")
    hero_intro = models.CharField(
        max_length=200, default="turning raw footage into stories that stop the scroll and move people.",
    )
    rotating_roles = models.TextField(
        help_text="One per line — these rotate in the hero",
        default="Video Editor\nVisual Designer\nColorist\nMotion Artist\nStoryteller\nReels Specialist",
    )
    is_available = models.BooleanField("Available for work", default=True)
    availability_text = models.CharField(max_length=80, default="Available for freelance projects")
    hero_bg_video = models.FileField(
        "Hero background video", upload_to="videos/", blank=True,
        help_text="Optional muted looping video behind the headline (MP4, keep it under ~15 MB)",
    )
    showreel_url = models.URLField(blank=True, help_text="YouTube / Vimeo / Drive link to your showreel")
    showreel_file = models.FileField(upload_to="videos/", blank=True, help_text="Or upload the showreel MP4")
    based_in = models.CharField(max_length=60, default="India")
    specialty = models.CharField(max_length=60, default="Edit · Color · Motion")
    response_time = models.CharField(max_length=60, default="Within 24 hrs")

    marquee_items = models.TextField(
        "Scrolling banner words", help_text="One per line",
        default="Video Editing\nColor Grading\nMotion Graphics\nReels & Shorts\nGraphic Design\nSound Design\nThumbnails\nStorytelling",
    )

    # About
    about_title = models.CharField(max_length=80, default="Every frame has a")
    about_gold = models.CharField(max_length=40, default="purpose.")
    about_text = models.TextField(
        help_text="Leave an empty line between paragraphs",
        default=(
            "I'm Pranav, a video editor and designer who believes great content isn't just seen — it's felt. "
            "I blend storytelling, rhythm and visual design to create edits that hook viewers in the first second "
            "and hold them until the last.\n\n"
            "From brand commercials and music videos to viral reels, YouTube content and wedding films — I handle "
            "the full post-production pipeline: editing, color grading, motion graphics, sound design and the "
            "thumbnails that get the click."
        ),
    )
    about_tags = models.TextField(
        help_text="One per line",
        default="Storytelling\nFast Turnaround\nPixel Perfect\nTrend Aware\nClient Focused",
    )
    profile_photo = models.FileField(upload_to="profile/", blank=True, help_text="Portrait shown in the About section")
    badge_number = models.CharField("Floating badge number", max_length=10, default="3+")
    badge_label = models.CharField("Floating badge label", max_length=40, default="Years of Editing")
    resume = models.FileField("Resume / CV (PDF)", upload_to="resume/", blank=True)

    # Section headings
    services_title = models.CharField(max_length=80, default="Services that make your")
    services_gold = models.CharField(max_length=40, default="content shine.")
    work_title = models.CharField(max_length=80, default="Projects that speak for")
    work_gold = models.CharField(max_length=40, default="themselves.")
    skills_title = models.CharField(max_length=80, default="Industry tools,")
    skills_gold = models.CharField(max_length=40, default="mastered.")
    process_title = models.CharField(max_length=80, default="From raw footage to")
    process_gold = models.CharField(max_length=40, default="final cut.")
    testimonials_title = models.CharField(max_length=80, default="Words from")
    testimonials_gold = models.CharField(max_length=40, default="happy clients.")
    cta_title = models.CharField("Call-to-action title", max_length=80, default="Got footage?")
    cta_gold = models.CharField("Call-to-action gold line", max_length=80, default="Let's make it unforgettable.")
    cta_button = models.CharField(max_length=40, default="Start a Project")

    # Contact
    contact_title = models.CharField(max_length=80, default="Let's create something")
    contact_gold = models.CharField(max_length=40, default="iconic.")
    contact_intro = models.CharField(
        max_length=250,
        default="Have a project, a brand, or just a wild idea? Drop a message — I usually reply within 24 hours.",
    )
    email = models.EmailField(default="pranavrc1122@gmail.com")
    phone = models.CharField(max_length=30, default="+91 85085 63679")
    whatsapp = models.CharField(
        "WhatsApp number", max_length=20, default="918508563679",
        help_text="Digits only, with country code (e.g. 918508563679)",
    )
    whatsapp_message = models.CharField(
        max_length=200, default="Hi Pranav, I saw your portfolio and want to discuss a project.",
    )
    location = models.CharField(max_length=80, default="India · Available Worldwide")
    project_types = models.TextField(
        "Contact form: project types", help_text="One per line",
        default="Reels / Shorts\nYouTube Video\nCommercial / Ad\nMusic Video\nWedding / Event\nMotion Graphics\nGraphic Design\nOther",
    )
    budgets = models.TextField(
        "Contact form: budgets", help_text="One per line",
        default="Under ₹5,000\n₹5,000 – ₹15,000\n₹15,000 – ₹50,000\n₹50,000+\nLet's discuss",
    )

    # Socials
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    behance = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    vimeo = models.URLField(blank=True)
    twitter = models.URLField("X / Twitter", blank=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def tagline(self):
        return f"{self.hero_line1} {self.hero_gold} {self.hero_line2} {self.hero_outline}"

    @property
    def roles_list(self):
        return _lines(self.rotating_roles)

    @property
    def marquee_list(self):
        return _lines(self.marquee_items)

    @property
    def about_paragraphs(self):
        return [p.strip() for p in self.about_text.split("\n\n") if p.strip()]

    @property
    def about_tags_list(self):
        return _lines(self.about_tags)

    @property
    def project_types_list(self):
        return _lines(self.project_types)

    @property
    def budgets_list(self):
        return _lines(self.budgets)

    @property
    def phone_link(self):
        return "".join(ch for ch in self.phone if ch.isdigit() or ch == "+")

    @property
    def showreel_embed(self):
        return to_embed_url(self.showreel_url)

    @property
    def showreel_bg_embed(self):
        """Autoplaying muted version of the showreel link (YouTube / Vimeo only)."""
        return to_background_embed_url(self.showreel_url)

    @property
    def has_auto_reel(self):
        return bool(self.showreel_file or self.showreel_bg_embed)

    @property
    def socials(self):
        pairs = [("Instagram", self.instagram), ("YouTube", self.youtube), ("Behance", self.behance),
                 ("LinkedIn", self.linkedin), ("Vimeo", self.vimeo), ("X", self.twitter)]
        return [(n, u) for n, u in pairs if u]


# Friendly admin pages that all edit the same single settings row.
class HeroSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = verbose_name_plural = "Home page & videos"


class AboutSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = verbose_name_plural = "About me"


class ContactSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = verbose_name_plural = "Contact & social links"


class HeadingSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = verbose_name_plural = "Section titles"


# ---------------------------------------------------------------------------
# Repeating content
# ---------------------------------------------------------------------------
class Stat(OrderedModel):
    value = models.PositiveIntegerField()
    suffix = models.CharField(max_length=5, blank=True, help_text="e.g. +, M+, K")
    label = models.CharField(max_length=60)

    class Meta(OrderedModel.Meta):
        verbose_name = "Number counter"
        verbose_name_plural = "Number counters"

    def __str__(self):
        return f"{self.value}{self.suffix} {self.label}"


class Service(OrderedModel):
    ICONS = [
        ("film", "Film / Editing"), ("phone", "Phone / Reels"), ("palette", "Palette / Color"),
        ("spark", "Spark / Motion"), ("pen", "Pen / Design"), ("wave", "Waveform / Sound"),
        ("camera", "Camera / Shoot"), ("layers", "Layers / VFX"), ("image", "Image / Thumbnail"),
        ("play", "Play / YouTube"),
    ]
    title = models.CharField(max_length=60)
    description = models.TextField()
    icon = models.CharField(max_length=20, choices=ICONS, default="film")
    starting_price = models.CharField(max_length=40, blank=True, help_text="Optional, e.g. From ₹2,000")

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.title


class Tool(OrderedModel):
    GROUPS = [
        ("video", "Video Editing"),
        ("color", "Color"),
        ("motion", "Motion & VFX"),
        ("design", "Design"),
        ("audio", "Audio"),
        ("other", "Other"),
    ]
    name = models.CharField(max_length=60)
    short = models.CharField("Badge letters", max_length=3, help_text="e.g. Pr, Ae — shown if no logo is uploaded")
    level = models.PositiveIntegerField(default=80, help_text="0–100")
    group = models.CharField(max_length=10, choices=GROUPS, default="video",
                             help_text="Used for the filter tabs in the Toolkit section")
    logo = models.FileField(upload_to="tools/", blank=True,
                            help_text="Optional square logo (PNG/SVG). Badge letters are used if empty.")
    years = models.CharField("Experience", max_length=20, blank=True, help_text="Optional, e.g. 3 yrs")

    class Meta(OrderedModel.Meta):
        verbose_name = "Software skill"
        verbose_name_plural = "Software skills"

    def __str__(self):
        return self.name


class ProcessStep(OrderedModel):
    title = models.CharField(max_length=60)
    text = models.CharField(max_length=200)

    class Meta(OrderedModel.Meta):
        verbose_name = "Work process step"
        verbose_name_plural = "Work process steps"

    def __str__(self):
        return self.title


class Highlight(OrderedModel):
    icon = models.CharField(max_length=4, default="✦", help_text="An emoji or symbol")
    title = models.CharField(max_length=60)
    text = models.CharField(max_length=160)

    class Meta(OrderedModel.Meta):
        verbose_name = "Why-choose-me point"
        verbose_name_plural = "Why-choose-me points"

    def __str__(self):
        return self.title


class Testimonial(OrderedModel):
    name = models.CharField(max_length=80)
    role = models.CharField(max_length=100, blank=True, help_text="e.g. Founder, XYZ Studio")
    quote = models.TextField()
    photo = models.FileField(upload_to="testimonials/", blank=True)
    rating = models.PositiveSmallIntegerField(default=5, help_text="1–5 stars")

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        return self.name

    @property
    def stars(self):
        return range(max(0, min(5, self.rating)))


class ClientLogo(OrderedModel):
    name = models.CharField(max_length=80)
    logo = models.FileField(upload_to="clients/", blank=True, help_text="PNG/SVG with transparent background works best")
    url = models.URLField(blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Client / brand"
        verbose_name_plural = "Clients / brands"

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
class Category(OrderedModel):
    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = "Project category"
        verbose_name_plural = "Project categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or f"cat-{self.pk or ''}"
        super().save(*args, **kwargs)


class Project(OrderedModel):
    title = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="projects")
    client = models.CharField(max_length=120, blank=True)
    year = models.PositiveIntegerField(blank=True, null=True)
    description = models.TextField(blank=True)
    role = models.CharField(max_length=200, blank=True, help_text="e.g. Edit · Color Grade · Sound Design")
    tools = models.CharField(max_length=200, blank=True, help_text="Comma separated, e.g. Premiere Pro, After Effects")
    thumbnail = models.FileField(upload_to="thumbnails/", blank=True)
    thumbnail_url = models.URLField(blank=True, help_text="Use instead of uploading a thumbnail")
    video_file = models.FileField(upload_to="videos/", blank=True, help_text="Upload an MP4 / WebM")
    video_url = models.URLField(blank=True, help_text="Or paste a YouTube, Vimeo, Instagram or Google Drive link")
    preview_on_hover = models.BooleanField(
        default=True, help_text="Play the uploaded video silently when the card is hovered",
    )
    featured = models.BooleanField(default=False, help_text="Shows as a large card")
    is_sample = models.BooleanField(default=False, editable=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created"]

    def __str__(self):
        return self.title

    @property
    def image(self):
        if self.thumbnail:
            return self.thumbnail.url
        if self.thumbnail_url:
            return self.thumbnail_url
        vid = self._youtube_id()
        if vid:
            return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        return ""

    def _youtube_id(self):
        url = self.video_url or ""
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        if "youtube.com/watch" in url and "v=" in url:
            return url.split("v=")[1].split("&")[0]
        if "youtube.com/shorts/" in url:
            return url.split("shorts/")[1].split("?")[0]
        return ""

    @property
    def tool_list(self):
        return [t.strip() for t in self.tools.split(",") if t.strip()]

    @property
    def embed_url(self):
        return to_embed_url(self.video_url)


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    project_type = models.CharField(max_length=60, blank=True)
    budget = models.CharField(max_length=60, blank=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.name} — {self.project_type or 'Enquiry'}"
