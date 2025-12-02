from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # Default queryset excludes soft-deleted records
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        # Method to get all records, including soft-deleted ones
        return super().get_queryset()

    def deleted_only(self):
        # Method to get only soft-deleted records
        return super().get_queryset().filter(is_deleted=True)


class BaseModel(models.Model):
    """
    Base model to include common fields and methods for all models,
    including soft delete functionality.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)

    # Activation & Publication Status
    is_active = models.BooleanField(default=True, help_text="Whether this item is active and usable")
    is_published = models.BooleanField(default=False, help_text="Whether this item is published/visible")

    # Soft Delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Model Managers
    objects = SoftDeleteManager()  # Default manager filters out deleted items
    all_objects = models.Manager() # Manager to access all items, including deleted

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete the object."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)

    def restore(self, using=None):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the object."""
        super().delete(using=using, keep_parents=keep_parents)