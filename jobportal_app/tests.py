import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import JobForm
from .models import ApplicationModel, CompanyModel, JobModel, ProfileModel

TEMP_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class BaseTestCase(TestCase):
    """Creates two employers, one seeker, one company and one job."""

    @classmethod
    def setUpTestData(cls):
        cls.employer = User.objects.create_user('employer1', 'e1@test.com', 'pass12345')
        ProfileModel.objects.create(user=cls.employer, role='employer')

        cls.employer2 = User.objects.create_user('employer2', 'e2@test.com', 'pass12345')
        ProfileModel.objects.create(user=cls.employer2, role='employer')

        cls.seeker = User.objects.create_user('seeker1', 's1@test.com', 'pass12345')
        ProfileModel.objects.create(user=cls.seeker, role='seeker')

        cls.company = CompanyModel.objects.create(
            user=cls.employer, name='BrightPath', location='Dhaka'
        )
        cls.job = cls.make_job('Junior Django Developer')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    @classmethod
    def make_job(cls, title, **extra):
        data = {
            'company': cls.company,
            'title': title,
            'description': 'Build web apps with Django.',
            'location': 'Dhaka',
            'job_type': 'full_time',
            'deadline': timezone.localdate() + timedelta(days=10),
            'is_active': True,
        }
        data.update(extra)
        return JobModel.objects.create(**data)

    def login(self, user):
        self.client.login(username=user.username, password='pass12345')

    @staticmethod
    def pdf(name='cv.pdf'):
        return SimpleUploadedFile(name, b'%PDF-1.4 test resume', content_type='application/pdf')


