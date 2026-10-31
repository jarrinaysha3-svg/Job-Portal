from django.contrib import admin
from .models import ProfileModel, CompanyModel, JobModel, ApplicationModel

admin.site.register(ProfileModel)
admin.site.register(CompanyModel)
admin.site.register(JobModel)
admin.site.register(ApplicationModel)