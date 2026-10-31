from django import forms
from django.contrib.auth.models import User
from jobportal_app.models import ProfileModel, CompanyModel, JobModel, ApplicationModel


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=ProfileModel.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class CompanyForm(forms.ModelForm):
    class Meta:
        model = CompanyModel
        exclude = ['user']


class JobForm(forms.ModelForm):
    class Meta:
        model = JobModel
        exclude = ['company', 'created_at']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError('Minimum salary cannot be greater than maximum salary.')
        return cleaned_data


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = ApplicationModel
        exclude = ['job', 'user', 'status', 'applied_at']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 5}),
        }

    def clean_resume(self):
        resume = self.cleaned_data['resume']
        ext = resume.name.rsplit('.', 1)[-1].lower()
        if ext not in ['pdf', 'doc', 'docx']:
            raise forms.ValidationError('Upload a PDF, DOC, or DOCX file.')
        if resume.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Resume must be under 2 MB.')
        return resume

class ProfileForm(forms.ModelForm):
    class Meta:
        model = ProfileModel
        exclude = ['user', 'role']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }