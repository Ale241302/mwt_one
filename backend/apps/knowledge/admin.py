from django.contrib import admin
from .models import ConversationLog


@admin.register(ConversationLog)
class ConversationLogAdmin(admin.ModelAdmin):
    list_display  = ('session_id', 'user', 'user_role', 'expediente_ref', 'created_at', 'retain_until')
    list_filter   = ('user_role',)
    search_fields = ('session_id', 'question')
    readonly_fields = ('created_at',)
