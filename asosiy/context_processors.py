from .models import Savatcha

def global_data(request):
    savat_soni = 0
    compare_soni = 0

    if request.user.is_authenticated:
        savat_soni = Savatcha.objects.filter(foydalanuvchi=request.user).count()

    compare_list = request.session.get("compare_list", [])
    compare_soni = len(compare_list)

    return {
        "savat_soni": savat_soni,
        "compare_soni": compare_soni,
    }