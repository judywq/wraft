from django.db import models
from django.db.models import Q


class AccessControlMixin(models.Model):
    """
    Abstract base model that adds creator-based access control.

    This mixin provides a created_by field and permission checking methods
    to implement access control based on who created the object. Models
    inheriting from this can control who can view, edit, or delete instances
    based on the creator relationship.
    """

    # Foreign key to the user who created this instance
    # Used for access control - users can typically only access objects they created
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="%(class)s_created",
    )

    class Meta:
        # Abstract model - won't create a database table
        abstract = True

    @classmethod
    def has_management_permission(cls, user):
        """
        Check if user has permission to manage this model type.

        Args:
            user: The user to check permissions for

        Returns:
            bool: True if user is superuser or has the specific management permission
        """
        # Superusers have all permissions
        if user.is_superuser:
            return True
        # Check for model-specific permission (e.g., 'myapp.can_manage_limited_forms')
        perm_name = f"{cls._meta.app_label}.can_manage_limited_{cls._meta.model_name}s"
        return user.has_perm(perm_name)


class AccessControlManagerMixin:
    """
    Mixin for model managers that implements creator-based access control.

    This mixin provides queryset filtering methods to restrict access to objects
    based on the creator relationship. It can be used with models that have
    a created_by field and optionally a managers relationship.

    Usage:
        class MyModelManager(AccessControlManagerMixin, models.Manager):
            pass

        class MyModel(models.Model):
            objects = MyModelManager()
    """

    # Name of the relationship field for managers (e.g., "managers" ManyToMany field)
    managers_relation_name = "managers"

    def accessible_by_user(self, user):
        """
        Returns queryset of objects that the user can access.

        Access is granted if:
        - User is a superuser (access to all objects)
        - User created the object (created_by=user)
        - User is in the managers relationship (if the model has one)

        Args:
            user: The user to check access for

        Returns:
            QuerySet: Filtered queryset of accessible objects, or empty queryset
                     if user is not authenticated
        """
        # Unauthenticated users get no access
        if not user or not user.is_authenticated:
            return self.none()
        # Superusers have access to everything
        if user.is_superuser:
            return self.all()

        # Base query: user can access objects they created
        query = Q(created_by=user)

        # Extend query to include manager access if applicable
        query = self.extend_manager_query(query, user)

        # Return distinct results in case user matches multiple conditions
        return self.filter(query).distinct()

    def extend_manager_query(self, query, user):
        """
        Extend the base query with manager access.

        Checks if the model has a managers relationship (ManyToMany or reverse
        ForeignKey) and adds it to the query if present.

        Args:
            query: The base Q object query to extend
            user: The user to check manager access for

        Returns:
            Q: Extended query object that includes manager access if applicable
        """
        # Check if model has managers relationship by examining:
        # 1. ManyToMany fields and regular fields
        # 2. Related objects (reverse relationships)
        has_managers = any(
            field.name == self.managers_relation_name
            for field in self.model._meta.many_to_many + self.model._meta.fields  # noqa: SLF001
        ) or any(
            # Reference: https://stackoverflow.com/a/52485429/1938012
            rel.name == self.managers_relation_name
            for rel in self.model._meta.related_objects  # noqa: SLF001
        )

        # If managers relationship exists, add it to the query
        # User can access objects where they are in the managers set
        if has_managers:
            query |= Q(managers=user)

        return query


class AccessControlAdminMixin:
    """
    Mixin for ModelAdmin that implements creator-based access control.

    This mixin restricts Django admin access based on the created_by field
    and management permissions. It ensures users can only see and modify
    objects they created (or have management permissions for).

    Usage:
        @admin.register(MyModel)
        class MyModelAdmin(AccessControlAdminMixin, admin.ModelAdmin):
            pass
    """

    def save_model(self, request, obj, form, change):
        """
        Override save to automatically set created_by on new objects.

        When creating a new object, automatically sets created_by to the
        current user. This ensures the creator relationship is always set.

        Args:
            request: The HTTP request object
            obj: The model instance being saved
            form: The form instance
            change: Boolean indicating if this is an update (True) or create (False)
        """
        # If creating new object, set the creator to the current user
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """
        Filter queryset to only show objects accessible by the user.

        Uses the accessible_by_user manager method to restrict the admin
        list view to only objects the user can access.

        Args:
            request: The HTTP request object

        Returns:
            QuerySet: Filtered queryset of accessible objects
        """
        return self.model.objects.accessible_by_user(request.user)

    def has_view_permission(self, request, obj=None):
        """
        Check if user has permission to view the model or a specific instance.

        - Superusers always have permission
        - Users with management permission can view if obj is None (list view)
        - For specific objects, user must have management permission AND
          the object must be in their accessible queryset

        Args:
            request: The HTTP request object
            obj: Optional model instance to check permission for

        Returns:
            bool: True if user has view permission, False otherwise
        """
        # Superusers can view everything
        if request.user.is_superuser:
            return True
        # Check if user has management permission for this model type
        if self.model.has_management_permission(request.user):
            # For list view (obj is None), grant permission
            if obj is None:
                return True
            # For specific object, check if it's in the user's accessible queryset
            return (
                self.model.objects.accessible_by_user(request.user)
                .filter(
                    id=obj.id,
                )
                .exists()
            )

        # No permission by default
        return False

    def has_add_permission(self, request):
        """
        Check if user has permission to add new instances.

        Delegates to has_view_permission with obj=None, meaning users
        who can view the list can also add new items.

        Args:
            request: The HTTP request object

        Returns:
            bool: True if user can add instances
        """
        return self.has_view_permission(request, obj=None)

    def has_change_permission(self, request, obj=None):
        """
        Check if user has permission to change an instance.

        Delegates to has_view_permission, meaning users who can view
        an object can also edit it.

        Args:
            request: The HTTP request object
            obj: Optional model instance to check permission for

        Returns:
            bool: True if user can change the instance
        """
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Check if user has permission to delete an instance.

        Delegates to has_view_permission, meaning users who can view
        an object can also delete it.

        Args:
            request: The HTTP request object
            obj: Optional model instance to check permission for

        Returns:
            bool: True if user can delete the instance
        """
        return self.has_view_permission(request, obj)
