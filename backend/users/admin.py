from django.conf import settings as s
from django.contrib import admin

from .models import Subscribe, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'email', 'first_name',
        'last_name', 'is_superuser'
    )
    search_fields = ('username', 'email',)
    empty_value_display = s.IT_IS_EMPTY


@admin.register(Subscribe)
class Subscribe(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = ('user', 'author')
    empty_value_display = s.IT_IS_EMPTY
