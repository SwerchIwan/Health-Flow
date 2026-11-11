from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from HealthFlow import settings
from home.views import index_page, window_page, seed_demo_data
from subscription.views import pay_page, process_payment, payment_success, cancel_subscription
from users.views import auth_page, auth_page_two, reg_page, login_user, logout_user, register_user, check, confirm_registration_code
from django.views.generic import TemplateView
# from messenger.views import *
from diary.views import *
from profile_user.views import profile_page, chat_detail, send_message,  update_profile, add_note, search_specialist, start_chat, get_note_details, set_rating, create_specialist, delete_chat, get_bmi_data, process_message, my_notes, send_notes, specialists_catalog, specialist_detail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index_page),
    path('accounts/', auth_page, name='auth_page'),
    path('accounts/step-two/', auth_page_two, name='auth_page_two'),
    path('accounts/registration/', register_user, name='reg_page'),
    path('accounts/registration/confirm/', confirm_registration_code, name='confirm_registration'),
    path('accounts/login/', login_user, name='login'),
    path('accounts/logout/', logout_user, name='logout'),
    path('accounts/check/', check, name='check'),
    path('users/', include('users.urls', namespace="auth_reg")),
    path('window', TemplateView.as_view(template_name="window.html"), name='window'),
    # path('new', message_list, name='message_list'),
    # path('send/', send_message, name='send_message'),
    path('new2', entry_list, name='entry_list'),
    path('add/', entry_create, name='entry_create'),
    path('profile/', profile_page, name="profile_page"),
    path('profile/chat_detail/<int:chat_id>/', chat_detail, name='chat_detail'),
    path('profile/send_message/', send_message, name='send_message'),
    path('profile/notes/', my_notes, name='my_notes'),
    path('profile/send_notes/<int:chat_id>/', send_notes, name='send_notes'),
    path('profile/set_rating/', set_rating, name='set_rating'),
    path('profile/create_specialist/', create_specialist, name='create_specialist'),
    path('profile/update_profile/', update_profile, name='update-profile'),
    path('profile/add_note/', add_note, name='add-note'),
    path('search_specialist/', search_specialist, name='search_specialist'),
    path('profile/start_chat/', start_chat, name='start_chat'),
    path('profile/get_note_details/<int:note_id>/', get_note_details, name='get_note_details'),
    path('profile/delete_chat/<int:chat_id>/', delete_chat, name='delete_chat'),
    path('pay/', pay_page, name='pay'),
    path('process_payment/', process_payment, name='process_payment'),
    path('payment_success/', payment_success, name='payment_success'),
    path('pay/cancel/', cancel_subscription, name='cancel_subscription'),
    path('profile/get_bmi_data/', get_bmi_data, name='get_bmi_data'),
    path('process-message/', process_message, name='process-message'),
    path('register/', register_user, name='register_user'),
    path('confirm_phone/', confirm_registration_code, name='confirm_phone_registration'),
    path('check/', check, name='check'),
    path('specialists/', specialists_catalog, name='specialists_catalog'),
    path('specialists/<int:specialist_id>/', specialist_detail, name='specialist_detail'),
    path('internal/seed/<str:token>/', seed_demo_data, name='seed_demo_data'),
]

# Добавьте это в конец файла
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)