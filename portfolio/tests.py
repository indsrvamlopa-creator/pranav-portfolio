import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from .models import Category, ContactMessage, Project, Service, SiteSettings, Testimonial, to_background_embed_url, to_embed_url
from .notify import build_payload, send_contact_email

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PortfolioTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin", "a@a.com", "pass12345")

    def test_home_renders_seeded_content(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Crafting")
        self.assertContains(r, "Video Editing")       # seeded service
        self.assertContains(r, "Midnight Drive")      # seeded project
        self.assertContains(r, "pranavrc1122@gmail.com")
        self.assertNotContains(r, 'id="testimonials"')  # hidden until added

    def test_site_settings_edits_show_on_site(self):
        s = SiteSettings.load()
        s.hero_gold = "Stories,"
        s.instagram = "https://instagram.com/pranav"
        s.save()
        r = self.client.get("/")
        self.assertContains(r, "Stories,")
        self.assertContains(r, "https://instagram.com/pranav")

    def test_hidden_items_not_shown(self):
        Service.objects.filter(title="Sound Design").update(is_active=False)
        self.assertNotContains(self.client.get("/"), "Sound Design</h3>")

    def test_admin_pages_load(self):
        self.client.force_login(self.admin)
        ContactMessage.objects.create(name="Ravi", email="r@r.com", message="Need a reel edit")
        for url in ["/admin/", "/admin/portfolio/project/", "/admin/portfolio/project/add/",
                    "/admin/portfolio/project/1/change/", "/admin/portfolio/category/",
                    "/admin/portfolio/service/", "/admin/portfolio/service/add/", "/admin/portfolio/stat/",
                    "/admin/portfolio/tool/", "/admin/portfolio/processstep/", "/admin/portfolio/highlight/",
                    "/admin/portfolio/testimonial/add/", "/admin/portfolio/clientlogo/add/",
                    "/admin/portfolio/contactmessage/", "/admin/auth/user/"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        dash = self.client.get("/admin/")
        self.assertContains(dash, "New project")
        self.assertContains(dash, 'class="pf-side__badge">1<')      # unread badge in sidebar
        self.assertContains(dash, "Recent projects")
        # sidebar highlights the current page
        self.assertContains(self.client.get("/admin/portfolio/service/"), 'class="pf-side__link is-active"')
        # each settings page jumps straight to its single form
        for name in ["herosettings", "aboutsettings", "contactsettings", "headingsettings"]:
            r = self.client.get(f"/admin/portfolio/{name}/")
            self.assertRedirects(r, f"/admin/portfolio/{name}/1/change/")
            self.assertEqual(self.client.get(f"/admin/portfolio/{name}/1/change/").status_code, 200)

    def test_upload_video_project_via_admin(self):
        self.client.force_login(self.admin)
        cat = Category.objects.get(slug="reels")
        video = SimpleUploadedFile("clip.mp4", b"\x00\x00\x00\x18ftypmp42", content_type="video/mp4")
        r = self.client.post("/admin/portfolio/project/add/", {
            "title": "My Real Reel", "category": cat.pk, "client": "Brand X", "year": 2026,
            "description": "Real work", "role": "Edit", "tools": "Premiere Pro",
            "video_file": video, "video_url": "", "preview_on_hover": "on",
            "thumbnail_url": "", "order": 0, "is_active": "on",
        })
        self.assertEqual(r.status_code, 302, r.content[:2000])
        p = Project.objects.get(title="My Real Reel")
        self.assertTrue(p.video_file.name.startswith("videos/"))
        home = self.client.get("/")
        self.assertContains(home, "My Real Reel")
        self.assertContains(home, f'data-video="{p.video_file.url}"')

    def test_settings_page_save(self):
        self.client.force_login(self.admin)
        url = "/admin/portfolio/headingsettings/1/change/"
        form = self.client.get(url).context["adminform"].form
        data = {k: (v if v is not None else "") for k, v in form.initial.items() if k in form.fields}
        data["services_gold"] = "pure magic."
        r = self.client.post(url, data)
        self.assertRedirects(r, url)
        self.assertEqual(SiteSettings.load().services_gold, "pure magic.")
        self.assertContains(self.client.get("/"), "pure magic.")

    def test_opening_message_marks_read(self):
        self.client.force_login(self.admin)
        m = ContactMessage.objects.create(name="A", email="a@a.com", message="hi")
        self.assertEqual(self.client.get(f"/admin/portfolio/contactmessage/{m.pk}/change/").status_code, 200)
        m.refresh_from_db()
        self.assertTrue(m.is_read)

    def test_embed_url_conversion(self):
        self.assertEqual(to_embed_url("https://youtu.be/abc?si=1"), "https://www.youtube.com/embed/abc?autoplay=1&rel=0")
        self.assertEqual(to_embed_url("https://www.youtube.com/watch?v=xyz&t=3"), "https://www.youtube.com/embed/xyz?autoplay=1&rel=0")
        self.assertEqual(to_embed_url("https://vimeo.com/12345"), "https://player.vimeo.com/video/12345?autoplay=1")
        self.assertEqual(to_embed_url("https://www.instagram.com/reel/C0de/?igsh=x"), "https://www.instagram.com/reel/C0de/embed")
        p = Project(title="t", video_url="https://youtu.be/abc")
        self.assertEqual(p.image, "https://i.ytimg.com/vi/abc/hqdefault.jpg")

    def test_showreel_autoplays_in_hero(self):
        r = self.client.get("/")
        self.assertNotContains(r, "monitor__reel")          # nothing uploaded yet
        s = SiteSettings.load()
        s.showreel_file = SimpleUploadedFile("reel.mp4", b"\x00\x00\x00\x18ftypmp42", content_type="video/mp4")
        s.save()
        r = self.client.get("/")
        self.assertContains(r, 'id="monReel"')
        self.assertContains(r, "autoplay muted loop playsinline", count=2)  # monitor + hero background
        self.assertContains(r, "Watch with sound")
        # a YouTube link also autoplays (muted, looping) when no file is uploaded
        s.showreel_file = ""
        s.showreel_url = "https://youtu.be/abc"
        s.save()
        r = self.client.get("/")
        self.assertContains(r, "embed/abc?autoplay=1&amp;mute=1&amp;loop=1&amp;playlist=abc")
        self.assertEqual(to_background_embed_url("https://drive.google.com/file/d/x/view"), "")

    def test_testimonial_section_appears(self):
        Testimonial.objects.create(name="Arjun", role="Founder", quote="Amazing edits!", rating=5)
        r = self.client.get("/")
        self.assertContains(r, 'id="testimonials"')
        self.assertContains(r, "Amazing edits!")

    def test_contact_form_saves(self):
        with patch("portfolio.views.notify_new_message") as notify:
            r = self.client.post("/", {"name": "A", "email": "a@b.com", "message": "Hi", "budget": "₹50,000+"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        notify.assert_called_once_with(ContactMessage.objects.get())
        # an incomplete form is not saved or emailed
        with patch("portfolio.views.notify_new_message") as notify:
            self.client.post("/", {"name": "A", "email": "", "message": "Hi"})
        notify.assert_not_called()

    @override_settings(BREVO_API_KEY="test-key", CONTACT_RECEIVER_EMAIL="owner@x.com",
                       BREVO_SENDER_EMAIL="owner@x.com", BREVO_SENDER_NAME="Portfolio")
    def test_brevo_email_payload(self):
        m = ContactMessage(name="Riya <b>", email="riya@x.com", project_type="Reels", budget="₹10k", message="Need\nedits")
        data = build_payload(m)
        self.assertEqual(data["to"], [{"email": "owner@x.com"}])
        self.assertEqual(data["replyTo"]["email"], "riya@x.com")
        self.assertEqual(data["subject"], "New enquiry from Riya <b> · Reels")
        self.assertIn("Riya &lt;b&gt;", data["htmlContent"])       # visitor input is escaped
        self.assertIn("Need<br>edits", data["htmlContent"])
        with patch("portfolio.notify.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.status = 201
            self.assertTrue(send_contact_email(m))
        req = urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://api.brevo.com/v3/smtp/email")
        self.assertEqual(req.get_header("Api-key"), "test-key")
        with override_settings(BREVO_API_KEY=""):
            self.assertFalse(send_contact_email(m))                 # no key → skipped, no crash

    def test_sample_note_only_for_staff(self):
        self.assertNotContains(self.client.get("/"), "Some projects are samples")
        self.client.force_login(self.admin)
        self.assertContains(self.client.get("/"), "Some projects are samples")
