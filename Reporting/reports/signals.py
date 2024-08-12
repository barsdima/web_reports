import os
from django.db import models
from django.dispatch import receiver
from reports.models import Report

# https://stackoverflow.com/a/16041527
# These two auto-delete files from filesystem when they are unneeded:

@receiver(models.signals.post_delete, sender=Report)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Report` object is deleted.
    """
    if instance.file_report:
        if os.path.isfile(instance.file_report.path):
            os.remove(instance.file_report.path)

@receiver(models.signals.pre_save, sender=Report)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `Report` object is updated
    with new file.
    """
    # the instance does not already exist in the DB (object is being created)
    if not instance.pk:
        return False

    try:
        old_file = Report.objects.get(pk=instance.pk).file_report
    except Report.DoesNotExist:
        return False

    # the uploaded file is being replaced
    if instance.file_report != old_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)