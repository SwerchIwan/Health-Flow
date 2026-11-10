from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Specialist, SpecialistApplication, Note, Blood, Pressure, BMI, Review, Rating


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'city', 'experience_years', 'price', 'is_published', 'is_catalog_demo')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'is_catalog_demo', 'specialty', 'city')
    search_fields = ('name', 'user__username', 'user__email', 'city', 'about')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('specialist', 'author', 'created_at')
    list_filter = ('specialist',)
    search_fields = ('specialist__name', 'author__username', 'text')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('specialist', 'user', 'rating')
    list_filter = ('rating', 'specialist')
    search_fields = ('specialist__name', 'user__username')


@admin.register(SpecialistApplication)
class SpecialistApplicationAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'specialization', 'status', 'created_at')
    list_filter = ('status', 'specialization')
    search_fields = ('first_name', 'last_name', 'contact', 'user__username')
    actions = ('approve_applications', 'reject_applications')

    @admin.action(description='Одобрить и опубликовать в каталоге')
    def approve_applications(self, request, queryset):
        approved = 0
        for application in queryset:
            if Specialist.objects.filter(user=application.user).exists():
                self.message_user(
                    request,
                    f'У пользователя {application.user} уже есть карточка специалиста.',
                    level=messages.WARNING,
                )
                continue
            Specialist.objects.create(
                user=application.user,
                name=f'{application.first_name} {application.last_name}'.strip(),
                specialty=application.specialization,
                about=application.additional_info,
                is_published=True,
            )
            application.status = 'approved'
            application.save(update_fields=['status'])
            approved += 1
        self.message_user(request, format_html('Одобрено заявок: <b>{}</b>', approved))

    @admin.action(description='Отклонить заявки')
    def reject_applications(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'Отклонено заявок: {updated}')


admin.site.register(Note)
admin.site.register(Blood)
admin.site.register(Pressure)
admin.site.register(BMI)
