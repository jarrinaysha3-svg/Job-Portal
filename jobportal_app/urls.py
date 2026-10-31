from django.urls import path
from jobportal_app.views import *

urlpatterns = [
    path('', home_view, name='home_view'),
    path('register/', register_view, name='register_view'),
    path('login/', login_view, name='login_view'),
    path('logout/', logout_view, name='logout_view'),
    path('employer_dashboard/', employer_dashboard, name='employer_dashboard'),
    path('add_company/', add_company, name='add_company'),
    path('update_company/', update_company, name='update_company'),
    path('add_job/', add_job, name='add_job'),
    path('update_job/<int:id>/', update_job, name='update_job'),
    path('delete_job/<int:id>/', delete_job, name='delete_job'),
    path('job_detail/<int:id>/', job_detail, name='job_detail'),
    path('apply_job/<int:id>/', apply_job, name='apply_job'),
    path('my_applications/', my_applications, name='my_applications'),
        path('job_applicants/<int:id>/', job_applicants, name='job_applicants'),
    path('update_application_status/<int:id>/', update_application_status, name='update_application_status'),
        path('update_profile/', update_profile, name='update_profile'),
]