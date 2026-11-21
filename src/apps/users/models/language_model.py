import uuid

from django.db import models


class AppLanguage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    language_code = models.CharField(max_length=10, unique=True)
    language_name = models.CharField(max_length=100)
    native_name = models.CharField(max_length=100, null=True, blank=True)  # noqa: DJ001
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "app_languages"
        ordering = ["display_order", "language_name"]

    def __str__(self) -> str:
        return self.language_code


class AppTranslation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    language = models.ForeignKey(
        AppLanguage,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    namespace = models.CharField(max_length=50)
    string_key = models.CharField(max_length=150)
    string_value = models.TextField()
    version = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "app_translations"
        constraints = [
            models.UniqueConstraint(
                fields=["language", "namespace", "string_key"],
                name="uq_translation_language_namespace_key",
            )
        ]

    def __str__(self) -> str:
        return f"{self.language.language_code}:{self.namespace}.{self.string_key}"
