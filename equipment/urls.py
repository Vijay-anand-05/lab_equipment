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
    path("student/requested_apparatus/", views.requested_apparatus_view, name="requested_apparatus"),
    path('get_apparatus_details/', views.get_apparatus_details, name='get_apparatus_details'),
    path('student/payment_upload/', views.payment_upload, name='payment_upload'),
    path('student/manual', views.manual, name = "manual"),
    
    path('student/qr_code/', views.upload_qr, name='qr_code'),


    path('student/student_logout', views.student_logout, name = 'student_logout'),


    # ------------------------ FACULTY --------------


    path('faculty_login/', views.faculty_login, name='faculty_login'),
    # path('faculty_dashbord/', views.faculty_dashbord, name='faculty_dashbord'),



    path('technician_login', views.technician_login, name = 'technician_login'),
    # path('technician/technician_dashboard', views.technician_dashboard, name = 'technician_dashboard'),
    path('technician/add_subject', views.add_subject_type, name = 'add_subject_type'),
    path('technician/add_category', views.add_category, name = 'add_category'),
    path('technician/add_course', views.add_course, name = 'add_course'),
    path('technician/add_lab_exercise', views.add_lab_exercise, name = "add_lab_exercise"),
    path('technician/add_apparatus', views.add_apparatus, name = 'add_apparatus'),
    path('technician/add_batch', views.add_batch, name = 'add_batch'),
    path('technician/view_batches', views.view_batches, name='view_batches'),
    path('edit_lab_batch/<int:assignment_id>/', views.edit_lab_batch_assignment, name='edit_lab_batch_assignment'),
    
    path("technician/technician_dashboard", views.technician_dashboard, name="technician_dashboard"),
    path('technician/update_request_status/', views.update_apparatus_request_status, name='update_request_status'),
    path('technician/accept_or_reject_request/', views.accept_or_reject_apparatus_request, name='accept_or_reject_request'),
    
    path('technician/damaged_apparatus/', views.damaged_apparatus, name="damaged_apparatus"),  # Added missing slash
    
    # path('submit-damaged-apparatus/<int:return_request_id>/', views.submit_damaged_apparatus, name='submit_damaged_apparatus'),
    path("technician/payment_status/", views.payment_status, name = "payment_status"),
    path("payment-receipt/<int:request_id>/", views.generate_payment_pdf, name="generate_payment_pdf"),

    
    path('technician/review_payment_receipt', views.review_payment_receipt, name = 'review_payment_receipt'),

    


    path('technician/technician_logout', views.technician_logout, name = 'technician_logout'),
    
    
    
    
    path('hod/hod_dashboard', views.hod_dashboard, name = "hod_dashboard"),
    path('hod/approve_request/', views.approve_request, name='approve_request'),
    path("hod/hod_damaged_apparatus_view", views.hod_damaged_apparatus_view, name = "hod_damaged_apparatus_view"),
    path("hod/hod_overview", views.hod_overview, name = "hod_overview"),
    
    
    
    path('faculty/faculty_logout', views.faculty_logout, name = 'faculty_logout'),
    
    
    
    
    path("principle/principle_dashboard/", views.principle_dashboard, name = "principle_dashboard"),
    path("vice_principle/vice_principle_dashboard", views.vice_principle_dashboard, name = "vice_principle_dashboard"),
    
    
    

]