class AuthTests(BaseTestCase):
    def test_register_creates_profile_with_role(self):
        response = self.client.post(reverse('register_view'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'pass12345',
            'role': 'seeker',
        })
        self.assertRedirects(response, reverse('login_view'))
        user = User.objects.get(username='newuser')
        self.assertEqual(user.profilemodel.role, 'seeker')
        self.assertTrue(user.check_password('pass12345'))

    def test_employer_login_goes_to_dashboard(self):
        response = self.client.post(reverse('login_view'), {
            'username': 'employer1', 'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('employer_dashboard'), fetch_redirect_response=False)

    def test_seeker_login_goes_to_home(self):
        response = self.client.post(reverse('login_view'), {
            'username': 'seeker1', 'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('home_view'))

    def test_wrong_password_stays_on_login(self):
        response = self.client.post(reverse('login_view'), {
            'username': 'seeker1', 'password': 'wrong',
        })
        self.assertEqual(response.status_code, 200)


class AccessControlTests(BaseTestCase):
    def test_anonymous_redirected_to_login(self):
        url = reverse('employer_dashboard')
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login_view')}?next={url}")

    def test_seeker_blocked_from_employer_pages(self):
        self.login(self.seeker)
        for name in ['employer_dashboard', 'add_company', 'add_job']:
            response = self.client.get(reverse(name))
            self.assertRedirects(response, reverse('home_view'), msg_prefix=name)

    def test_employer_blocked_from_my_applications(self):
        self.login(self.employer)
        response = self.client.get(reverse('my_applications'))
        self.assertRedirects(response, reverse('home_view'))

    def test_employer_cannot_edit_other_employers_job(self):
        self.login(self.employer2)
        response = self.client.get(reverse('update_job', args=[self.job.id]))
        self.assertEqual(response.status_code, 404)

    def test_employer_cannot_delete_other_employers_job(self):
        self.login(self.employer2)
        response = self.client.post(reverse('delete_job', args=[self.job.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(JobModel.objects.filter(id=self.job.id).exists())

    def test_employer_cannot_view_other_employers_applicants(self):
        self.login(self.employer2)
        response = self.client.get(reverse('job_applicants', args=[self.job.id]))
        self.assertEqual(response.status_code, 404)


class EmployerJobTests(BaseTestCase):
    def test_dashboard_counts(self):
        self.make_job('Closed Job', is_active=False)
        self.login(self.employer)
        response = self.client.get(reverse('employer_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_jobs'], 2)
        self.assertEqual(response.context['active_jobs'], 1)

    def test_add_job_attaches_company(self):
        self.login(self.employer)
        response = self.client.post(reverse('add_job'), {
            'title': 'QA Intern',
            'description': 'Test things.',
            'location': 'Dhaka',
            'job_type': 'internship',
            'deadline': (timezone.localdate() + timedelta(days=5)).isoformat(),
            'is_active': 'on',
        })
        self.assertRedirects(response, reverse('employer_dashboard'))
        self.assertEqual(JobModel.objects.get(title='QA Intern').company, self.company)

    def test_update_job(self):
        self.login(self.employer)
        response = self.client.post(reverse('update_job', args=[self.job.id]), {
            'title': 'Senior Django Developer',
            'description': 'Updated.',
            'location': 'Dhaka',
            'job_type': 'full_time',
            'deadline': (timezone.localdate() + timedelta(days=5)).isoformat(),
            'is_active': 'on',
        })
        self.assertRedirects(response, reverse('employer_dashboard'))
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, 'Senior Django Developer')

    def test_delete_job(self):
        self.login(self.employer)
        self.client.post(reverse('delete_job', args=[self.job.id]))
        self.assertFalse(JobModel.objects.filter(id=self.job.id).exists())

    def test_salary_min_cannot_exceed_max(self):
        form = JobForm(data={
            'title': 'Bad Salary',
            'description': 'x',
            'location': 'Dhaka',
            'job_type': 'full_time',
            'salary_min': 50000,
            'salary_max': 20000,
            'deadline': timezone.localdate() + timedelta(days=5),
        })
        self.assertFalse(form.is_valid())


class ApplyJobTests(BaseTestCase):
    def apply(self, job=None, resume=None):
        job = job or self.job
        return self.client.post(reverse('apply_job', args=[job.id]), {
            'cover_letter': 'I would like to join.',
            'resume': resume or self.pdf(),
        })

    def test_seeker_can_apply(self):
        self.login(self.seeker)
        response = self.apply()
        self.assertRedirects(response, reverse('my_applications'))
        application = ApplicationModel.objects.get()
        self.assertEqual(application.user, self.seeker)
        self.assertEqual(application.job, self.job)
        self.assertEqual(application.status, 'pending')

    def test_duplicate_application_blocked(self):
        self.login(self.seeker)
        self.apply()
        self.apply()
        self.assertEqual(ApplicationModel.objects.count(), 1)

    def test_invalid_file_type_rejected(self):
        self.login(self.seeker)
        bad = SimpleUploadedFile('cv.txt', b'plain text', content_type='text/plain')
        response = self.apply(resume=bad)
        self.assertEqual(response.status_code, 200)
        self.assertIn('resume', response.context['form_data'].errors)
        self.assertEqual(ApplicationModel.objects.count(), 0)

    def test_large_file_rejected(self):
        self.login(self.seeker)
        big = SimpleUploadedFile('big.pdf', b'a' * (3 * 1024 * 1024), content_type='application/pdf')
        response = self.apply(resume=big)
        self.assertIn('resume', response.context['form_data'].errors)
        self.assertEqual(ApplicationModel.objects.count(), 0)

    def test_cannot_apply_to_inactive_job(self):
        closed = self.make_job('Closed', is_active=False)
        self.login(self.seeker)
        response = self.client.get(reverse('apply_job', args=[closed.id]))
        self.assertEqual(response.status_code, 404)

    def test_cannot_apply_after_deadline(self):
        expired = self.make_job('Expired', deadline=timezone.localdate() - timedelta(days=1))
        self.login(self.seeker)
        response = self.client.get(reverse('apply_job', args=[expired.id]))
        self.assertEqual(response.status_code, 404)

    def test_employer_cannot_apply(self):
        self.login(self.employer2)
        response = self.client.get(reverse('apply_job', args=[self.job.id]))
        self.assertRedirects(response, reverse('home_view'))


class ApplicationStatusTests(BaseTestCase):
    def setUp(self):
        self.application = ApplicationModel.objects.create(
            job=self.job, user=self.seeker, resume=self.pdf()
        )
        self.url = reverse('update_application_status', args=[self.application.id])

    def test_employer_can_shortlist(self):
        self.login(self.employer)
        response = self.client.post(self.url, {'status': 'shortlisted'})
        self.assertRedirects(response, reverse('job_applicants', args=[self.job.id]))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'shortlisted')

    def test_invalid_status_ignored(self):
        self.login(self.employer)
        self.client.post(self.url, {'status': 'hired'})
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'pending')

    def test_get_request_not_allowed(self):
        self.login(self.employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_other_employer_cannot_change_status(self):
        self.login(self.employer2)
        response = self.client.post(self.url, {'status': 'rejected'})
        self.assertEqual(response.status_code, 404)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'pending')

    def test_seeker_cannot_change_status(self):
        self.login(self.seeker)
        self.client.post(self.url, {'status': 'shortlisted'})
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'pending')

    def test_status_filter_on_applicants_page(self):
        self.login(self.employer)
        response = self.client.get(reverse('job_applicants', args=[self.job.id]), {'status': 'rejected'})
        self.assertEqual(len(response.context['applications']), 0)
        response = self.client.get(reverse('job_applicants', args=[self.job.id]), {'status': 'pending'})
        self.assertEqual(len(response.context['applications']), 1)


class HomePageTests(BaseTestCase):
    def test_hides_inactive_and_expired_jobs(self):
        self.make_job('Inactive Job', is_active=False)
        self.make_job('Expired Job', deadline=timezone.localdate() - timedelta(days=1))
        response = self.client.get(reverse('home_view'))
        titles = [job.title for job in response.context['page_obj']]
        self.assertEqual(titles, ['Junior Django Developer'])

    def test_search_by_keyword(self):
        self.make_job('Frontend Developer', description='Bootstrap and JavaScript.')
        response = self.client.get(reverse('home_view'), {'q': 'bootstrap'})
        titles = [job.title for job in response.context['page_obj']]
        self.assertEqual(titles, ['Frontend Developer'])

    def test_filter_by_job_type(self):
        self.make_job('QA Intern', job_type='internship')
        response = self.client.get(reverse('home_view'), {'job_type': 'internship'})
        titles = [job.title for job in response.context['page_obj']]
        self.assertEqual(titles, ['QA Intern'])

    def test_pagination_five_per_page(self):
        for i in range(6):
            self.make_job(f'Job {i}')
        first = self.client.get(reverse('home_view'))
        second = self.client.get(reverse('home_view'), {'page': 2})
        self.assertEqual(len(first.context['page_obj']), 5)
        self.assertEqual(len(second.context['page_obj']), 2)

    def test_profile_update_saves_skills(self):
        self.login(self.seeker)
        self.client.post(reverse('update_profile'), {
            'phone': '01700000000',
            'location': 'Dhaka',
            'skills': 'Django, HTML',
            'bio': 'Fresh graduate.',
        })
        self.seeker.profilemodel.refresh_from_db()
        self.assertEqual(self.seeker.profilemodel.skills, 'Django, HTML')