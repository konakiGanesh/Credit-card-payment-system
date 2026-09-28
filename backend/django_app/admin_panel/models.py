from django.conf import settings
from django.db import models


class AdminLog(models.Model):
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=60)
    target_type = models.CharField(max_length=60)
    target_id = models.CharField(max_length=60)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)