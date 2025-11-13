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
            registration_form = AdminUserRegistrationForm(
                data=request.POST, staff_user=request.user
            )
            if registration_form.is_valid():
                registration_form.save()
                messages.success(request, "New user account has been created.")
                changelist_url = reverse("admin:users_user_changelist")
                return HttpResponseRedirect(changelist_url)
            form = registration_form
        else:
            # Display empty form
            form = AdminUserRegistrationForm(staff_user=request.user)

        # Prepare context for template
        admin_context = self.admin_site.each_context(request)
        context = {
            "form": form,
            "title": "Register New User",
            **admin_context,
        }
        template_path = "admin/users/user/user_register.html"
        return TemplateResponse(request, template_path, context)

    def _process_import_row(self, row_data, row_index, admin_user):
        """
        Process a single row from the import file.

        Args:
            row_data: Dictionary containing row data
            row_index: Index of the row (0-based)
            admin_user: The admin user performing the import

        Returns:
            tuple: (success: bool, error_message: str or None)
        """
        try:
            with transaction.atomic():
                # Prepare form data from Excel row
                # Use email as username if username is not provided
                user_email = row_data["email"]
                user_password = row_data["password"]
                user_name = row_data.get("name")
                user_username = row_data.get("username") or user_email

                form_data = {
                    "email": user_email,
                    "password": user_password,
                    "name": user_name,
                    "username": user_username,
                }

                # Create a temporary form to validate and save the user
                registration_form = AdminUserRegistrationForm(
                    data=form_data,
                    staff_user=admin_user,
                )

                if registration_form.is_valid():
                    registration_form.save()
                    return True, None
                else:
                    # Collect validation errors for this row
                    # row_index + 2 because Excel rows are 1-indexed and we skip header
                    error_text = registration_form.errors.as_text()
                    error_msg = f"Row {row_index + 2}: {error_text}"
                    return False, error_msg
        except (KeyError, ValueError) as exc:
            # Handle missing required columns or invalid data
            error_msg = f"Row {row_index + 2}: {exc!s}"
            return False, error_msg

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
            import_form = UserImportForm(request.POST, request.FILES)
            if import_form.is_valid():
                uploaded_file = request.FILES["file"]
                # Read Excel file into pandas DataFrame
                # keep_default_na=False prevents pandas from converting empty cells to NaN
                excel_dataframe = pd.read_excel(uploaded_file, keep_default_na=False)
                created_count = 0
                error_list = []

                # Process each row in the Excel file
                for row_idx, excel_row in excel_dataframe.iterrows():
                    row_dict = excel_row.to_dict()
                    success, error_message = self._process_import_row(
                        row_dict, row_idx, request.user
                    )
                    if success:
                        created_count += 1
                    else:
                        error_list.append(error_message)

                # Display success message if any users were created
                if created_count > 0:
                    success_msg = f"{created_count} user(s) imported successfully."
                    messages.success(request, success_msg)

                # Display error messages for failed rows
                for error_msg in error_list:
                    messages.error(request, error_msg)

                changelist_url = reverse("admin:users_user_changelist")
                return HttpResponseRedirect(changelist_url)
            form = import_form
        else:
            # Display empty form
            form = UserImportForm()

        # Prepare context for template
        admin_context = self.admin_site.each_context(request)
        context = {
            "form": form,
            "title": "Import Users",
            **admin_context,
        }
        template_path = "admin/users/user/user_import.html"
        return TemplateResponse(request, template_path, context)

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
        base_form_class = super().get_form(request, obj, **kwargs)
        current_admin_user = request.user

        # Return a lambda that automatically injects staff_user into form kwargs
        def form_factory(*args, **form_kwargs):
            form_kwargs["staff_user"] = current_admin_user
            return base_form_class(*args, **form_kwargs)

        return form_factory


# Unregister EmailAddress from admin to prevent direct editing
# Email addresses should be managed through the User model
admin.site.unregister(EmailAddress)
