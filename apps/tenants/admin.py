from django.contrib import admin
from .models import SubscriptionPlan, Institution, InstitutionSubscription, SubscriptionApplication, AddOn, GrantedAddOn

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price', 'original_price', 'max_competitions', 'max_contestants', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    prepopulated_fields = {'code': ('name',)}


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'price', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    prepopulated_fields = {'code': ('name',)}


@admin.register(GrantedAddOn)
class GrantedAddOnAdmin(admin.ModelAdmin):
    list_display = ('institution', 'add_on', 'is_active', 'granted_at')
    list_filter = ('is_active', 'add_on')
    search_fields = ('institution__name', 'add_on__name')


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'is_public_suspended', 'email', 'phone', 'is_demo', 'created_at')
    list_filter = ('status', 'is_public_suspended', 'is_demo', 'created_at')
    search_fields = ('name', 'slug', 'email', 'phone')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(InstitutionSubscription)
class InstitutionSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('institution', 'plan', 'additional_work_charge', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'plan')
    search_fields = ('institution__name', 'plan__name')


@admin.register(SubscriptionApplication)
class SubscriptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('institution_name', 'desired_plan', 'contact_name', 'email', 'phone', 'payment_utr', 'status', 'submitted_at')
    list_filter = ('status', 'desired_plan', 'submitted_at')
    search_fields = ('institution_name', 'contact_name', 'email', 'phone', 'payment_utr')
