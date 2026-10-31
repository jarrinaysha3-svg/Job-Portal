from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from jobportal_app.forms import RegisterForm, LoginForm, CompanyForm, JobForm, ApplicationForm, ProfileForm, UserUpdateForm
from jobportal_app.models import ProfileModel, CompanyModel, JobModel, ApplicationModel
from jobportal_app.decorators import employer_required, seeker_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator


def home_view(request):
    jobs = JobModel.objects.filter(
        is_active=True, deadline__gte=timezone.localdate()
    ).select_related('company').order_by('-created_at')

    q = request.GET.get('q', '').strip()
    job_type = request.GET.get('job_type', '')
    location = request.GET.get('location', '').strip()

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(company__name__icontains=q)
        )
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if location:
        jobs = jobs.filter(location__icontains=location)

    paginator = Paginator(jobs, 5)
    page_obj = paginator.get_page(request.GET.get('page'))

    params = request.GET.copy()
    params.pop('page', None)

    context = {
        'page_obj': page_obj,
        'query_string': params.urlencode(),
        'q': q,
        'job_type': job_type,
        'location': location,
        'type_choices': JobModel.TYPE_CHOICES,
        'title': 'Home',
    }
    return render(request, 'home.html', context)

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            ProfileModel.objects.create(user=user, role=form.cleaned_data['role'])
            messages.success(request, 'Account created. Please log in.')
            return redirect('login_view')
    else:
        form = RegisterForm()
    context = {
        'form_data': form,
        'form_title': 'Register',
        'form_btn': 'Register',
        'title': 'Register',
    }
    return render(request, 'master/base_form.html', context)


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                return redirect('home_view')
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    context = {
        'form_data': form,
        'form_title': 'Login',
        'form_btn': 'Login',
        'title': 'Login',
    }
    return render(request, 'master/base_form.html', context)


def logout_view(request):
    logout(request)
    return redirect('login_view')


@login_required
@employer_required
def employer_dashboard(request):
    company = CompanyModel.objects.filter(user=request.user).first()
    if not company:
        messages.warning(request, 'Please add your company details first.')
        return redirect('add_company')

    jobs = JobModel.objects.filter(company=company).annotate(
        applicant_count=Count('applicationmodel')
    ).order_by('-created_at')

    context = {
        'company': company,
        'jobs': jobs,
        'total_jobs': jobs.count(),
        'active_jobs': jobs.filter(is_active=True).count(),
        'total_applications': ApplicationModel.objects.filter(job__company=company).count(),
        'title': 'Employer Dashboard',
    }
    return render(request, 'employer_dashboard.html', context)


@login_required
@employer_required
def add_company(request):
    if CompanyModel.objects.filter(user=request.user).exists():
        messages.warning(request, 'You already have a company profile.')
        return redirect('employer_dashboard')

    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()
            messages.success(request, 'Company added successfully.')
            return redirect('employer_dashboard')
    else:
        form = CompanyForm()
    context = {
        'form_data': form,
        'form_title': 'Add Company',
        'form_btn': 'Save Company',
        'title': 'Add Company',
    }
    return render(request, 'master/base_form.html', context)


@login_required
@employer_required
def update_company(request):
    company = get_object_or_404(CompanyModel, user=request.user)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company updated successfully.')
            return redirect('employer_dashboard')
    else:
        form = CompanyForm(instance=company)
    context = {
        'form_data': form,
        'form_title': 'Update Company',
        'form_btn': 'Update Company',
        'title': 'Update Company',
    }
    return render(request, 'master/base_form.html', context)


@login_required
@employer_required
def add_job(request):
    company = CompanyModel.objects.filter(user=request.user).first()
    if not company:
        messages.warning(request, 'Please add your company details first.')
        return redirect('add_company')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.save()
            messages.success(request, 'Job posted successfully.')
            return redirect('employer_dashboard')
    else:
        form = JobForm()
    context = {
        'form_data': form,
        'form_title': 'Post a Job',
        'form_btn': 'Post Job',
        'title': 'Post a Job',
    }
    return render(request, 'master/base_form.html', context)


