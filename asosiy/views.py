from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

import google.generativeai as genai
import requests

genai.configure(api_key=settings.GEMINI_API_KEY)

from .models import (
    Mahsulot,
    Savatcha,
    Kategoriya,
    Buyurtma,
    BuyurtmaMahsulot,
    Izoh,
    Saralangan,
)
from .forms import BuyurtmaForm


def send_telegram_message(message):
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)

    if not token or not chat_id:
        print("TELEGRAM ERROR: TELEGRAM_BOT_TOKEN yoki TELEGRAM_CHAT_ID topilmadi")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        print("TELEGRAM STATUS:", response.status_code)
        print("TELEGRAM RESPONSE:", response.text)
    except requests.RequestException as e:
        print("TELEGRAM ERROR:", str(e))


def send_low_stock_alert(mahsulot):
    if mahsulot.mavjud_soni <= 5:
        message = (
            f"<b>Kam qolgan mahsulot!</b>\n\n"
            f"<b>Mahsulot:</b> {mahsulot.nomi}\n"
            f"<b>Qolgan soni:</b> {mahsulot.mavjud_soni} ta\n"
            f"<b>Narxi:</b> {mahsulot.narxi} so'm"
        )
        send_telegram_message(message)


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ro'yxatdan muvaffaqiyatli o'tdingiz. Endi tizimga kiring.")
            return redirect("login")
        messages.error(request, "Ro'yxatdan o'tishda xatolik bor. Ma'lumotlarni tekshiring.")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


def analyze_symptoms(symptom_text):
    """
    Oddiy simptom tahlili.
    Bu diagnostika emas, faqat mos kategoriya va mahsulotlarni ko'rsatadi.
    """
    text = symptom_text.lower().strip()

    symptom_map = {
        "shamollash": {
            "keywords": ["yo'tal", "tomoq", "isitma", "gripp", "shamollash", "burun", "tumov"],
            "title": "Shamollash va grippga oid ehtiyojlar",
            "category_names": ["Shamollash", "Vitaminlar", "Og'riq qoldiruvchi"],
            "advice": "Ko‘p suyuqlik ichish va tana haroratini kuzatish tavsiya etiladi. Kuchli isitma yoki holsizlik bo‘lsa shifokorga murojaat qiling.",
        },
        "bosh_ogriq": {
            "keywords": ["bosh og'riq", "migren", "boshim og'riyapti", "bosh aylanishi", "bosh og'riyapti"],
            "title": "Bosh og‘rig‘iga oid mahsulotlar",
            "category_names": ["Og'riq qoldiruvchi", "Vitaminlar"],
            "advice": "Dam olish, suv ichish va simptom kuchaysa shifokorga murojaat qilish tavsiya etiladi.",
        },
        "oshqozon": {
            "keywords": ["oshqozon", "ich ketish", "qorin", "ko'ngil aynish", "hazm", "qabziyat"],
            "title": "Oshqozon va hazm tizimiga oid mahsulotlar",
            "category_names": ["Oshqozon", "Vitaminlar"],
            "advice": "Og‘ir ovqatlardan vaqtincha saqlanish va suyuqlik balansini ushlash tavsiya etiladi.",
        },
        "allergiya": {
            "keywords": ["allergiya", "toshma", "qichishish", "aksirish", "ko'z yoshlanishi"],
            "title": "Allergiyaga oid mahsulotlar",
            "category_names": ["Allergiya", "Vitaminlar"],
            "advice": "Allergiya kuchaysa yoki nafas olish qiyinlashsa tezda shifokorga murojaat qiling.",
        },
        "vitamin": {
            "keywords": ["holsizlik", "vitamin", "immunitet", "charchoq", "quvvat yo'q"],
            "title": "Vitamin va umumiy qo'llab-quvvatlash mahsulotlari",
            "category_names": ["Vitaminlar"],
            "advice": "Doimiy charchoq bo‘lsa shifokor bilan maslahatlashish foydali bo‘ladi.",
        },
    }

    matched = None
    best_score = 0

    for key, data in symptom_map.items():
        score = sum(1 for keyword in data["keywords"] if keyword in text)
        if score > best_score:
            best_score = score
            matched = data

    return matched


