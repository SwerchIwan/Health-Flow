from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from HealthFlow import settings
from home.views import index_page, window_page
from subscription.views import pay_page, process_payment, payment_success
from users.views import auth_page, auth_page_two, reg_page, login_user, logout_user, register_user, confirm_registration,check, confirm_phone_registration
from django.views.generic import TemplateView
# from messenger.views import *
from diary.views import *
from profile_user.views import profile_page, chat_detail, send_message,  update_profile, add_note, search_specialist, start_chat, get_note_details, set_rating, create_specialist, delete_chat, get_bmi_data, process_message

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_page),
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
    path('profile/set_rating/', set_rating, name='set_rating'),
    path('profile/create_specialist/', create_specialist, name='create_specialist'),
    path('profile/update_profile/', csrf_exempt(update_profile), name='update-profile'),
    path('profile/add_note/', add_note, name='add-note'),
    path('search_specialist/', search_specialist, name='search_specialist'),
    path('profile/start_chat/', start_chat, name='start_chat'),
    path('profile/get_note_details/<int:note_id>/', get_note_details, name='get_note_details'),
    path('profile/delete_chat/<int:chat_id>/', delete_chat, name='delete_chat'),
    path('pay/', pay_page, name='pay'),
    path('process_payment/', process_payment, name='process_payment'),
    path('payment_success/', payment_success, name='payment_success'),
    path('profile/get_bmi_data/', get_bmi_data, name='get_bmi_data'),
    path('process-message/', process_message, name='process-message'),
    path('register/', register_user, name='register_user'),
    path('confirm/<str:token>/', confirm_registration, name='confirm_registration'),
    path('confirm_phone/', confirm_phone_registration, name='confirm_phone_registration'),
    path('check/', check, name='check'),
]

# Добавьте это в конец файла
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)