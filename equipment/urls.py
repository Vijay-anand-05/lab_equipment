from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    #------------------------- STUDENT ----------------

    path('student_login/', views.student_login, name='student_login'),
    path('student/student_dashbord/', views.student_dashboard, name='student_dashboard'),
    path('student/dashboard/slip/', views.slip, name='slip'),
    path('student/student_profile', views.student_profile, name = 'student_profile'),
    path('student/apparatus_request', views.apparatus_request, name = "apparatus_request"),
    



    path('student/student_logout', views.student_logout, name = 'student_logout'),


    # ------------------------ FACULTY --------------


    path('faculty_login/', views.faculty_login, name='faculty_login'),
    path('faculty_dashbord/', views.faculty_dashbord, name='faculty_dashbord'),



    path('technician_login', views.technician_login, name = 'technician_login'),
    path('technician/technician_dashboard', views.technician_dashboard, name = 'technician_dashboard'),
    path('technician/add_subject', views.add_subject_type, name = 'add_subject_type'),
    path('technician/add_category', views.add_category, name = 'add_category'),
    path('technician/add_course', views.add_course, name = 'add_course'),
    path('technician/add_lab_exercise', views.add_lab_exercise, name = "add_lab_exercise"),
    path('technician/add_apparatus', views.add_apparatus, name = 'add_apparatus'),
    path('technician/add_batch', views.add_batch, name = 'add_batch'),
    path('view_batches/', views.view_batches, name='view_batches'),
    path('edit_lab_batch/<int:assignment_id>/', views.edit_lab_batch_assignment, name='edit_lab_batch_assignment'),
    


    path('technician/technician_logout', views.technician_logout, name = 'technician_logout'),

]
