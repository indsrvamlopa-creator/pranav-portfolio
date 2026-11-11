"""Put the starter tools into sensible groups."""
from django.db import migrations

GROUPS = {
    "Premiere Pro": "video", "CapCut": "video", "DaVinci Resolve": "color",
    "After Effects": "motion", "Photoshop": "design", "Illustrator": "design",
    "Canva": "design", "Figma": "design",
}


def forwards(apps, schema_editor):
    Tool = apps.get_model("portfolio", "Tool")
    for name, group in GROUPS.items():
        Tool.objects.filter(name=name).update(group=group)


class Migration(migrations.Migration):
    dependencies = [("portfolio", "0004_tool_groups")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
