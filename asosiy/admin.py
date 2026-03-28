from django.contrib import admin
from .models import (
    Kategoriya,
    Mahsulot,
    Savatcha,
    Buyurtma,
    BuyurtmaMahsulot,
    Izoh,
    Saralangan,
)


@admin.register(Kategoriya)
class KategoriyaAdmin(admin.ModelAdmin):
    list_display = ("id", "nomi", "slug")
    search_fields = ("nomi", "slug")
    prepopulated_fields = {"slug": ("nomi",)}


@admin.register(Mahsulot)
class MahsulotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nomi",
        "kategoriya",
        "narxi",
        "mavjud_soni",
        "is_active",
        "created_at",
    )
    list_filter = ("kategoriya", "is_active", "created_at")
    search_fields = ("nomi", "tavsif", "slug")
    list_editable = ("narxi", "mavjud_soni", "is_active")
    prepopulated_fields = {"slug": ("nomi",)}
    list_per_page = 20


@admin.register(Savatcha)
class SavatchaAdmin(admin.ModelAdmin):
    list_display = ("id", "foydalanuvchi", "mahsulot", "soni", "jami_narx", "qoshilgan_vaqt")
    list_filter = ("qoshilgan_vaqt",)
    search_fields = ("foydalanuvchi__username", "mahsulot__nomi")
    autocomplete_fields = ("foydalanuvchi", "mahsulot")
    list_per_page = 20


class BuyurtmaMahsulotInline(admin.TabularInline):
    model = BuyurtmaMahsulot
    extra = 0
    readonly_fields = ("mahsulot", "soni", "narxi", "jami_narx")
    can_delete = False

    def jami_narx(self, obj):
        return obj.jami_narx
    jami_narx.short_description = "Jami"


@admin.register(Buyurtma)
class BuyurtmaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "foydalanuvchi",
        "tel_raqam",
        "jami_summa",
        "holati",
        "sana",
    )
    list_filter = ("holati", "sana")
    search_fields = ("foydalanuvchi__username", "tel_raqam", "manzil")
    autocomplete_fields = ("foydalanuvchi",)
    inlines = [BuyurtmaMahsulotInline]
    list_editable = ("holati",)
    readonly_fields = ("sana",)
    list_per_page = 20


@admin.register(Izoh)
class IzohAdmin(admin.ModelAdmin):
    list_display = ("id", "foydalanuvchi", "mahsulot", "baho", "sana")
    list_filter = ("baho", "sana")
    search_fields = ("foydalanuvchi__username", "mahsulot__nomi", "matn")
    autocomplete_fields = ("foydalanuvchi", "mahsulot")
    list_per_page = 20


@admin.register(Saralangan)
class SaralanganAdmin(admin.ModelAdmin):
    list_display = ("id", "foydalanuvchi", "mahsulot", "qoshilgan_vaqt")
    list_filter = ("qoshilgan_vaqt",)
    search_fields = ("foydalanuvchi__username", "mahsulot__nomi")
    autocomplete_fields = ("foydalanuvchi", "mahsulot")
    list_per_page = 20