from django.contrib import admin

from subscription.models import Plan, Payment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price', 'duration_days', 'is_active', 'sort_order')
    list_editable = ('price', 'duration_days', 'is_active', 'sort_order')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'status', 'card_mask', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'plan', 'amount', 'duration_days', 'card_mask', 'status', 'created_at')
