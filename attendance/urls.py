from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('mark-present/<int:member_id>/', views.mark_present, name='mark_present'),
    path("complete-profile/", views.complete_profile, name="complete_profile"),
    path("new-member/", views.new_member, name="new_member"),
    path("existing-member/", views.existing_member, name="existing_member"),
    path("COT/", views.admin, name="admin"),
    path("download/", views.download, name="download"),
    path("download_page/", views.download_page, name="download_page"),
    path("passcode/", views.check_passcode, name="check_passcode"),
    path("logout/", views.logout_user, name="logout")
]
