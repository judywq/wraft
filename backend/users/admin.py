"""
Django admin configuration for User model.

This module configures the Django admin interface for user management,
including custom views for user registration and bulk import functionality.
"""
import pandas as pd
from allauth.account.decorators import secure_admin_login
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import admin as auth_admin
from django.db import transaction
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from backend.common.mixins import AccessControlAdminMixin

from .forms import AdminUserRegistrationForm
from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .forms import UserImportForm
from .models import User

# Force django-allauth authentication for admin if configured
# This ensures admin login goes through the allauth workflow
if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


@admin.register(User)
class UserAdmin(AccessControlAdminMixin, auth_admin.UserAdmin):
    """
    Admin interface for User model.

    This admin class provides:
    - Access control based on created_by field
    - Custom views for user registration and bulk import
    - Permission-based field visibility
    - Custom list display based on user permissions
    """

    # Forms used for editing and creating users
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    # Fields that can be searched in the admin list view
    search_fields = [
        "username",
        "email",
        "name",
    ]
    # Fields displayed as horizontal filter widgets
    filter_horizontal = ["groups", "user_permissions"]

    def get_list_display(self, request):
        """
        Get the list of fields to display in the admin list view.

        Superusers see more fields including created_by, staff status, etc.
        Regular users see only basic information.

        Args:
            request: The HTTP request object

        Returns:
            list: List of field names to display
        """
        if request.user.is_superuser:
            # Superusers see all fields including permissions and metadata
            return [
                "username",
                "email",
                "name",
                "created_by",
                "is_staff",
                "is_superuser",
                "date_joined",
            ]
        # Regular users see only basic information
        return ["username", "email", "name", "date_joined"]

    def get_fieldsets(self, request, obj=None):
        """
        Get the fieldsets to display in the admin form.

        Fieldsets are organized based on user permissions:
        - Superusers see all fields including permissions and metadata
        - Users with management permission see only basic fields
        - Others see nothing (handled by AccessControlAdminMixin)

        Args:
            request: The HTTP request object
            obj: The user object being edited (None for new users)

        Returns:
            tuple: Fieldsets configuration
        """
        fieldsets = []
        if request.user.is_superuser:
            # Superusers see all fields organized in sections
            fieldsets = (
                (None, {"fields": ("username", "password")}),
                (_("Personal info"), {"fields": ("name", "email")}),
                (
                    _("Permissions"),
                    {
                        "fields": (
                            "is_active",
                            "is_staff",
                            "is_superuser",
                            "groups",
                            "user_permissions",
                        ),
                    },
                ),
                (
                    _("Meta data"),
                    {"fields": ("created_by", "last_login", "date_joined")},
                ),
            )
        elif request.user.has_perm("users.can_manage_limited_users"):
            # Users with management permission see only basic fields
            fieldsets = (
                (None, {"fields": ("username", "password")}),
                (_("Personal info"), {"fields": ("name", "email")}),
            )
        return fieldsets

    def get_list_filter(self, request):
        """
        Get the list of filters to display in the admin list view.

        Only superusers see filters for permissions and created_by.

        Args:
            request: The HTTP request object

        Returns:
            list: List of field names to use as filters
        """
        if request.user.is_superuser:
            # Superusers can filter by permissions and creator
            return [
                "is_active",
                "is_staff",
                "is_superuser",
                "created_by",
            ]
        # Regular users see no filters
        return []

    def get_queryset(self, request):
        """
        Get the queryset of users to display in the admin list.

        Uses AccessControlManagerMixin to filter users based on access control.

        Args:
            request: The HTTP request object

        Returns:
            QuerySet: Filtered queryset of accessible users
        """
        return self.model.objects.accessible_by_user(request.user)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Disable the default add user button.

        We use custom views (user_register_view) instead of the default
        add functionality to have more control over user creation.

        Args:
            request: The HTTP request object

        Returns:
            bool: Always False to disable default add button
        """
        return False

    def get_urls(self):
        """
        Add custom URLs for user registration and import.

        Returns:
            list: List of URL patterns including custom views
        """
        urls = super().get_urls()
        # Custom URLs for user registration and bulk import
        custom_urls = [
            path(
                "register/",
                self.admin_site.admin_view(self.user_register_view),
                name="user_register",
            ),
            path(
                "import/",
                self.admin_site.admin_view(self.user_import_view),
                name="user_import",
            ),
        ]
        # Custom URLs come first, then default admin URLs
        return custom_urls + urls

    def user_register_view(self, request):
        """
        View for manually registering a new user.

        This view provides a form for admin users to manually create
        a new user account. It handles both GET (display form) and
        POST (process form submission) requests.

        Args:
            request: The HTTP request object

        Returns:
            TemplateResponse: Rendered registration form template
            HttpResponseRedirect: Redirect to user list after successful registration
        """
        if request.method == "POST":
            # Process form submission
            form = AdminUserRegistrationForm(data=request.POST, staff_user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "User registered successfully.")
                return HttpResponseRedirect(reverse("admin:users_user_changelist"))
        else:
            # Display empty form
            form = AdminUserRegistrationForm(staff_user=request.user)

        # Prepare context for template
        context = {
            "form": form,
            "title": "Register New User",
            **self.admin_site.each_context(request),
        }
        return TemplateResponse(request, "admin/users/user/user_register.html", context)

    def user_import_view(self, request):
        """
        View for bulk importing users from an Excel file.

        This view processes an Excel file containing user data and creates
        multiple user accounts. Each row in the Excel file represents one user.
        Errors are collected and displayed to the user after processing.

        Args:
            request: The HTTP request object

        Returns:
            TemplateResponse: Rendered import form template
            HttpResponseRedirect: Redirect to user list after import (with messages)
        """
        if request.method == "POST":
            # Process file upload
            form = UserImportForm(request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES["file"]
                # Read Excel file into pandas DataFrame
                # keep_default_na=False prevents pandas from converting empty cells to NaN
                df_data = pd.read_excel(file, keep_default_na=False)
                success_count = 0
                errors = []

                # Process each row in the Excel file
                for idx, row in df_data.iterrows():
                    try:
                        # Use transaction to ensure atomicity per user
                        # If one user fails, others can still succeed
                        with transaction.atomic():
                            # Convert row to dictionary and handle missing columns
                            row_dict = row.to_dict()

                            # Prepare form data from Excel row
                            # Use email as username if username is not provided
                            form_data = {
                                "email": row_dict["email"],
                                "password": row_dict["password"],
                                "name": row_dict.get("name"),
                                "username": row_dict.get("username")
                                or row_dict["email"],
                            }
                            # Create a temporary form to validate and save the user
                            temp_form = AdminUserRegistrationForm(
                                data=form_data,
                                staff_user=request.user,
                            )
                            if temp_form.is_valid():
                                temp_form.save()
                                success_count += 1
                            else:
                                # Collect validation errors for this row
                                # idx + 2 because Excel rows are 1-indexed and we skip header
                                errors.append(
                                    f"Row {idx + 2}: {temp_form.errors.as_text()}",
                                )
                    except (KeyError, ValueError) as e:
                        # Handle missing required columns or invalid data
                        msg = f"Row {idx + 2}: {e!s}"
                        errors.append(msg)

                # Display success message if any users were created
                if success_count > 0:
                    messages.success(
                        request,
                        f"Successfully created {success_count} users.",
                    )
                # Display error messages for failed rows
                if errors:
                    for error in errors:
                        messages.error(request, error)
                return HttpResponseRedirect(reverse("admin:users_user_changelist"))
        else:
            # Display empty form
            form = UserImportForm()

        # Prepare context for template
        context = {
            "form": form,
            "title": "Import Users",
            **self.admin_site.each_context(request),
        }
        return TemplateResponse(request, "admin/users/user/user_import.html", context)

    def changelist_view(self, request, extra_context=None):
        """
        Override changelist view to add custom action buttons.

        Adds context variables to show "Register User" and "Import Users"
        buttons in the admin list view.

        Args:
            request: The HTTP request object
            extra_context: Additional context to pass to template

        Returns:
            TemplateResponse: Rendered changelist template
        """
        extra_context = extra_context or {}
        # Enable custom action buttons in the template
        extra_context["show_register_button"] = True
        extra_context["show_user_import_button"] = True
        return super().changelist_view(request, extra_context=extra_context)

    def get_form(self, request, obj=None, change=False, **kwargs):  # noqa: FBT002
        """
        Override get_form to inject staff_user into form initialization.

        This ensures that forms always receive the current admin user
        as staff_user, which is needed for access control.

        Args:
            request: The HTTP request object
            obj: The user object being edited (None for new users)
            change: Whether this is an edit (True) or create (False) operation
            **kwargs: Additional keyword arguments

        Returns:
            Form class: Form class with staff_user automatically injected
        """
        form_class = super().get_form(request, obj, **kwargs)
        # Return a lambda that automatically injects staff_user into form kwargs
        return lambda *args, **k: form_class(*args, **{**k, "staff_user": request.user})


# Unregister EmailAddress from admin to prevent direct editing
# Email addresses should be managed through the User model
admin.site.unregister(EmailAddress)