@login_required
@employer_required
def update_job(request, id):
    job = get_object_or_404(JobModel, id=id, company__user=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully.')
            return redirect('employer_dashboard')
    else:
        form = JobForm(instance=job)
    context = {
        'form_data': form,
        'form_title': 'Update Job',
        'form_btn': 'Update Job',
        'title': 'Update Job',
    }
    return render(request, 'master/base_form.html', context)


@login_required
@employer_required
def delete_job(request, id):
    job = get_object_or_404(JobModel, id=id, company__user=request.user)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully.')
        return redirect('employer_dashboard')
    context = {'job': job, 'title': 'Delete Job'}
    return render(request, 'delete_job.html', context)

def job_detail(request, id):
    job = get_object_or_404(JobModel, id=id)
    has_applied = False
    if request.user.is_authenticated:
        has_applied = ApplicationModel.objects.filter(job=job, user=request.user).exists()
    is_open = job.is_active and job.deadline >= timezone.localdate()
    context = {
        'job': job,
        'has_applied': has_applied,
        'is_open': is_open,
        'title': job.title,
    }
    return render(request, 'job_detail.html', context)


@login_required
@seeker_required
def apply_job(request, id):
    job = get_object_or_404(
        JobModel, id=id, is_active=True, deadline__gte=timezone.localdate()
    )
    if ApplicationModel.objects.filter(job=job, user=request.user).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('my_applications')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.user = request.user
            application.save()
            messages.success(request, 'Application submitted successfully.')
            return redirect('my_applications')
    else:
        form = ApplicationForm()
    context = {
        'form_data': form,
        'form_title': f'Apply for {job.title}',
        'form_btn': 'Submit Application',
        'title': 'Apply',
    }
    return render(request, 'master/base_form.html', context)


@login_required
@seeker_required
def my_applications(request):
    applications = ApplicationModel.objects.filter(
        user=request.user
    ).select_related('job', 'job__company').order_by('-applied_at')
    context = {'applications': applications, 'title': 'My Applications'}
    return render(request, 'my_applications.html', context)

@login_required
@employer_required
def job_applicants(request, id):
    job = get_object_or_404(JobModel, id=id, company__user=request.user)
    applications = ApplicationModel.objects.filter(job=job).select_related('user', 'user__profilemodel').order_by('-applied_at')

    status = request.GET.get('status', '')
    if status in ['pending', 'shortlisted', 'rejected']:
        applications = applications.filter(status=status)

    counts = ApplicationModel.objects.filter(job=job).aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        shortlisted=Count('id', filter=Q(status='shortlisted')),
        rejected=Count('id', filter=Q(status='rejected')),
    )

    context = {
        'job': job,
        'applications': applications,
        'counts': counts,
        'status': status,
        'title': 'Applicants',
    }
    return render(request, 'job_applicants.html', context)


@login_required
@employer_required
@require_POST
def update_application_status(request, id):
    application = get_object_or_404(
        ApplicationModel, id=id, job__company__user=request.user
    )
    new_status = request.POST.get('status')
    if new_status in ['pending', 'shortlisted', 'rejected']:
        application.status = new_status
        application.save()
        messages.success(request, f'Application marked as {new_status}.')
    else:
        messages.error(request, 'Invalid status.')
    return redirect('job_applicants', id=application.job.id)

@login_required
def update_profile(request):
    profile = get_object_or_404(ProfileModel, user=request.user)
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile_view')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'My Profile',
    }
    return render(request, 'profile.html', context)

@login_required
def profile_view(request):
    profile = get_object_or_404(ProfileModel, user=request.user)
    context = {'profile': profile, 'title': 'My Profile'}
    return render(request, 'profile_view.html', context)