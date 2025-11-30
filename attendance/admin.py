from django.contrib import admin
from .models import Member, NewMember, Attendance


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'name', 'role', 'phone_number', 'department', 'status_complete', 'created_at')
    list_filter = ('role', 'status_complete', 'department', 'gender')
    search_fields = ('name', 'serial_number', 'phone_number', 'parent_name')
    ordering = ('-created_at',)
    readonly_fields = ('serial_number', 'created_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('serial_number', 'name', 'role', 'gender', 'age')
        }),
        ('Contact Info', {
            'fields': ('phone_number', 'parent_name', 'parent_phone_number')
        }),
        ('Work Details', {
            'fields': ('department',),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('status_complete', 'created_at')
        }),
    )
    
    list_per_page = 50


@admin.register(NewMember)
class NewMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'phone_number', 'date_joined')
    list_filter = ('role', 'date_joined')
    search_fields = ('name', 'phone_number')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined',)
    date_hierarchy = 'date_joined'
    
    list_per_page = 50


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('member', 'date', 'service_type', 'time_marked', 'marked_by')
    list_filter = ('service_type', 'date', 'member__role')
    search_fields = ('member__name', 'member__serial_number', 'marked_by')
    ordering = ('-date', '-time_marked')
    readonly_fields = ('time_marked',)
    date_hierarchy = 'date'
    
    # For better performance with large datasets
    raw_id_fields = ('member',)
    
    list_per_page = 100
    
    def get_queryset(self, request):
        """Optimize queryset by selecting related member."""
        return super().get_queryset(request).select_related('member')
