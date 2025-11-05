from django.apps import apps
from django.contrib.admin import SimpleListFilter


class UserListFilter(SimpleListFilter):
    title = "User"
    parameter_name = "created_by"

    def lookups(self, request, model_admin):
        User = apps.get_model("users", "User")
        if request.user.is_superuser:
            users = User.objects.all()
        else:
            users = [
                request.user,
                *list(User.objects.accessible_by_user(request.user)),
            ]

        return [(user.username, user.name) for user in users]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(created_by__username=self.value())
        return queryset
