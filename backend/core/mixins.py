from django.db import models
from django.db.models import Q


class AccessControlMixin(models.Model):
    """
    Abstract base model that adds creator-based access control.
    """

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="%(class)s_created",
    )

    class Meta:
        abstract = True

    @classmethod
    def has_management_permission(cls, user):
        """Check if user has permission to manage this model type."""
        if user.is_superuser:
            return True
        perm_name = f"{cls._meta.app_label}.can_manage_limited_{cls._meta.model_name}s"
        return user.has_perm(perm_name)


class AccessControlManagerMixin:
    """
    Mixin for model managers that implements creator-based access control.
    """

    managers_relation_name = "managers"

    def accessible_by_user(self, user):
        """Returns queryset of objects that the user can access."""
        if not user or not user.is_authenticated:
            return self.none()
        if user.is_superuser:
            return self.all()

        # Base query for creator access
        query = Q(created_by=user)

        query = self.extend_manager_query(query, user)

        return self.filter(query).distinct()

    def extend_manager_query(self, query, user):
        """Extend the base query with manager access."""
        # Check if model has managers relationship
        has_managers = any(
            field.name == self.managers_relation_name
            for field in self.model._meta.many_to_many + self.model._meta.fields  # noqa: SLF001
        ) or any(
            # https://stackoverflow.com/a/52485429/1938012
            rel.name == self.managers_relation_name
            for rel in self.model._meta.related_objects  # noqa: SLF001
        )

        # Add manager access if applicable
        if has_managers:
            query |= Q(managers=user)

        return query


class AccessControlAdminMixin:
    """
    Mixin for ModelAdmin that implements creator-based access control.
    """

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return self.model.objects.accessible_by_user(request.user)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if self.model.has_management_permission(request.user):
            if obj is None:
                return True
            return (
                self.model.objects.accessible_by_user(request.user)
                .filter(
                    id=obj.id,
                )
                .exists()
            )

        return False

    def has_add_permission(self, request):
        return self.has_view_permission(request, obj=None)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)
