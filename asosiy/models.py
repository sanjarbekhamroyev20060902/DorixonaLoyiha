from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class Kategoriya(models.Model):
    nomi = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, blank=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ["nomi"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nomi)
            slug = base_slug
            counter = 1
            while Kategoriya.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nomi


class Mahsulot(models.Model):
    kategoriya = models.ForeignKey(
        Kategoriya,
        on_delete=models.CASCADE,
        related_name="mahsulotlar",
        null=True,
        blank=True
    )
    nomi = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    narxi = models.PositiveIntegerField(validators=[MinValueValidator(1000)])
    tavsif = models.TextField(blank=True)
    rasm = models.ImageField(upload_to="dorilar/")
    mavjud_soni = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nomi)
            slug = base_slug
            counter = 1
            while Mahsulot.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def mavjudmi(self):
        return self.mavjud_soni > 0

    def __str__(self):
        return self.nomi


class Savatcha(models.Model):
    foydalanuvchi = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="savatcha_items"
    )
    mahsulot = models.ForeignKey(
        Mahsulot,
        on_delete=models.CASCADE,
        related_name="savatchada"
    )
    soni = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    qoshilgan_vaqt = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Savatcha"
        verbose_name_plural = "Savatcha"
        unique_together = ("foydalanuvchi", "mahsulot")
        ordering = ["-qoshilgan_vaqt"]

    @property
    def jami_narx(self):
        return self.mahsulot.narxi * self.soni

    def __str__(self):
        return f"{self.foydalanuvchi.username} - {self.mahsulot.nomi} ({self.soni} ta)"


class Buyurtma(models.Model):
    HOLAT_TANLOVLARI = [
        ("Jarayonda", "Jarayonda"),
        ("Tasdiqlandi", "Tasdiqlandi"),
        ("Yuborildi", "Yuborildi"),
        ("Yetkazildi", "Yetkazildi"),
        ("Bekor qilindi", "Bekor qilindi"),
    ]

    foydalanuvchi = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="buyurtmalar"
    )
    sana = models.DateTimeField(auto_now_add=True)
    jami_summa = models.PositiveIntegerField(default=0)
    manzil = models.CharField(max_length=255)
    tel_raqam = models.CharField(max_length=20, default="+998")
    holati = models.CharField(
        max_length=50,
        choices=HOLAT_TANLOVLARI,
        default="Jarayonda"
    )

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ["-sana"]

    def __str__(self):
        return f"Buyurtma #{self.id} - {self.foydalanuvchi.username}"


class BuyurtmaMahsulot(models.Model):
    buyurtma = models.ForeignKey(
        Buyurtma,
        on_delete=models.CASCADE,
        related_name="buyurtma_dorilari"
    )
    mahsulot = models.ForeignKey(
        Mahsulot,
        on_delete=models.CASCADE,
        related_name="buyurtma_mahsulotlari"
    )
    soni = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    narxi = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Buyurtma mahsuloti"
        verbose_name_plural = "Buyurtma mahsulotlari"

    @property
    def jami_narx(self):
        return self.soni * self.narxi

    def __str__(self):
        return f"Buyurtma #{self.buyurtma.id} - {self.mahsulot.nomi}"


class Izoh(models.Model):
    mahsulot = models.ForeignKey(
        Mahsulot,
        on_delete=models.CASCADE,
        related_name="izohlar"
    )
    foydalanuvchi = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="izohlar"
    )
    matn = models.TextField()
    baho = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    sana = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Izoh"
        verbose_name_plural = "Izohlar"
        ordering = ["-sana"]

    def __str__(self):
        return f"{self.foydalanuvchi.username} - {self.mahsulot.nomi} ({self.baho})"


class Saralangan(models.Model):
    foydalanuvchi = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saralanganlar"
    )
    mahsulot = models.ForeignKey(
        Mahsulot,
        on_delete=models.CASCADE,
        related_name="yoqtirilganlar"
    )
    qoshilgan_vaqt = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Saralangan"
        verbose_name_plural = "Saralanganlar"
        unique_together = ("foydalanuvchi", "mahsulot")
        ordering = ["-qoshilgan_vaqt"]

    def __str__(self):
        return f"{self.foydalanuvchi.username} yoqtirdi: {self.mahsulot.nomi}"