def ai_symptom_analysis(symptom_text):
    """
    Gemini AI orqali simptomlar bo'yicha umumiy tavsiya.
    Bu diagnostika emas.
    """
    prompt = f"""
Foydalanuvchi quyidagi simptomlarni yozdi:

{symptom_text}

Muhim qoidalar:
- Sen tibbiy tashxis qo'ymaysan.
- Sen faqat umumiy ma'lumot berasan.
- Xavfli yoki kuchli davom etayotgan simptomlarda shifokorga murojaat qilishni tavsiya qilasan.
- Javob o'zbek tilida bo'lsin.
- Juda uzun yozma.

Quyidagi formatda yoz:
1. Ehtimoliy holat
2. Mos bo‘lishi mumkin bo‘lgan dori turi yoki kategoriya
3. Qachon shifokorga murojaat qilish kerak
4. Bu tashxis emas, degan ogohlantirish
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        return "AI javob qaytarmadi. Iltimos, keyinroq yana urinib ko'ring."
    except Exception as e:
        print("GEMINI ERROR:", str(e))
        return "Hozircha AI tahlil vaqtincha ishlamayapti. Quyida umumiy tavsiyalar ko‘rsatiladi."


@login_required
def symptom_checker(request):
    symptom_text = ""
    ai_response = ""
    recommended_products = []
    matched_info = None

    if request.method == "POST":
        symptom_text = request.POST.get("symptoms", "").strip()

        if symptom_text:
            ai_response = ai_symptom_analysis(symptom_text)
            matched_info = analyze_symptoms(symptom_text)

            if matched_info:
                recommended_products = Mahsulot.objects.filter(
                    is_active=True,
                    kategoriya__nomi__in=matched_info["category_names"]
                ).select_related("kategoriya")[:8]
            else:
                recommended_products = Mahsulot.objects.filter(
                    is_active=True
                ).select_related("kategoriya")[:8]

    context = {
        "symptom_text": symptom_text,
        "ai_response": ai_response,
        "recommended_products": recommended_products,
        "matched_info": matched_info,
    }

    return render(request, "symptom_checker.html", context)


@login_required
def home(request, id=None):
    kategoriyalar = Kategoriya.objects.all()

    dorilar = (
        Mahsulot.objects.filter(is_active=True)
        .select_related("kategoriya")
    )

    tanlangan_kategoriya = None

    if id is not None:
        tanlangan_kategoriya = get_object_or_404(Kategoriya, id=id)
        dorilar = dorilar.filter(kategoriya_id=id)

    qidiruv = request.GET.get("q", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    sort = request.GET.get("sort", "newest")

    if qidiruv:
        dorilar = dorilar.filter(
            Q(nomi__icontains=qidiruv) |
            Q(tavsif__icontains=qidiruv) |
            Q(kategoriya__nomi__icontains=qidiruv)
        )

    if min_price:
        try:
            dorilar = dorilar.filter(narxi__gte=int(min_price))
        except ValueError:
            min_price = ""

    if max_price:
        try:
            dorilar = dorilar.filter(narxi__lte=int(max_price))
        except ValueError:
            max_price = ""

    if sort == "price_asc":
        dorilar = dorilar.order_by("narxi")
    elif sort == "price_desc":
        dorilar = dorilar.order_by("-narxi")
    elif sort == "name":
        dorilar = dorilar.order_by("nomi")
    else:
        dorilar = dorilar.order_by("-created_at")

    saralangan_ids = set(
        Saralangan.objects.filter(foydalanuvchi=request.user)
        .values_list("mahsulot_id", flat=True)
    )

    eng_kop_sotilgan_ids = (
        BuyurtmaMahsulot.objects
        .values("mahsulot")
        .annotate(jami_sotilgan=Sum("soni"))
        .order_by("-jami_sotilgan")[:6]
    )

    top_ids = [item["mahsulot"] for item in eng_kop_sotilgan_ids]

    eng_kop_sotilganlar = list(
        Mahsulot.objects.filter(id__in=top_ids, is_active=True)
        .select_related("kategoriya")
    )

    mahsulot_map = {m.id: m for m in eng_kop_sotilganlar}
    eng_kop_sotilganlar = [mahsulot_map[i] for i in top_ids if i in mahsulot_map]

    paginator = Paginator(dorilar, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "dorilar": page_obj,
        "page_obj": page_obj,
        "kategoriyalar": kategoriyalar,
        "qidiruv": qidiruv,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
        "tanlangan_kategoriya": tanlangan_kategoriya,
        "saralangan_ids": saralangan_ids,
        "eng_kop_sotilganlar": eng_kop_sotilganlar,
    }
    return render(request, "home.html", context)


def product_detail(request, id):
    dori = get_object_or_404(
        Mahsulot.objects.select_related("kategoriya"),
        id=id,
        is_active=True
    )

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Izoh qoldirish uchun tizimga kiring.")
            return redirect("login")

        matn = request.POST.get("izoh_matni", "").strip()
        baho = request.POST.get("baho", "").strip()

        if not matn:
            messages.error(request, "Izoh matnini kiriting.")
            return redirect("product_detail", id=id)

        try:
            baho = int(baho)
            if baho < 1 or baho > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Baho 1 dan 5 gacha bo'lishi kerak.")
            return redirect("product_detail", id=id)

        Izoh.objects.create(
            mahsulot=dori,
            foydalanuvchi=request.user,
            matn=matn,
            baho=baho
        )
        messages.success(request, "Izoh muvaffaqiyatli qo'shildi.")
        return redirect("product_detail", id=id)

    izohlar = dori.izohlar.select_related("foydalanuvchi").all().order_by("-sana")
    izohlar_soni = izohlar.count()
    baho_jami = sum(i.baho for i in izohlar)
    ortacha_baho = round(baho_jami / izohlar_soni, 1) if izohlar_soni else 0

    oxshash_dorilar = (
        Mahsulot.objects.filter(
            kategoriya=dori.kategoriya,
            is_active=True
        )
        .exclude(id=dori.id)[:4]
    )

    saralanganmi = False
    if request.user.is_authenticated:
        saralanganmi = Saralangan.objects.filter(
            foydalanuvchi=request.user,
            mahsulot=dori
        ).exists()

    context = {
        "dori": dori,
        "izohlar": izohlar,
        "izohlar_soni": izohlar_soni,
        "ortacha_baho": ortacha_baho,
        "oxshash_dorilar": oxshash_dorilar,
        "saralanganmi": saralanganmi,
    }
    return render(request, "detail.html", context)


@login_required
def add_to_cart(request, id):
    dori = get_object_or_404(Mahsulot, id=id, is_active=True)

    if dori.mavjud_soni < 1:
        messages.error(request, "Bu mahsulot hozir mavjud emas.")
        return redirect(request.META.get("HTTP_REFERER", "home"))

    item, created = Savatcha.objects.get_or_create(
        foydalanuvchi=request.user,
        mahsulot=dori
    )

    if not created:
        if item.soni + 1 > dori.mavjud_soni:
            messages.warning(request, f"Omborda '{dori.nomi}' dan faqat {dori.mavjud_soni} ta bor.")
            return redirect(request.META.get("HTTP_REFERER", "home"))
        item.soni += 1
        item.save()

    messages.success(request, f"{dori.nomi} savatchaga qo'shildi.")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def minus_cart(request, item_id):
    item = get_object_or_404(Savatcha, id=item_id, foydalanuvchi=request.user)

    if item.soni > 1:
        item.soni -= 1
        item.save()
    else:
        item.delete()

    return redirect("cart")


@login_required
def delete_cart(request, item_id):
    item = get_object_or_404(Savatcha, id=item_id, foydalanuvchi=request.user)
    item.delete()
    messages.warning(request, "Mahsulot savatchadan olib tashlandi.")
    return redirect("cart")


@login_required
def view_cart(request):
    items = (
        Savatcha.objects.filter(foydalanuvchi=request.user)
        .select_related("mahsulot", "mahsulot__kategoriya")
        .order_by("-qoshilgan_vaqt")
    )
    jami_summa = sum(item.jami_narx for item in items)

    context = {
        "items": items,
        "jami": jami_summa,
    }
    return render(request, "cart.html", context)


@login_required
def checkout(request):
    items = Savatcha.objects.filter(foydalanuvchi=request.user).select_related("mahsulot")

    if not items.exists():
        messages.warning(request, "Savatchangiz bo'sh.")
        return redirect("home")

    jami = sum(item.jami_narx for item in items)

    for item in items:
        if item.mahsulot.mavjud_soni < item.soni:
            messages.error(
                request,
                f"Uzr, '{item.mahsulot.nomi}' dan omborda faqat {item.mahsulot.mavjud_soni} ta qolgan."
            )
            return redirect("cart")

    if request.method == "POST":
        form = BuyurtmaForm(request.POST)
        if form.is_valid():
            buyurtma = form.save(commit=False)
            buyurtma.foydalanuvchi = request.user
            buyurtma.jami_summa = jami
            buyurtma.save()

            for item in items:
                BuyurtmaMahsulot.objects.create(
                    buyurtma=buyurtma,
                    mahsulot=item.mahsulot,
                    soni=item.soni,
                    narxi=item.mahsulot.narxi,
                )

                product = item.mahsulot
                product.mavjud_soni -= item.soni
                product.save()

                send_low_stock_alert(product)

            order_items = BuyurtmaMahsulot.objects.filter(buyurtma=buyurtma).select_related("mahsulot")

            mahsulotlar_text = ""
            for item in order_items:
                mahsulotlar_text += f"• {item.mahsulot.nomi} — {item.soni} ta\n"

            telegram_text = (
                f"<b>Yangi buyurtma!</b>\n\n"
                f"<b>Buyurtma ID:</b> #{buyurtma.id}\n"
                f"<b>Foydalanuvchi:</b> {request.user.username}\n"
                f"<b>Telefon:</b> {buyurtma.tel_raqam}\n"
                f"<b>Manzil:</b> {buyurtma.manzil}\n"
                f"<b>Jami summa:</b> {buyurtma.jami_summa} so'm\n\n"
                f"<b>Mahsulotlar:</b>\n{mahsulotlar_text}"
            )

            send_telegram_message(telegram_text)

            items.delete()
            messages.success(request, "Buyurtmangiz muvaffaqiyatli qabul qilindi.")
            return redirect("profile")

        messages.error(request, "Forma ma'lumotlarini to'g'ri kiriting.")
    else:
        form = BuyurtmaForm()

    context = {
        "form": form,
        "jami": jami,
        "items": items,
    }
    return render(request, "checkout.html", context)


@login_required
def profile(request):
    buyurtmalar = (
        Buyurtma.objects.filter(foydalanuvchi=request.user)
        .prefetch_related("buyurtma_dorilari__mahsulot")
        .order_by("-sana")
    )

    savat_soni = Savatcha.objects.filter(foydalanuvchi=request.user).count()
    saralangan_soni = Saralangan.objects.filter(foydalanuvchi=request.user).count()

    context = {
        "buyurtmalar": buyurtmalar,
        "savat_soni": savat_soni,
        "saralangan_soni": saralangan_soni,
    }
    return render(request, "profile.html", context)


@login_required
def toggle_wishlist(request, id):
    dori = get_object_or_404(Mahsulot, id=id, is_active=True)

    saralangan, created = Saralangan.objects.get_or_create(
        foydalanuvchi=request.user,
        mahsulot=dori
    )

    if created:
        messages.success(request, "Saralanganlarga qo'shildi ❤️")
    else:
        saralangan.delete()
        messages.warning(request, "Saralanganlardan olib tashlandi.")

    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def view_wishlist(request):
    saralanganlar = (
        Saralangan.objects.filter(foydalanuvchi=request.user)
        .select_related("mahsulot", "mahsulot__kategoriya")
        .order_by("-qoshilgan_vaqt")
    )

    context = {
        "saralanganlar": saralanganlar,
    }
    return render(request, "wishlist.html", context)


@login_required
def add_to_compare(request, id):
    dori = get_object_or_404(Mahsulot, id=id, is_active=True)

    compare_list = request.session.get("compare_list", [])

    if id in compare_list:
        messages.info(request, "Bu mahsulot allaqachon solishtirish ro'yxatida bor.")
    else:
        if len(compare_list) >= 3:
            messages.warning(request, "Bir vaqtda ko'pi bilan 3 ta mahsulotni solishtirish mumkin.")
        else:
            compare_list.append(id)
            request.session["compare_list"] = compare_list
            request.session.modified = True
            messages.success(request, f"{dori.nomi} solishtirish ro'yxatiga qo'shildi.")

    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def remove_from_compare(request, id):
    compare_list = request.session.get("compare_list", [])

    if id in compare_list:
        compare_list.remove(id)
        request.session["compare_list"] = compare_list
        request.session.modified = True
        messages.warning(request, "Mahsulot solishtirish ro'yxatidan olib tashlandi.")

    return redirect("compare_products")


@login_required
def compare_products(request):
    compare_list = request.session.get("compare_list", [])

    mahsulotlar = (
        Mahsulot.objects.filter(id__in=compare_list, is_active=True)
        .select_related("kategoriya")
    )

    mahsulot_dict = {m.id: m for m in mahsulotlar}
    ordered_mahsulotlar = [mahsulot_dict[i] for i in compare_list if i in mahsulot_dict]

    context = {
        "compare_products": ordered_mahsulotlar,
        "compare_count": len(ordered_mahsulotlar),
    }
    return render(request, "compare.html", context)


@login_required
def reorder(request, id):
    buyurtma = get_object_or_404(Buyurtma, id=id, foydalanuvchi=request.user)
    mahsulotlar = BuyurtmaMahsulot.objects.filter(buyurtma=buyurtma).select_related("mahsulot")

    added_count = 0

    for item in mahsulotlar:
        mahsulot = item.mahsulot

        if not mahsulot.is_active or mahsulot.mavjud_soni < 1:
            continue

        savat_item, created = Savatcha.objects.get_or_create(
            foydalanuvchi=request.user,
            mahsulot=mahsulot,
            defaults={"soni": 0}
        )

        mumkin_bolgan_son = mahsulot.mavjud_soni - savat_item.soni
        if mumkin_bolgan_son <= 0:
            continue

        qoshiladigan_son = min(item.soni, mumkin_bolgan_son)
        savat_item.soni += qoshiladigan_son
        savat_item.save()
        added_count += qoshiladigan_son

    if added_count > 0:
        messages.success(request, "Buyurtmadagi mahsulotlar savatchaga qayta qo'shildi.")
    else:
        messages.warning(request, "Qayta qo'shish uchun mos mahsulot topilmadi yoki omborda mavjud emas.")

    return redirect("cart")


@staff_member_required
def admin_dashboard(request):
    today = timezone.now().date()

    jami_mahsulotlar = Mahsulot.objects.count()
    jami_buyurtmalar = Buyurtma.objects.count()
    jami_foydalanuvchilar = User.objects.count()

    bugungi_buyurtmalar = Buyurtma.objects.filter(sana__date=today)
    bugungi_buyurtma_soni = bugungi_buyurtmalar.count()
    bugungi_tushum = bugungi_buyurtmalar.aggregate(total=Sum("jami_summa"))["total"] or 0

    kam_qolgan_mahsulotlar = (
        Mahsulot.objects.filter(mavjud_soni__lte=5, is_active=True)
        .order_by("mavjud_soni")[:10]
    )

    eng_kop_sotilganlar = (
        BuyurtmaMahsulot.objects
        .values("mahsulot__nomi")
        .annotate(jami_sotilgan=Sum("soni"))
        .order_by("-jami_sotilgan")[:10]
    )

    oxirgi_buyurtmalar = Buyurtma.objects.select_related("foydalanuvchi").order_by("-sana")[:10]

    labels = []
    orders_data = []
    revenue_data = []

    for i in range(6, -1, -1):
        day = today - timezone.timedelta(days=i)
        day_orders = Buyurtma.objects.filter(sana__date=day)
        day_count = day_orders.count()
        day_revenue = day_orders.aggregate(total=Sum("jami_summa"))["total"] or 0

        labels.append(day.strftime("%d.%m"))
        orders_data.append(day_count)
        revenue_data.append(day_revenue)

    context = {
        "jami_mahsulotlar": jami_mahsulotlar,
        "jami_buyurtmalar": jami_buyurtmalar,
        "jami_foydalanuvchilar": jami_foydalanuvchilar,
        "bugungi_buyurtma_soni": bugungi_buyurtma_soni,
        "bugungi_tushum": bugungi_tushum,
        "kam_qolgan_mahsulotlar": kam_qolgan_mahsulotlar,
        "eng_kop_sotilganlar": eng_kop_sotilganlar,
        "oxirgi_buyurtmalar": oxirgi_buyurtmalar,
        "chart_labels": labels,
        "chart_orders": orders_data,
        "chart_revenue": revenue_data,
    }
    return render(request, "admin_dashboard.html", context)