from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.views.static import serve
from asosiy import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('symptom-checker/', views.symptom_checker, name='symptom_checker'),
    path('', views.home, name='home'),
    path('category/<int:id>/', views.home, name='category_filter'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),

    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('add/<int:id>/', views.add_to_cart, name='add_cart'),
    path('minus/<int:item_id>/', views.minus_cart, name='minus_cart'),
    path('delete/<int:item_id>/', views.delete_cart, name='delete_cart'),
    path('cart/', views.view_cart, name='cart'),

    path('checkout/', views.checkout, name='checkout'),
    path('profile/', views.profile, name='profile'),
    path('reorder/<int:id>/', views.reorder, name='reorder'),

    path('wishlist/', views.view_wishlist, name='wishlist'),
    path('wishlist/toggle/<int:id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('compare/', views.compare_products, name='compare_products'),
    path('compare/add/<int:id>/', views.add_to_compare, name='add_to_compare'),
    path('compare/remove/<int:id>/', views.remove_from_compare, name='remove_from_compare'),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]