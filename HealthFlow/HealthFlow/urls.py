from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from HealthFlow import settings
from home.views import index_page, window_page
from subscription.views import sub_page
from users.views import auth_page, auth_page_two, reg_page, login_user, logout_user, register_user, confirm_registration,check
from django.views.generic import TemplateView
# from messenger.views import *
from diary.views import *
from profile_user.views import profile_page, chat_detail, send_message, process_message, update_profile, add_note

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_page),
    path('type-subscription/', sub_page),
    path('accounts/', auth_page, name='auth_page'),
    path('accounts/step-two/', auth_page_two, name='auth_page_two'),
    path('accounts/registration/', reg_page, name='reg_page'),
    path('accounts/login/', login_user, name='login'),
    path('accounts/registration/confirm', register_user, name='registration'),
    path('accounts/logout/', logout_user, name='logout'),
    path('accounts/check/', check, name='check'),
    path('users/', include('users.urls', namespace="auth_reg")),
    path('window', TemplateView.as_view(template_name="window.html"), name='window'),
    path('accounts/registration/confirm/<str:token>/', confirm_registration, name='confirm_registration'),
    # path('new', message_list, name='message_list'),
    # path('send/', send_message, name='send_message'),
    path('new2', entry_list, name='entry_list'),
    path('add/', entry_create, name='entry_create'),
    path('profile/', profile_page, name="profile_page"),
    path('profile/chat_detail/<int:chat_id>/', chat_detail, name='chat_detail'),
    path('profile/send_message/', send_message, name='send_message'),
    path('process-message/', process_message, name='process-message'),
    path('profile/update_profile/', csrf_exempt(update_profile), name='update-profile'),
    path('profile/add_note/', add_note, name='add-note')
]

# Добавьте это в конец файла
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)