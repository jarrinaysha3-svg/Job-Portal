# Job Portal

A full-stack job portal built with Django. Employers can post and manage jobs and review applicants, and job seekers can search for jobs and apply with a resume.

## Features

**Job seekers**
- Register and log in as a job seeker
- Search jobs by keyword, location, and job type, with pagination
- View job details and apply with a resume (PDF/DOC/DOCX, max 2 MB) and cover letter
- Track application status (Pending, Shortlisted, Rejected)
- View and edit a profile with name, email, phone, location, skills, and bio

**Employers**
- Register and log in as an employer
- Add and update a company profile
- Post, edit, and delete jobs, with salary range validation
- Dashboard with total jobs, active jobs, and application counts
- View applicants per job, download resumes, read cover letters
- Shortlist or reject applicants, and filter by status

**General**
- Role-based access control (employers and seekers cannot open each other's pages)
- Employers can only manage their own jobs and applicants
- Expired and inactive jobs are hidden from the public job list
- Automated tests for access rules, applications, and filtering

## Tech Stack

- Python, Django
- HTML, CSS, Bootstrap 5
- Django Crispy Forms (Bootstrap 5 template pack)
- SQLite

## Usage

1. Register one account as an **Employer** and one as a **Job Seeker**.
2. As the employer, add your company and post a job.
3. As the job seeker, search for the job and apply with a resume.
4. As the employer, open the applicants page to shortlist or reject.

## Author

Aysha Jarrin - [GitHub](https://github.com/jarrinaysha3-svg)

## Screenshots

<img width="1437" height="812" alt="Screenshot 2026-10-31 at 11 50 45 PM" src="https://github.com/user-attachments/assets/627d1514-e0b0-466a-951e-f8c1fcd5e53f" />
<img width="1440" height="811" alt="Screenshot 2026-10-31 at 11 52 31 PM" src="https://github.com/user-attachments/assets/21b97c84-ac50-4482-bc75-ae31ec917abd" />
<img width="1440" height="810" alt="Screenshot 2026-10-31 at 11 52 57 PM" src="https://github.com/user-attachments/assets/9c10051f-8cf6-4415-a005-f77ce09b4bcd" />
<img width="1440" height="811" alt="Screenshot 2026-10-31 at 11 51 14 PM" src="https://github.com/user-attachments/assets/73d67acc-39f7-48f0-b373-bd0d7cbb642e" />
