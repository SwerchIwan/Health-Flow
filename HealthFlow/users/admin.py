from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    # Поля, которые будут отображаться в админке при просмотре списка пользователей
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'phone', 'subscription', 'photo')

    # Поля, которые будут использоваться при фильтрации списка пользователей
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'subscription')

    # Поля, которые будут отображаться на форме редактирования пользователя
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'subscription', 'photo')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Поля, которые будут использоваться при создании нового пользователя через админку
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
            'username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'phone', 'subscription', 'photo')}
         ),
    )

    # Поля, которые будут использоваться для поиска пользователей
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('username',)


# Зарегистрируйте вашу модель User с пользовательским классом UserAdmin
admin.site.register(User, UserAdmin)
