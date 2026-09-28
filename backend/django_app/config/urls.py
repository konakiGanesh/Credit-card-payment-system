from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from admin_panel import views as admin_views
from cards import views as card_views
from transactions import views as transaction_views
from users import views as user_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/register/", user_views.RegisterView.as_view()),
    path("api/auth/login/", user_views.LoginView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/auth/logout/", user_views.LogoutView.as_view()),
    path("api/auth/me/", user_views.MeView.as_view()),
    path("api/cards/", card_views.CardListCreateView.as_view()),
    path("api/cards/<int:pk>/", card_views.CardDeleteView.as_view()),
    path("api/transactions/", transaction_views.TransactionListView.as_view()),
    path("api/transactions/<int:pk>/", transaction_views.TransactionDetailView.as_view()),
    path("api/admin/users/", admin_views.UserListView.as_view()),
    path("api/admin/users/<int:pk>/", admin_views.UserManageView.as_view()),
    path("api/admin/cards/", admin_views.AdminCardListView.as_view()),
    path("api/admin/transactions/", admin_views.AdminTransactionListView.as_view()),
    path("api/admin/transactions/export/", admin_views.ExportView.as_view()),
    path("api/admin/summary/", admin_views.SummaryView.as_view()),
    path("api/admin/logs/", admin_views.AdminLogListView.as_view()),
    path("internal/payments/", transaction_views.InternalPaymentView.as_view()),
    path("internal/payments/<uuid:reference>/", transaction_views.InternalPaymentFinalizeView.as_view()),
]