from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, User
from django.contrib import messages
import hashlib


def encrypt_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def home(request):
    return render(request, "home.html")


#################################student####################################

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Student_cgpa


def student_login(request):
    if request.method == "POST":
        student_regno = request.POST.get("regno")
        student_password = request.POST.get("password")

        try:
            student = Student.objects.using("placement_portal").get(
                student_regno=student_regno
            )
            if student.student_password == encrypt_password(student_password):  # Use hashing if passwords are encrypted
                request.session["student_regno"] = student_regno  # Store student regno in session

                # Retrieve the department from Student_cgpa
                student_details = Student_cgpa.objects.using("rit_cgpatrack").get(reg_no=student_regno)
                request.session["department"] = student_details.department  # Store department in session
                department = request.session["department"]
                print(department)

                return redirect("student_dashboard")
            else:
                messages.error(request, "Invalid registration number or password")

        except Student.DoesNotExist:
            messages.error(request, "Student not found")
        except Student_cgpa.DoesNotExist:
            messages.error(request, "Student details not found")

    return render(request, "student_login.html")


# Custom decorator for student authentication
def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if "student_regno" not in request.session:  # Check if student is logged in
            return redirect("/student_login?next=" + request.path)
        return view_func(request, *args, **kwargs)

    return wrapper


from django.shortcuts import render
from .models import Student_cgpa, LabBatchAssignment


@student_required  # Ensure the user is logged in as a student.
def student_dashboard(request):
    student_regno = request.session.get("student_regno")
    if not student_regno:
        return render(
            request,
            "error.html",
            {"message": "Student registration number not found in session."},
        )

    try:
        # Retrieve student details
        student_details = Student_cgpa.objects.using("rit_cgpatrack").get(
            reg_no=student_regno
        )
    except Student_cgpa.DoesNotExist:
        return render(request, "error.html", {"message": "Student details not found."})

    # Retrieve student's lab batch assignments
    student_assignments = LabBatchAssignment.objects.filter(
        student=student_details
    ).order_by("created_at")

    # Organize lab batch members by Course Code and Lab Batch No
    lab_batch_members = {}
    for assignment in student_assignments:
        course_code = assignment.course_code
        lab_batch_no = assignment.lab_batch_no

        if course_code not in lab_batch_members:
            lab_batch_members[course_code] = {}

        if lab_batch_no not in lab_batch_members[course_code]:
            lab_batch_members[course_code][lab_batch_no] = []

        # Add all students assigned to this batch
        lab_batch_members[course_code][lab_batch_no] = list(
            LabBatchAssignment.objects.filter(lab_batch_no=lab_batch_no)
            .order_by("created_at")
        )

    context = {
        "student_details": student_details,
        "student_assignments": student_assignments,  # List of assignments
        "lab_batch_members": lab_batch_members,  # Members grouped by course & batch
    }
    return render(request, "student/student_dashboard.html", context)



@student_required
def slip(request):
    return render(request, "student/apparatus_slip.html")


@student_required
def student_profile(request):
    student_regno = request.session.get("student_regno")
    if not student_regno:
        return render(
            request,
            "error.html",
            {"message": "Student registration number not found in session."},
        )

    try:
        student_details = Student_cgpa.objects.using("rit_cgpatrack").get(
            reg_no=student_regno
        )
    except Student_cgpa.DoesNotExist:
        return render(request, "error.html", {"message": "Student details not found."})

    context = {"student_details": student_details}
    return render(request, "student/student_profile.html", context)


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Apparatus, ApparatusRequest, LabBatchAssignment, Course

def apparatus_request(request):
    # Retrieve student details
    student_regno = request.session.get("student_regno")
    student_department = request.session.get("department")

    if not student_department:
        messages.error(request, "Department information is missing. Please log in again.")
        return redirect("student_dashboard")

    # Get relevant course codes for the student's department
    dept_course_codes = list(
        Course.objects.filter(department=student_department).values_list("course_code", flat=True)
    )

    # Fetch distinct values for dropdown filters
    ex_no_list = LabExercise.objects.filter(course_code__in=dept_course_codes).values_list("Ex_no", flat=True).distinct()
    course_code_list = dept_course_codes  # Already filtered by department
    practical_course_list = (
        LabExercise.objects.filter(course_code__in=dept_course_codes).values_list("practical_course", flat=True).distinct()
    )

    # Get filter values from GET request
    ex_no = request.GET.get("ex_no", "").strip()
    course_code = request.GET.get("course_code", "").strip()
    practical_course = request.GET.get("practical_course", "").strip()

    # Fetch apparatus based on filters
    apparatus_list = Apparatus.objects.none()  # Default: No apparatus
    experiment_name = None
    experiment_no = None

    if ex_no or course_code or practical_course:
        apparatus_list = Apparatus.objects.filter(course_code__in=dept_course_codes)

        if ex_no:
            apparatus_list = apparatus_list.filter(ex_no=ex_no)
        if course_code:
            apparatus_list = apparatus_list.filter(course_code=course_code)
        if practical_course:
            apparatus_list = apparatus_list.filter(practical_course=practical_course)

        # Fetch experiment details if apparatus exists
        if apparatus_list.exists():
            first_apparatus = apparatus_list.first()
            experiment_name = first_apparatus.experiment_name
            experiment_no = first_apparatus.ex_no

    # Handle POST request (Submit Apparatus Request)
    if request.method == "POST" and apparatus_list.exists():
        # Fetch student's lab batch assignment
        lab_batch = LabBatchAssignment.objects.filter(student_id=student_regno).first()
        if not lab_batch:
            messages.error(request, "You are not assigned to any lab batch.")
            return redirect("apparatus_request")

        apparatus_requests = [
            ApparatusRequest(
                student_id=student_regno,
                lab_batch=lab_batch,
                apparatus=apparatus,
                course_code=apparatus.course_code,
                status="Pending",
            )
            for apparatus in apparatus_list
        ]

        ApparatusRequest.objects.bulk_create(apparatus_requests)
        messages.success(request, "Apparatus request submitted successfully!")
        return redirect("apparatus_request")

    context = {
        "apparatus_list": apparatus_list,
        "experiment_name": experiment_name,
        "experiment_no": experiment_no,
        "ex_no_list": ex_no_list,
        "course_code_list": course_code_list,
        "practical_course_list": practical_course_list,
        "student_department": student_department,
    }

    return render(request, "student/apparatus_request.html", context)




from django.shortcuts import render
from django.db.models import Count
from .models import ApparatusRequest, Student_cgpa, LabExercise, LabBatchAssignment

import logging
from datetime import timedelta
from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncMinute
from .models import (
    Student_cgpa,
    LabBatchAssignment,
    ApparatusRequest,
    LabExercise,
)

logger = logging.getLogger(__name__)

def requested_apparatus_view(request):
    student_regno = request.session.get("student_regno")

    # 🔹 1. Get the logged-in student's details
    try:
        student = Student_cgpa.objects.using("rit_cgpatrack").get(reg_no=student_regno)
    except Student_cgpa.DoesNotExist:
        return render(request, "student/requested_apparatus.html", {"error": "Student not found"})

    # 🔹 2. Find the lab batch the student is assigned to
    assigned_batches = LabBatchAssignment.objects.filter(student=student).values_list("lab_batch_no", flat=True)

    if not assigned_batches:
        return render(request, "student/requested_apparatus.html", {"error": "No lab batch assigned."})

    # 🔹 3. Find all students assigned to the same lab batch
    batch_students = LabBatchAssignment.objects.filter(lab_batch_no__in=assigned_batches).values_list("student__reg_no", flat=True)

    # 🔹 4. Get all apparatus requests made by students in the same lab batch
    qs = ApparatusRequest.objects.filter(student__reg_no__in=batch_students)

    qs = qs.annotate(request_minute=TruncMinute("request_date"))

    grouped = (
        qs.values(
            "student__reg_no",
            "lab_batch__course_code",
            "apparatus__ex_no",
            "apparatus__department",
            "lab_batch__lab_batch_no",
            "status",
            "request_minute",
            "apparatus__experiment_name",
            "apparatus__practical_course",
        )
        .annotate(apparatus_count=Count("id"))
        .order_by("student__reg_no", "lab_batch__lab_batch_no", "request_minute")
    )

    grouped_list = list(grouped)

    for group in grouped_list:
        student_reg = group["student__reg_no"]
        course = group["lab_batch__course_code"]
        exp_no = group["apparatus__ex_no"]
        dept = group["apparatus__department"]
        lab_batch = group["lab_batch__lab_batch_no"]
        req_min = group["request_minute"]

        # 🔹 Fetch apparatus details from `ApparatusRequest`
        details_qs = ApparatusRequest.objects.filter(
            student__reg_no=student_reg,
            lab_batch__course_code=course,
            apparatus__ex_no=exp_no,
            apparatus__department=dept,
            lab_batch__lab_batch_no=lab_batch,
            request_date__gte=req_min,
            request_date__lt=req_min + timedelta(minutes=1),
        )

        if details_qs.exists():
            # ✅ Apparatus exists, fetch details from `ApparatusRequest`
            group["details"] = list(
                details_qs.values(
                    "apparatus__apparatus_name",
                    "apparatus__range_specification",
                    "apparatus__quantity_available",
                )
            )
        else:
            # 🔹 No apparatus found, fetch details from `LabExercise`
            lab_exercise_qs = LabExercise.objects.filter(course_code=course, Ex_no=exp_no).values(
                "experiment_name", "practical_course"
            )

            if lab_exercise_qs.exists():
                lab_exercise_data = lab_exercise_qs.first()  # Fetch first matching record
                group["details"] = [
                    {
                        "apparatus__apparatus_name": "N/A",
                        "apparatus__range_specification": "N/A",
                        "apparatus__quantity_available": "N/A",
                        "experiment_name": lab_exercise_data["experiment_name"],
                        "practical_course": lab_exercise_data["practical_course"],
                    }
                ]
            else:
                group["details"] = [{"error": "No apparatus or experiment data found"}]

    context = {
        "student_name": student.student_name,
        "department": student.department,
        "student_reg_no": student.reg_no,
        "grouped_requests": grouped_list,
    }

    return render(request, "student/requested_apparatus.html", context)




from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import ApparatusRequest


def get_apparatus_details(request):
    """Fetch apparatus details for a given experiment number and batch number."""
    experiment_no = request.GET.get("experiment_no")
    batch_no = request.GET.get("batch_no")

    apparatus_list = ApparatusRequest.objects.filter(
        lab_batch__ex_no=experiment_no, lab_batch__lab_batch_no=batch_no
    ).values(
        "apparatus__apparatus_name",
        "apparatus__range_specification",
        "apparatus__quantity_available",
    )

    html = render_to_string(
        "student/apparatus_details.html", {"apparatus_list": apparatus_list}
    )
    return JsonResponse(html, safe=False)


from .forms import *
from .models import Payment
def payment_upload(request):
    # student = request.user  # Assuming the student is logged in
    student = Student_cgpa.objects.using('rit_cgpatrack').all().first()  # Get the student from the database
    payment = Payment.objects.filter(student=student).first()  # Get the student's payment entry

    if request.method == "POST":
        form = PaymentProofForm(request.POST, request.FILES, instance=payment)
        if form.is_valid():
            # form.save()
            return redirect("payment_page")  # Refresh page after upload

    else:
        form = PaymentProofForm(instance=payment)

    return render(request, "student\payment_upload.html", {"form": form, "payment": payment})





@student_required
def student_logout(request):
    logout(request)  # Clears session
    # request.session.flush()  # Ensure all session data is cleared
    messages.success(request, "You have been logged out successfully.")
    return redirect("student_login")


###################################faculty######################################


def faculty_login(request):
    if request.method == "POST":
        username = request.POST.get("username")  # This will map to `staff_id`
        password = request.POST.get("password")

        print(
            f"Attempting to log in with staff_id: {username} and password: {password}"
        )
        
        # Custom authentication check
        try:
            user = User.objects.using("rit_e_approval").get(staff_id=username)
            if encrypt_password(password) == user.Password:
                if user.role == "HOD":
                    
                    print(
                    encrypt_password(password), user.Password
                )  # Assuming passwords are hashed
                    print("Authentication successful!")

                # Create a session or any custom login logic
                    request.session["user_id"] = user.id  # Store user ID in session
                    request.session["role"] = user.role  # Store the role if needed

                    return redirect("hod_dashboard")  # Redirect to the appropriate page
                else:
                    print('failed')
            else:
                print("Authentication failed! Incorrect password.")
        except User.DoesNotExist:
            print("Authentication failed! User not found.")

        return render(request, "faculty_login.html", {"error": "Invalid credentials!"})

    return render(request, "faculty_login.html")




from django.contrib.auth.decorators import login_required

# @login_required
# def faculty_dashbord(request):
#     return render(request, "faculty/faculty_dashbord.html")


# _---------------------------- TECHNICIAN -------------------------------------------------------------

from django.contrib.auth import authenticate, login

# def technician_login(request):
#     if request.method == "POST":
#         username = request.POST.get('username')  # Maps to `staff_id`
#         password = request.POST.get('password')

#         try:
#             user = User.objects.using('rit_e_approval').get(staff_id=username)
#             if encrypt_password(password) == user.Password:
#                 # ✅ Store session data
#                 request.session['user_id'] = user.id
#                 request.session['role'] = user.role
#                 request.session['department'] = user.Department

#                 print(f'Session Data: {request.session.items()}')  # Debugging

#                 return redirect('technician_dashboard')
#             else:
#                 return render(request, 'technician_login.html', {'error': 'Invalid credentials!'})
#         except User.DoesNotExist:
#             return render(request, 'technician_login.html', {'error': 'Invalid credentials!'})

#     return render(request, 'technician_login.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .models import User  # Import User model
# from .utils import encrypt_password  # Ensure encrypt_password is correctly imported


from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import User
from .backends import CustomUserBackend  # Import the custom backend

from django.contrib import messages
from django.shortcuts import render, redirect
from .models import User
from django.utils.http import url_has_allowed_host_and_scheme

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import User  # Ensure this is a Django user model
from django.utils.http import url_has_allowed_host_and_scheme

from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from .models import User  # Import your custom User model

def encrypt_password(password):
    # Replace this with your actual password encryption logic
    # For example, if you are using SHA-256:
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def technician_login(request):
    print("dsfslks", request.method)  # Debugging
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        next_url = request.GET.get("next")
        print(username, password)
        try:
            # Fetch the user from the database
            user = User.objects.using("rit_e_approval").get(staff_id=username)
            print(user)  # Debugging

            # Check if the password matches
            if encrypt_password(password) == user.Password:
                if user.role == "Technician":
                    # Manually log in the user
                    request.session['user_id'] = user.id  # Store user ID in session
                    request.session['user_role'] = user.role  # Store user role in session

                    print(f"Logged in User: {user}")  # Debugging

                    # Ensure `next_url` is safe before redirecting
                    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                        return redirect(next_url)

                    return redirect("technician_dashboard")
                else:
                    messages.error(request, "You are not authorized to log in as a technician.")
            else:
                messages.error(request, "Invalid credentials!")

        except User.DoesNotExist:
            messages.error(request, "User not found!")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            print(e)  # Debugging

    return render(request, "technician_login.html")



import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncMinute
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from .models import ApparatusRequest
from django.contrib.auth import get_user_model

User = get_user_model()

# Helper function to get technician from session
def get_current_technician(request):
    # Assumes that 'user_id' is stored in the session during login
    user_id = request.session.get("user_id")
    if user_id:
        try:
            return User.objects.get(staff_id=user_id)
        except User.DoesNotExist:
            return None
    return None


import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncMinute
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import ApparatusRequest

User = get_user_model()

# Custom decorator to check technician authentication
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from equipment.models import User  # Ensure correct import


# Technician login view
# def technician_login(request):
#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")
#         next_url = request.GET.get("next")

#         try:
#             user = User.objects.using("rit_e_approval").get(staff_id=username)
#             if encrypt_password(password) == user.Password:
#                 request.session["user_id"] = user.staff_id
#                 request.session["role"] = user.role
#                 request.session["department"] = user.Department

#                 return redirect(next_url if next_url else "technician_dashboard")
#             else:
#                 messages.error(request, "Invalid credentials!")
#         except User.DoesNotExist:
#             messages.error(request, "User  not found!")

#     return render(request, "technician_login.html")


# Technician dashboard view
from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncMinute
from datetime import timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)

from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncMinute
from datetime import timedelta
import logging
from .models import ApparatusRequest, Course
# from .decorators import technician_required  # Ensure technician authentication

logger = logging.getLogger(__name__)

DEPARTMENT_MAPPING = {
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
    "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
    "INFORMATION TECHNOLOGY": "B.TECH IT",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
    "MECHANICAL ENGINEERING": "B.E ME",
}

def technician_dashboard(request):
    user_id = request.session.get("user_id", None)
    if user_id is None:
        return redirect("/hod_login")

    # Fetch logged-in technician's data
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    
    # Check if user is a technician and get department
    if user_data.role != "Technician":
        return redirect("/hod_login")

    # Map department name using the dictionary
    technician_department = DEPARTMENT_MAPPING.get(user_data.Department, user_data.Department)

    # Get filters from request
    status_filter = request.GET.get("status", "Pending")
    batch = request.GET.get("batch")
    course_code = request.GET.get("course_code")
    lab_batch_no = request.GET.get("lab_batch_no")
    experiment_no = request.GET.get("experiment_no")

    # Fetch only requests related to the mapped technician's department
    qs = ApparatusRequest.objects.filter(status=status_filter, apparatus__department=technician_department)

    # Apply additional filters if provided
    if batch:
        qs = qs.filter(apparatus__batch=batch)
    if course_code:
        qs = qs.filter(lab_batch__course_code=course_code)
    if lab_batch_no:
        qs = qs.filter(lab_batch__lab_batch_no=lab_batch_no)
    if experiment_no:
        qs = qs.filter(apparatus__ex_no=experiment_no)

    logger.debug(f"Filtered QuerySet: {qs.query}")

    qs = qs.annotate(request_minute=TruncMinute("request_date"))

    grouped = (
        qs.values(
            "student__reg_no",
            "lab_batch__course_code",
            "apparatus__ex_no",
            "apparatus__department",
            "lab_batch__lab_batch_no",
            "status",
            "request_minute",
        )
        .annotate(apparatus_count=Count("id"))
        .order_by("student__reg_no", "lab_batch__lab_batch_no", "request_minute")
    )

    grouped_list = list(grouped)

    for group in grouped_list:
        student_reg = group["student__reg_no"]
        course = group["lab_batch__course_code"]
        exp_no = group["apparatus__ex_no"]
        dept = group["apparatus__department"]
        lab_batch = group["lab_batch__lab_batch_no"]
        req_min = group["request_minute"]

        details_qs = ApparatusRequest.objects.filter(
            student__reg_no=student_reg,
            lab_batch__course_code=course,
            apparatus__ex_no=exp_no,
            apparatus__department=dept,
            lab_batch__lab_batch_no=lab_batch,
            request_date__gte=req_min,
            request_date__lt=req_min + timedelta(minutes=1),
        )
        group["details"] = list(
            details_qs.values(
                "apparatus__apparatus_name",
                "apparatus__range_specification",
                "apparatus__quantity_available",
            )
        )

    def sorted_list(qs_values):
        return sorted(list(set(qs_values)))

    page_name = "technician_dashboard"
    context = {
        "grouped_requests": grouped_list,
        "status_filter": status_filter,
        "status_choices": ["Pending", "Accepted", "Rejected", "Returned", "Damaged"],
        "department_list": sorted_list(
            ApparatusRequest.objects.filter(apparatus__department=technician_department)
            .values_list("apparatus__department", flat=True)
        ),
        "batch_list": sorted_list(
            ApparatusRequest.objects.filter(apparatus__department=technician_department).values_list("apparatus__batch", flat=True)
        ),
        "course_code_list": sorted_list(
            ApparatusRequest.objects.filter(apparatus__department=technician_department).values_list("lab_batch__course_code", flat=True)
        ),
        "lab_batch_no_list": sorted_list(
            ApparatusRequest.objects.filter(apparatus__department=technician_department).values_list("lab_batch__lab_batch_no", flat=True)
        ),
        "experiment_no_list": sorted_list(
            ApparatusRequest.objects.filter(apparatus__department=technician_department).values_list("apparatus__ex_no", flat=True)
        ),
        "page_name": page_name
    }
    
    return render(request, "technician/technician_dashboard.html", context)




# Accept or reject apparatus request



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from datetime import timedelta
import json
from .models import ApparatusRequest, Course
# from .decorators import technician_required / # Ensure you have a decorator for authentication

from .models import Student_cgpa  # Adjust the import based on your project structure

def get_student_department(reg_no):
    try:
        student = Student_cgpa.objects.using('rit_cgpatrack').get(reg_no=reg_no)
        return student.department
    except Student_cgpa.DoesNotExist:
        return None  # or handle the case where the student does not exist


@csrf_exempt  # Use proper CSRF handling in production
  
def accept_or_reject_apparatus_request(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            student_reg = data.get("student_reg")
            course_code = data.get("course")
            exp_no = data.get("exp_no")
            lab_batch = data.get("lab_batch")
            req_min_str = data.get("request_minute")
            new_status = data.get("status")

            req_min = parse_datetime(req_min_str)
            if not req_min:
                return JsonResponse(
                    {"success": False, "message": "Invalid request minute."}
                )

            if new_status not in ["Accepted", "Rejected"]:
                return JsonResponse({"success": False, "message": "Invalid status."})

            # Get the student's department
            student_department = get_student_department(student_reg)
            print(student_reg)
            if not student_department:
                return JsonResponse({"success": False, "message": "Student not found."})

            # Get the course department based on the course code
            try:
                course = Course.objects.get(course_code=course_code)
                course_dept = course.department
            except Course.DoesNotExist:
                return JsonResponse({"success": False, "message": "Course not found."})

            # Check if the technician's department matches the student's department
            if course_dept != student_department:
                return JsonResponse(
                    {"success": False, "message": "You are not authorized to process this request."}
                )

            updated = ApparatusRequest.objects.filter(
                student__reg_no=student_reg,
                lab_batch__course_code=course_code,
                apparatus__ex_no=exp_no,
                apparatus__department=student_department,  # Use the student's department
                lab_batch__lab_batch_no=lab_batch,
                request_date__gte=req_min,
                request_date__lt=req_min + timedelta(minutes=1),
                status="Pending",
            ).update(status=new_status)

            if updated:
                return JsonResponse(
                    {"success": True, "message": f"Request updated to {new_status}."}
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No matching records found or already processed.",
                    }
                )
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request method."})

@csrf_exempt  # Use proper CSRF handling in production
  
def update_apparatus_request_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            student_reg = data.get("student_reg")
            course = data.get("course")
            exp_no = data.get("exp_no")
            dept = data.get("dept")
            lab_batch = data.get("lab_batch")
            req_min_str = data.get("request_minute")
            new_status = data.get("status")

            req_min = parse_datetime(req_min_str)
            if not req_min:
                return JsonResponse(
                    {"success": False, "message": "Invalid request minute."}
                )

            if new_status not in ["Returned", "Damaged"]:
                return JsonResponse({"success": False, "message": "Invalid status."})

            updated = ApparatusRequest.objects.filter(
                student__reg_no=student_reg,
                lab_batch__course_code=course,
                apparatus__ex_no=exp_no,
                apparatus__department=dept,
                lab_batch__lab_batch_no=lab_batch,
                request_date__gte=req_min,
                request_date__lt=req_min + timedelta(minutes=1),
                status="Accepted",
            ).update(status=new_status)

            if updated:
                return JsonResponse(
                    {"success": True, "message": f"Group updated to {new_status}."}
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "No matching records found or not in accepted state.",
                    }
                )
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
    return JsonResponse({"success": False, "message": "Invalid request method."})


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SubjectType, Category
from django.contrib.auth.decorators import login_required


  
def add_subject_type(request):
    if request.method == "POST":
        type_name = request.POST.get("type_name")
        if type_name:
            if SubjectType.objects.filter(type_name=type_name).exists():
                messages.error(request, "This subject type already exists.")
            else:
                SubjectType.objects.create(type_name=type_name)
                messages.success(request, "Subject type added successfully.")
                return redirect("add_subject_type")
    subject_types = SubjectType.objects.all()
    return render(
        request, "technician/add_subject_type.html", {"subject_types": subject_types}
    )


from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Category
from django.contrib.auth.decorators import login_required


  
def add_category(request):
    if request.method == "POST":
        category_name = request.POST.get("category_name")

        if category_name:
            # Check if category already exists
            if Category.objects.filter(category_name=category_name).exists():
                messages.error(request, "Category already exists.")
            else:
                Category.objects.create(category_name=category_name)
                messages.success(request, "Category added successfully!")
                return redirect("add_category")  # Redirect after success
        else:
            messages.error(request, "Category name cannot be empty.")

    return render(request, "technician/add_category.html")


from django.shortcuts import render, redirect
from django.contrib import messages
from equipment.models import *
from .forms import CourseForm


  
def add_course(request):
    # Get the logged-in technician user ID
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/technician_login")  # Redirect to technician login

    # Retrieve technician details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()  # Ensure consistency

    # 🔹 Map technician department to student department format
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)
    print(mapped_department)

    # Check if the user is a Technician
    if user_data.role != "Technician":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/some_dashboard")

    if request.method == "POST":
        form = CourseForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Course added successfully!")
            return redirect("add_course")
        else:
            print("Form Errors:", form.errors)  # Debugging
            messages.error(request, f"Error adding course: {form.errors}")

    else:
        form = CourseForm()

    # 🔹 Filter departments to only the **technician's mapped department**
    department_list = (
        Student_cgpa.objects.using("rit_cgpatrack")
        .filter(department__iexact=mapped_department)  # ✅ Only mapped department
        .values_list("department", flat=True)
        .distinct()
    )

    sem = list(range(1, 9))  # Semesters from 1 to 8

    return render(
        request,
        "technician/add_course.html",
        {"form": form, "departments": department_list, "sem": sem},
    )

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LabExercise, Course
from .forms import LabExerciseForm

def add_lab_exercise(request):
    # Get the logged-in technician user ID
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/technician_login")  # Redirect to technician login

    # Retrieve technician details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()  # Ensure consistency

    # 🔹 Map technician department to student department format
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)

    # Check if the user is a Technician
    if user_data.role != "Technician":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/some_dashboard")

    # 🔹 Filter Courses by the Technician's Department
    courses = Course.objects.filter(department__iexact=mapped_department)

    # 🔹 Filter Departments (Only the Technician's Mapped Department)
    departments = (
        Student_cgpa.objects.using("rit_cgpatrack")
        .filter(department__iexact=mapped_department)
        .values_list("department", flat=True)
        .distinct()
    )

    if request.method == "POST":
        form = LabExerciseForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Lab Exercise added successfully!")
                return redirect("add_lab_exercise")  # Redirect to prevent duplicate form submission
            except Exception as e:
                print("Database Save Error:", e)  # Debugging: Print DB errors
                messages.error(request, "Error saving to database.")
        else:
            print("Form Errors:", form.errors)  # Debugging: Print form errors
            messages.error(request, "Error adding lab exercise. Please check the form.")

    else:
        form = LabExerciseForm()

    sem = list(range(1, 9))
    batch_list = Course.objects.filter(department__iexact=mapped_department).values_list("batch", flat=True).distinct()
    regulation_list = Course.objects.filter(department__iexact=mapped_department).values_list("regulations", flat=True).distinct()

    context = {
        "form": form,
        "courses": courses,
        "sem": sem,
        "batches": batch_list,
        "regulations": regulation_list,
        "departments": departments,
    }

    return render(request, "technician/add_lab_exercise.html", context)

from django.shortcuts import render
from django.http import JsonResponse
import json
from .models import Apparatus, LabExercise


from django.shortcuts import render
from django.http import JsonResponse
import json
from .models import Apparatus, LabExercise, Student_cgpa

# Make sure to import your technician_required decorator
# from .decorators import technician_required


  
from django.shortcuts import render
from django.http import JsonResponse
import json
from .models import Apparatus, LabExercise, Student_cgpa, User

# Department Mapping
DEPARTMENT_MAPPING = {
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
    "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
    "INFORMATION TECHNOLOGY": "B.TECH IT",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
    "MECHANICAL ENGINEERING": "B.E ME",
}

def add_apparatus(request):
    # 🔹 Get the logged-in Technician user ID
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/technician_login")  # Redirect if not logged in

    # 🔹 Retrieve Technician details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()  # Normalize
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)

    # 🔹 Ensure only Technicians can access
    if user_data.role != "Technician":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/some_dashboard")

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("✅ Received Data:", data)  # Debugging

            # Extract and sanitize input data
            ex_no = str(data.get("ex_no", "")).strip()  # ✅ Keep it as CharField
            course_code = str(data.get("course_code", "")).strip()
            practical_course = str(data.get("practical_course", "")).strip()
            regulation = str(data.get("regulation", "")).strip()
            batch = str(data.get("batch", "")).strip()
            department = str(data.get("department", "")).strip()  # New field for department
            semester = data.get("semester")
            experiment_name = str(data.get("experiment_name", "")).strip()
            apparatus_entries = data.get("apparatus_entries", [])

            # ✅ Validate required fields
            if not all([ex_no, course_code, practical_course, regulation, batch, department, semester, experiment_name]):
                return JsonResponse({"error": "Missing required fields"}, status=400)

            # ✅ Ensure the selected department matches the technician’s mapped department
            if department != mapped_department:
                return JsonResponse({"error": "Unauthorized department selection"}, status=403)

            # ✅ Validate experiment existence
            try:
                lab_exercise = LabExercise.objects.get(
                    Ex_no=ex_no, Ex_title=experiment_name, department=mapped_department
                )
            except LabExercise.DoesNotExist:
                return JsonResponse(
                    {"error": "Invalid experiment number or experiment name"},
                    status=400,
                )

            print("✅ Found LabExercise:", lab_exercise)

            # ✅ Save apparatus data
            saved_apparatus = []
            for entry in apparatus_entries:
                apparatus_name = str(entry.get("apparatus_name", "")).strip()
                range_specification = str(entry.get("range_specification", "")).strip()
                quantity_available = str(entry.get("quantity_available", "")).strip()

                if apparatus_name and quantity_available:
                    apparatus = Apparatus.objects.create(
                        ex_no=ex_no,  # ✅ Store as CharField
                        course_code=course_code,
                        practical_course=practical_course,
                        experiment_name=experiment_name,
                        regulation=regulation,
                        batch=batch,
                        semester=semester,
                        apparatus_name=apparatus_name,
                        range_specification=range_specification,
                        quantity_available=quantity_available,
                        department=department,  # Save department field
                    )
                    saved_apparatus.append(apparatus.apparatus_name)

            print(f"✅ Apparatus saved successfully: {saved_apparatus}")
            return JsonResponse(
                {"message": "Apparatus saved successfully!"}, status=201
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            print(f"❌ Error: {e}")
            return JsonResponse({"error": str(e)}, status=400)

    # ✅ Load dropdown data efficiently, filtered by department
    sem_list = list(range(1, 9))
    dropdown_data = {
        "batches": list(
            LabExercise.objects.filter(department=mapped_department)
            .values_list("batch", flat=True)
            .distinct()
        ),
        "regulations": list(
            LabExercise.objects.filter(department=mapped_department)
            .values_list("regulations", flat=True)
            .distinct()
        ),
        "course_code": list(
            LabExercise.objects.filter(department=mapped_department)
            .values_list("course_code", flat=True)
            .distinct()
        ),
        "practical_course": list(
            LabExercise.objects.filter(department=mapped_department)
            .values_list("practical_course", flat=True)
            .distinct()
        ),
        "ex_no": list(
            LabExercise.objects.filter(department=mapped_department)
            .values_list("Ex_no", flat=True)
            .distinct()
        ),  # ✅ CharField values
        "experiment_name": list(
            LabExercise.objects.filter(department=mapped_department)
            .values_list("Ex_title", flat=True)
            .distinct()
        ),
        "sem": sem_list,
        "department_list": [mapped_department],  # Only show Technician's department
    }

    return render(request, "technician/add_apparatus.html", dropdown_data)




import itertools
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Student_cgpa, Course, LabExercise, LabBatchAssignment, User

# Department Mapping
DEPARTMENT_MAPPING = {
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
    "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
    "INFORMATION TECHNOLOGY": "B.TECH IT",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
    "MECHANICAL ENGINEERING": "B.E ME",
}

def add_batch(request):
    # 🔹 Get the logged-in Technician user ID
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/technician_login")  # Redirect if not logged in

    # 🔹 Retrieve Technician details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()  # Normalize
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)

    # 🔹 Ensure only Technicians can access
    if user_data.role != "Technician":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/some_dashboard")

    if request.method == "POST":
        lab_batch_no = request.POST.get("lab_batch_no", "").strip()
        course_code = request.POST.get("course_code", "").strip()
        experiment_no_input = request.POST.get("experiment_no", "").strip()
        assessment = request.POST.get("assessment", "").strip()
        selected_students = request.POST.getlist("selected_students")

        # ✅ Ensure the course belongs to the Technician's department
        if not LabExercise.objects.filter(course_code=course_code, department=mapped_department).exists():
            messages.error(request, "Unauthorized course selection.")
            return redirect("add_batch")

        # Retrieve available experiment numbers for the selected course
        exp_numbers = list(
            LabExercise.objects.filter(course_code=course_code)
                .values_list("Ex_no", flat=True)
                .distinct()
        )

        # Get experiment number for this course batch if already assigned
        existing_batch = LabBatchAssignment.objects.filter(
            lab_batch_no=lab_batch_no, course_code=course_code
        ).first()

        if existing_batch:
            exp_no = existing_batch.ex_no
        else:
            if experiment_no_input:
                exp_no = experiment_no_input
            else:
                last_assignment = LabBatchAssignment.objects.filter(course_code=course_code).order_by("-created_at").first()
                if last_assignment:
                    try:
                        last_index = exp_numbers.index(last_assignment.ex_no)
                        new_order = exp_numbers[last_index + 1:] + exp_numbers[:last_index + 1]
                        exp_cycle = itertools.cycle(new_order)
                    except ValueError:
                        exp_cycle = itertools.cycle(exp_numbers)
                else:
                    exp_cycle = itertools.cycle(exp_numbers)

                exp_no = next(exp_cycle)

        if not lab_batch_no:
            messages.error(request, "Please enter a lab batch number.")
        elif not selected_students:
            messages.error(request, "Please select at least one student.")
        else:
            success_count = 0
            duplicate_count = 0

            for reg_no in selected_students:
                try:
                    student = Student_cgpa.objects.using("rit_cgpatrack").get(reg_no=reg_no)

                    # ✅ Ensure the student belongs to the Technician's department
                    if student.department != mapped_department:
                        messages.warning(request, f"Student {reg_no} does not belong to your department. Skipping.")
                        continue  # Skip this student

                    # Check if student is already assigned to this batch for the same course, department, and section
                    existing_assignment = LabBatchAssignment.objects.filter(
                        student=student,
                        lab_batch_no=lab_batch_no,
                        course_code=course_code,
                        department=student.department,
                        section=student.section,
                    ).exists()

                    if existing_assignment:
                        duplicate_count += 1
                        messages.warning(request, f"Student {reg_no} is already assigned to this batch. Skipping.")
                        continue

                    # Assign student to lab batch
                    LabBatchAssignment.objects.create(
                        student=student,
                        lab_batch_no=lab_batch_no,
                        course_code=course_code,
                        ex_no=exp_no,
                        assessment=assessment,
                        department=student.department,
                        section=student.section,
                    )
                    success_count += 1
                except Student_cgpa.DoesNotExist:
                    messages.warning(request, f"Student with registration number {reg_no} does not exist.")
                    continue

            if success_count > 0:
                messages.success(request, f"Lab batch assignment saved for {success_count} student(s).")
            if duplicate_count > 0:
                messages.info(request, f"{duplicate_count} student(s) were already assigned and skipped.")
            if success_count == 0 and duplicate_count == 0:
                messages.error(request, "No lab batch assignments were made.")

            return redirect("add_batch")

    # GET request: Filtering students
    batch_filter = request.GET.get("batch", "").strip()
    department_filter = request.GET.get("department", "").strip()
    section_filter = request.GET.get("section", "").strip()
    course_code = request.GET.get("course_code", "").strip()

    filtered = batch_filter or department_filter or section_filter

    students = Student_cgpa.objects.using("rit_cgpatrack").none()
    if filtered:
        students = Student_cgpa.objects.using("rit_cgpatrack").filter(department=mapped_department)
        if batch_filter:
            students = students.filter(batch=batch_filter)
        if section_filter:
            students = students.filter(section=section_filter)
        students = students.order_by("-gender")

        # Exclude students already assigned to the same batch and course
        assigned_regnos = list(
            LabBatchAssignment.objects.filter(
                course_code=course_code,
                lab_batch_no=batch_filter,
                department=mapped_department,
                section=section_filter,
            ).values_list("student__reg_no", flat=True)
        )
        students = students.exclude(reg_no__in=assigned_regnos)

    # Retrieve filter options:
    batches = Course.objects.values_list("batch", flat=True).distinct()
    section_options = (
        Student_cgpa.objects.using("rit_cgpatrack")
        .values_list("section", flat=True)
        .distinct()
    )
    # Filter only department-specific courses
    course_codes = list(
        LabExercise.objects.filter(department=mapped_department)
        .values_list("course_code", flat=True)
        .distinct()
    )
    ex_nos = list(
        LabExercise.objects.filter(department=mapped_department)
        .values_list("Ex_no", flat=True)
        .distinct()
    )

    # Retrieve existing assignments
    lab_assignments = LabBatchAssignment.objects.filter(department=mapped_department).order_by("-created_at")

    context = {
        "students": students,
        "filtered": filtered,
        "batch_filter": batch_filter,
        "department_filter": department_filter,
        "section_filter": section_filter,
        "batches": batches,
        "departments": [mapped_department],  # Only the technician's department
        "section_options": section_options,
        "course_code": course_codes,
        "ex_no": ex_nos,
        "lab_assignments": lab_assignments,
    }
    return render(request, "technician/add_batch.html", context)



from django.shortcuts import render, redirect
from .models import LabBatchAssignment, LabExercise, User

# Department Mapping
DEPARTMENT_MAPPING = {
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
    "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
    "INFORMATION TECHNOLOGY": "B.TECH IT",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
    "MECHANICAL ENGINEERING": "B.E ME",
}

def view_batches(request):
    """
    Display Lab Batch Assignments for the Technician's department only when filters are applied.
    """
    # 🔹 Get the logged-in Technician user ID
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/technician_login")  # Redirect if not logged in

    # 🔹 Retrieve Technician details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()  # Normalize
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)

    # 🔹 Ensure only Technicians can access
    if user_data.role != "Technician":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/some_dashboard")

    # Retrieve filter values from GET request
    course_code_filter = request.GET.get("course_code", "").strip()
    section_filter = request.GET.get("section", "").strip()
    assessment_filter = request.GET.get("assessment", "").strip()
    lab_batch_no_filter = request.GET.get("lab_batch_no", "").strip()

    # Check if any filter is applied
    filters_applied = any([course_code_filter, section_filter, assessment_filter, lab_batch_no_filter])

    # Initially, do not fetch any records until at least one filter is applied
    assignments = LabBatchAssignment.objects.none()

    if filters_applied:
        assignments = LabBatchAssignment.objects.filter(department=mapped_department).order_by("-created_at")

        # Apply filters
        if course_code_filter:
            assignments = assignments.filter(course_code=course_code_filter)
        if section_filter:
            assignments = assignments.filter(section=section_filter)
        if assessment_filter:
            assignments = assignments.filter(assessment=assessment_filter)
        if lab_batch_no_filter:
            assignments = assignments.filter(lab_batch_no=lab_batch_no_filter)

    # Retrieve distinct values for dropdowns (only for the technician's department)
    course_codes = (
        LabExercise.objects.filter(department=mapped_department)
        .values_list("course_code", flat=True)
        .distinct()
        .order_by("course_code")
    )
    sections = (
        LabBatchAssignment.objects.filter(department=mapped_department)
        .values_list("section", flat=True)
        .distinct()
        .order_by("section")
    )
    lab_batches = (
        LabBatchAssignment.objects.filter(department=mapped_department)
        .values_list("lab_batch_no", flat=True)
        .distinct()
        .order_by("lab_batch_no")
    )
    assessments = (
        LabBatchAssignment.objects.filter(department=mapped_department)
        .values_list("assessment", flat=True)
        .distinct()
        .order_by("assessment")
    )

    context = {
        "assignments": assignments,
        "course_codes": course_codes,
        "sections": sections,
        "assessments": assessments,
        "lab_batch_nos": lab_batches,
        "filters_applied": filters_applied,
    }
    return render(request, "technician/view_batches.html", context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import LabBatchAssignment, LabExercise, User

# Department Mapping
DEPARTMENT_MAPPING = {
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
    "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
    "INFORMATION TECHNOLOGY": "B.TECH IT",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
    "MECHANICAL ENGINEERING": "B.E ME",
}

def edit_lab_batch_assignment(request, assignment_id):
    """
    Allow a technician to edit a Lab Batch Assignment, restricting access to their department only.
    """
    # 🔹 Get the logged-in Technician user ID
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/technician_login")  # Redirect if not logged in

    # 🔹 Retrieve Technician details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()  # Normalize
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)

    # 🔹 Retrieve the assignment (404 if not found)
    assignment = get_object_or_404(LabBatchAssignment, id=assignment_id)

    # 🔹 Ensure the technician can only edit assignments in their department
    if assignment.department != mapped_department:
        messages.error(request, "You are not authorized to edit this lab batch assignment.")
        return redirect("view_batches")

    # Retrieve available course codes and experiment numbers (only for technician's department)
    course_codes = (
        LabExercise.objects.filter(department=mapped_department)
        .values_list("course_code", flat=True)
        .distinct()
        .order_by("course_code")
    )
    ex_nos = (
        LabExercise.objects.filter(department=mapped_department)
        .values_list("Ex_no", flat=True)
        .distinct()
        .order_by("Ex_no")
    )

    if request.method == "POST":
        lab_batch_no = request.POST.get("lab_batch_no", "").strip()
        course_code = request.POST.get("course_code", "").strip()
        experiment_no = request.POST.get("experiment_no", "").strip()
        assessment = request.POST.get("assessment", "").strip()

        if not lab_batch_no:
            messages.error(request, "Lab batch number is required.")
        else:
            # 🔹 Update assignment (keeping department and section unchanged)
            assignment.lab_batch_no = lab_batch_no
            assignment.course_code = course_code
            assignment.ex_no = experiment_no
            assignment.assessment = assessment
            assignment.save()

            messages.success(request, "Lab batch assignment updated successfully.")
            return redirect("view_batches")  # Redirect to the batch list page

    context = {
        "assignment": assignment,
        "course_codes": course_codes,
        "ex_nos": ex_nos,
    }
    return render(request, "technician/edit_lab_batch.html", context)





# from .decorators import technician_required

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.db.models import Count
from .models import ApparatusRequest, Student_cgpa, LabBatchAssignment, LabExercise

# def damaged_apparatus(request):
#     page_name = "damaged_apparatus"

#     if request.method == "POST":
#         return_request_id = request.POST.get("return_request_id")
#         action = request.POST.get("action")  # Get the action (verify/not_verify)

#         if not return_request_id:
#             messages.error(request, "❌ Invalid request ID.")
#             return redirect("damaged_apparatus")

#         first_request = ApparatusRequest.objects.filter(id=return_request_id).first()

#         if not first_request:
#             messages.error(request, "❌ Request not found. Please try again.")
#             return redirect("damaged_apparatus")

#         reg_no = first_request.student_id
#         student = Student_cgpa.objects.using("rit_cgpatrack").filter(reg_no=reg_no).first()

#         if student:
#             student_reg_no = student.reg_no
#         else:
#             student_reg_no = first_request.student.reg_no  # Fallback

#         # Get all requests in the same group
#         related_requests = ApparatusRequest.objects.filter(
#             student__reg_no=student_reg_no,
#             lab_batch__course_code=first_request.lab_batch.course_code,
#             apparatus__ex_no=first_request.apparatus.ex_no,
#             apparatus__department=first_request.apparatus.department,
#             lab_batch__lab_batch_no=first_request.lab_batch.lab_batch_no,
#             request_date=first_request.request_date
#         )

#         # Retrieve selected apparatus IDs
#         selected_apparatus_ids = request.POST.getlist("selected_apparatus")

#         if not selected_apparatus_ids:
#             messages.error(request, "❌ No apparatus selected for update.")
#             return redirect("damaged_apparatus")

#         updated_count = 0  # Track successful updates

#         # Update only selected apparatus
#         for apparatus_id in selected_apparatus_ids:
#             fine_amount = request.POST.get(f"fine_amount_{apparatus_id}", 0)
#             technician_remarks = request.POST.get(f"remarks_{apparatus_id}", "")

#             updated = ApparatusRequest.objects.filter(
#                 id=apparatus_id
#             ).update(
#                 fine_amount=fine_amount,
#                 technician_remarks=technician_remarks
#             )

#             if updated:
#                 updated_count += 1

#         if updated_count == 0:
#             messages.error(request, "❌ No updates were made. Please check your selections.")
#             return redirect("damaged_apparatus")

#         # Handle verification action
#         if action == "verify":
#             related_requests.update(verified=True, verified_date=now())
#             messages.success(request, f"✅ {updated_count} apparatus successfully verified.")
#         elif action == "not_verify":
#             related_requests.update(verified=False, verified_date=None)
#             messages.warning(request, f"⚠️ Verification removed for {updated_count} apparatus.")
#         messages.success(request, f"✅ {updated_count} apparatus successfully verified.")

#         return redirect("damaged_apparatus")

#     # Filtering logic
#     department = request.GET.get("department")
#     course_code = request.GET.get("course_code")
#     approval_status = request.GET.get("approval_status")

#     qs = ApparatusRequest.objects.filter(status="Damaged")
#     if department:
#         qs = qs.filter(apparatus__department=department)
#     if course_code:
#         qs = qs.filter(lab_batch__course_code=course_code)
#     if approval_status:
#         qs = qs.filter(hod_approval=(approval_status == "approved"))

#     grouped_list = []
#     grouped = (
#         qs.values(
#             "student__reg_no", "lab_batch__course_code", "apparatus__ex_no", "apparatus__department",
#             "lab_batch__lab_batch_no", "request_date", "hod_approval"
#         )
#         .annotate(apparatus_count=Count("id"))
#         .order_by("student__reg_no", "lab_batch__lab_batch_no", "request_date")
#     )
    
#     for group in grouped:
#         details_qs = ApparatusRequest.objects.filter(
#             student__reg_no=group["student__reg_no"], lab_batch__course_code=group["lab_batch__course_code"],
#             apparatus__ex_no=group["apparatus__ex_no"], apparatus__department=group["apparatus__department"],
#             lab_batch__lab_batch_no=group["lab_batch__lab_batch_no"], request_date=group["request_date"]
#         )
#         first_request = details_qs.first()
#         group["request_id"] = first_request.id if first_request else None
#         group["technician_remarks"] = first_request.technician_remarks if first_request else ""
#         group["verified"] = all(req.verified for req in details_qs)  # Check if all items in group are verified
#         group["apparatus_list"] = [
#             {
#                 "id": detail.id,  # Change apparatus.id to detail.id to match ApparatusRequest ID
#                 "apparatus_name": detail.apparatus.apparatus_name,
#                 "range_specification": detail.apparatus.range_specification,
#                 "quantity_available": detail.apparatus.quantity_available,
#                 "fine_amount": detail.fine_amount or 0,  # Ensure fine amount is stored
#                 "remarks": detail.technician_remarks or "",
#             }
#             for detail in details_qs if detail.apparatus
#         ]
#         grouped_list.append(group)

#     departments = LabBatchAssignment.objects.values_list("department", flat=True).distinct().order_by("department")
#     course_codes = LabExercise.objects.values_list("course_code", flat=True).distinct().order_by("course_code")

#     context = {
#         "damaged_apparatus_requests": grouped_list,
#         "departments": departments,
#         "course_codes": course_codes,
#         "page_name": page_name
#     }
#     return render(request, "technician/damaged_apparatus.html", context)



from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from .models import (
    ApparatusRequest, ApparatusRequestDamage, Student_cgpa,
    LabBatchAssignment, LabExercise, User
)

# Department Mapping
DEPARTMENT_MAPPING = {
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
    "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
    "INFORMATION TECHNOLOGY": "B.TECH IT",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
    "MECHANICAL ENGINEERING": "B.E ME",
}

def damaged_apparatus(request):
    """
    Technician can view, verify, and update damaged apparatus records from their department.
    """
    page_name = "damaged_apparatus"

    # 🔹 Get the logged-in Technician user ID
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/technician_login")  # Redirect if not logged in

    # 🔹 Retrieve Technician details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()  # Normalize
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)

    if request.method == "POST":
        return_request_id = request.POST.get("return_request_id")
        action = request.POST.get("action")  # "verify" or "not_verify"

        if not return_request_id:
            messages.error(request, "❌ Invalid request ID.")
            return redirect("damaged_apparatus")

        first_request = ApparatusRequest.objects.filter(id=return_request_id).first()

        if not first_request:
            messages.error(request, "❌ Request not found.")
            return redirect("damaged_apparatus")

        # 🔹 Ensure technician can only manage their department’s apparatus
        if first_request.apparatus.department != mapped_department:
            messages.error(request, "❌ You are not authorized to update this apparatus.")
            return redirect("damaged_apparatus")

        reg_no = first_request.student_id
        student = Student_cgpa.objects.using("rit_cgpatrack").filter(reg_no=reg_no).first()
        student_reg_no = student.reg_no if student else first_request.student.reg_no

        # Get all related requests
        related_requests = ApparatusRequest.objects.filter(
            student__reg_no=student_reg_no,
            lab_batch__course_code=first_request.lab_batch.course_code,
            apparatus__ex_no=first_request.apparatus.ex_no,
            apparatus__department=mapped_department,  # 🔹 Restrict by technician department
            lab_batch__lab_batch_no=first_request.lab_batch.lab_batch_no,
            request_date=first_request.request_date
        )

        # Retrieve selected apparatus IDs
        selected_apparatus_ids = request.POST.getlist("selected_apparatus")
        if not selected_apparatus_ids:
            messages.error(request, "❌ No apparatus selected.")
            return redirect("damaged_apparatus")

        updated_count = 0  # Track successful updates

        # Process selected apparatus updates
        for apparatus_id in selected_apparatus_ids:
            fine_amount = request.POST.get(f"fine_amount_{apparatus_id}", 0)
            technician_remarks = request.POST.get(f"remarks_{apparatus_id}", "")

            try:
                fine_amount = float(fine_amount)  # Ensure valid fine amount
            except ValueError:
                messages.error(request, f"❌ Invalid fine amount for apparatus ID {apparatus_id}.")
                continue

            try:
                apparatus_request_obj = ApparatusRequest.objects.get(id=apparatus_id)
            except ApparatusRequest.DoesNotExist:
                messages.error(request, f"❌ Apparatus request with ID {apparatus_id} not found.")
                continue

            # Ensure the apparatus exists
            if not apparatus_request_obj.apparatus:
                messages.error(request, f"❌ Apparatus missing for request ID {apparatus_id}.")
                continue

            # Update or create the damage record
            obj, created = ApparatusRequestDamage.objects.update_or_create(
                apparatus_request=apparatus_request_obj,
                apparatus=apparatus_request_obj.apparatus,
                defaults={"fine_amount": fine_amount, "remarks": technician_remarks}
            )

            messages.success(
                request,
                f"✅ {'Added' if created else 'Updated'} fine/remarks for apparatus ID {apparatus_id}."
            )
            updated_count += 1

        if updated_count == 0:
            messages.error(request, "❌ No updates were made.")
            return redirect("damaged_apparatus")

        # Handle verification
        if action == "verify":
            related_requests.update(verified=True, verified_date=timezone.now())
            messages.success(request, f"✅ {updated_count} apparatus verified.")
        elif action == "not_verify":
            related_requests.update(verified=False, verified_date=None)
            messages.warning(request, f"⚠️ Verification removed for {updated_count} apparatus.")

        return redirect("damaged_apparatus")

    # 🔹 Filtered queryset - Only damaged apparatus from the technician's department
    qs = ApparatusRequest.objects.filter(status="Damaged", apparatus__department=mapped_department)

    # Apply filters
    department = request.GET.get("department")
    course_code = request.GET.get("course_code")
    approval_status = request.GET.get("approval_status")

    if department:
        qs = qs.filter(apparatus__department=department)
    if course_code:
        qs = qs.filter(lab_batch__course_code=course_code)
    if approval_status:
        qs = qs.filter(hod_approval=(approval_status == "approved"))

    grouped_list = []
    grouped = (
        qs.values(
            "student__reg_no", "lab_batch__course_code", "apparatus__ex_no", "apparatus__department",
            "lab_batch__lab_batch_no", "request_date", "hod_approval"
        )
        .annotate(apparatus_count=Count("id"))
        .order_by("student__reg_no", "lab_batch__lab_batch_no", "request_date")
    )

    for group in grouped:
        details_qs = ApparatusRequest.objects.filter(
            student__reg_no=group["student__reg_no"], lab_batch__course_code=group["lab_batch__course_code"],
            apparatus__ex_no=group["apparatus__ex_no"], apparatus__department=group["apparatus__department"],
            lab_batch__lab_batch_no=group["lab_batch__lab_batch_no"], request_date=group["request_date"]
        )
        first_request = details_qs.first()
        group["request_id"] = first_request.id if first_request else None
        group["verified"] = all(req.verified for req in details_qs)

        # Get fine amount and remarks from ApparatusRequestDamage
        damage_details = {
            entry.apparatus_request_id: {"fine_amount": entry.fine_amount or 0, "remarks": entry.remarks or ""}
            for entry in ApparatusRequestDamage.objects.filter(apparatus_request__in=details_qs)
        }

        group["apparatus_list"] = [
            {
                "id": detail.id,
                "apparatus_name": detail.apparatus.apparatus_name,
                "range_specification": detail.apparatus.range_specification,
                "quantity_available": detail.apparatus.quantity_available,
                "fine_amount": damage_details.get(detail.id, {}).get("fine_amount", 0),
                "remarks": damage_details.get(detail.id, {}).get("remarks", ""),
            }
            for detail in details_qs if detail.apparatus
        ]
        grouped_list.append(group)

    departments = LabBatchAssignment.objects.filter(department=mapped_department).values_list("department", flat=True).distinct().order_by("department")
    course_codes = LabExercise.objects.filter(department=mapped_department).values_list("course_code", flat=True).distinct().order_by("course_code")

    context = {
        "damaged_apparatus_requests": grouped_list,
        "departments": departments,
        "course_codes": course_codes,
        "page_name": page_name,
    }
    return render(request, "technician/damaged_apparatus.html", context)




# def submit_damaged_apparatus(request, return_request_id):
#     return_request = get_object_or_404(ApparatusRequest, id=return_request_id)

#     if request.method == "POST":
#         selected_apparatus_ids = request.POST.getlist("selected_apparatus")  # Get selected apparatus IDs
#         fine_amount = request.POST.get("fine_amount")
#         remarks = request.POST.get("remarks")  # Get remarks from the form

#         if selected_apparatus_ids:
#             # Clear existing damaged apparatus items
#             return_request.damaged_apparatus.clear()

#             # Add newly selected apparatus items
#             for apparatus_id in selected_apparatus_ids:
#                 selected_apparatus = get_object_or_404(Apparatus, id=int(apparatus_id))
#                 return_request.damaged_apparatus.add(selected_apparatus)

#             # Update other fields
#             return_request.fine_amount = fine_amount if fine_amount else 0
#             return_request.hod_approval = False  # Waiting for HOD Approval
#             return_request.request_type = "Return"  # Mark it as a return request
#             return_request.remarks = remarks  # Save the remarks
#             return_request.save()

#             messages.success(request, "Request sent to HOD for approval!")
#         else:
#             messages.error(request, "Please select at least one apparatus!")

#     return redirect("damaged_apparatus")



from django.shortcuts import render, redirect
from django.db.models import Sum, Count
from .models import LabBatchAssignment, LabExercise, ApparatusRequest, ApparatusRequestDamage, User

# Department Mapping for Consistency
DEPARTMENT_MAPPING = {
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
    "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
    "INFORMATION TECHNOLOGY": "B.TECH IT",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
    "MECHANICAL ENGINEERING": "B.E ME",
}

def payment_status(request):
    """
    Technician can view and filter payment statuses for damaged apparatus.
    """
    page_name = "payment_status"
    
    # Technician Authentication
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("/technician_login")
    
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)
    
    # Get filter values from request
    department = request.GET.get("department")
    course_code = request.GET.get("course_code")
    payment_status = request.GET.get("payment_status")  # Paid or Not Paid
    
    # Base queryset for damaged apparatus requests
    qs = ApparatusRequest.objects.filter(status="Damaged", apparatus__department=mapped_department)
    
    if department:
        qs = qs.filter(apparatus__department=department)
    if course_code:
        qs = qs.filter(lab_batch__course_code=course_code)
    if payment_status:
        qs = qs.filter(verified=(payment_status == "paid"))
    
    grouped_list = []
    grouped = (
        qs.values(
            "student__reg_no", "lab_batch__course_code", "apparatus__ex_no", "apparatus__department",
            "lab_batch__lab_batch_no", "status", "verified"
        )
        .annotate(total_fine=Sum("apparatusrequestdamage__fine_amount"))
        .order_by("student__reg_no", "lab_batch__lab_batch_no")
    )
    
    for group in grouped:
        details_qs = ApparatusRequest.objects.filter(
            student__reg_no=group["student__reg_no"],
            lab_batch__course_code=group["lab_batch__course_code"],
            apparatus__ex_no=group["apparatus__ex_no"],
            apparatus__department=group["apparatus__department"],
            lab_batch__lab_batch_no=group["lab_batch__lab_batch_no"],
        )
        
        first_request = details_qs.first()
        group["request_id"] = first_request.id if first_request else None
        group["remarks"] = first_request.technician_remarks if first_request else ""
        
        damage_details = {
            entry.apparatus_request_id: {"fine_amount": entry.fine_amount or 0, "remarks": entry.remarks or ""}
            for entry in ApparatusRequestDamage.objects.filter(apparatus_request__in=details_qs)
        }
        
        group["apparatus_list"] = [
            {
                "id": detail.id,
                "apparatus_name": detail.apparatus.apparatus_name,
                "fine_amount": damage_details.get(detail.id, {}).get("fine_amount", 0),
                "remarks": damage_details.get(detail.id, {}).get("remarks", ""),
            }
            for detail in details_qs if detail.apparatus
        ]
        
        grouped_list.append(group)
    
    departments = LabBatchAssignment.objects.filter(
    department__in=[mapped_department]
).values_list("department", flat=True).distinct().order_by("department")

    course_codes = LabExercise.objects.filter(department=mapped_department).values_list("course_code", flat=True).distinct().order_by("course_code")
    
    context = {
        "departments": departments,
        "course_codes": course_codes,
        "damaged_apparatus_requests": grouped_list,
        "page_name": page_name,
    }
    return render(request, "technician/payment_status.html", context)

import os
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader

def generate_payment_pdf(request, request_id):
    apparatus_request = get_object_or_404(ApparatusRequest, id=request_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="payment_receipt.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Load Logo
    logo_path = os.path.join(settings.STATICFILES_DIRS[0], "images", "image.png")
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        p.drawImage(logo, 50, height - 100, width=80, height=50, mask='auto')

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 120, "Fine Payment Confirmation – Lab Equipment")

    # Line separator
    p.setStrokeColor(colors.black)
    p.line(50, height - 130, width - 50, height - 130)

    # Define text positions
    y_position = height - 180
    row_height = 25

    # Helper function to draw rows (one field per line)
    def draw_row(label, value, y_offset):
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_offset, label)
        p.setFont("Helvetica", 12)
        p.drawString(200, y_offset, str(value))  # Adjust the x-position for alignment
        return y_offset - row_height

    # Display Experiment Name
    y_position = draw_row("Experiment Name:", apparatus_request.apparatus.experiment_name, y_position)

    # Display Practical Course
    y_position = draw_row("Practical Course:", apparatus_request.apparatus.practical_course, y_position)

    # Display Payment Verification
    payment_verified = "Yes" if apparatus_request.verified else "No"
    y_position = draw_row("Payment Verified:", payment_verified, y_position)

    # Display Date
    y_position = draw_row("Date:", apparatus_request.verified_date, y_position)

    # Display Course Code
    y_position = draw_row("Course Code:", apparatus_request.course_code, y_position)

    # Display Experiment No
    y_position = draw_row("Experiment No:", apparatus_request.lab_batch.ex_no, y_position)

    # Display Department
    y_position = draw_row("Department:", apparatus_request.apparatus.department, y_position)

    # Display Lab Batch No
    y_position = draw_row("Lab Batch No:", apparatus_request.lab_batch.lab_batch_no, y_position)

    # Display Status
    y_position = draw_row("Status:", apparatus_request.status, y_position)

    # Apparatus Details Table
    table_data = [["Apparatus Name", "Fine Amount (INR)", "Remarks"]]
    total_fine = 0

    for damage in apparatus_request.apparatusrequestdamage_set.all():
        fine_amount = damage.fine_amount
        total_fine += fine_amount
        table_data.append([
            damage.apparatus.apparatus_name,
            f"₹ {fine_amount}",
            damage.remarks
        ])

    # Add Total Fine Amount row
    table_data.append(["", "Total: ₹ {}".format(total_fine), ""])

    # Create and Style Table
    table = Table(table_data, colWidths=[200, 100, 200])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (1, len(table_data) - 1), (1, len(table_data) - 1), colors.lightgrey),
        ("FONTNAME", (1, len(table_data) - 1), (1, len(table_data) - 1), "Helvetica-Bold")
    ]))

    # Draw Table
    y_position -= 50
    table.wrapOn(p, width, height)
    table.drawOn(p, 50, y_position - len(table_data) * 20)

    # Fetch Lab Batch Students
    lab_batch_assignments = LabBatchAssignment.objects.filter(
        course_code=apparatus_request.course_code,
        lab_batch_no=apparatus_request.lab_batch.lab_batch_no,
        ex_no=apparatus_request.lab_batch.ex_no,
    )

    students = Student_cgpa.objects.using("rit_cgpatrack").all()
    student_dict = {student.reg_no: student.student_name for student in students}

    lab_batch_students = []
    for assignment in lab_batch_assignments:
        student_id = assignment.student_id
        student_name = student_dict.get(student_id, "Unknown")
        lab_batch_students.append({
            "student_id": student_id,
            "student_name": student_name,
            "department": assignment.department,
            "section": assignment.section,
            "assessment": assignment.assessment,
        })

    # Lab Batch Students Table
    y_position -= len(table_data) * 20 + 50  # Adjust position after the previous table
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Lab Batch Students:")

    y_position -= 20
    student_table_data = [["Student ID", "Student Name", "Department", "Section", "Assessment"]]
    for student in lab_batch_students:
        student_table_data.append([
            student["student_id"],
            student["student_name"],
            student["department"],
            student["section"],
            student["assessment"],
        ])

    student_table = Table(student_table_data, colWidths=[100, 150, 100, 80, 100])
    student_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    student_table.wrapOn(p, width, height)
    student_table.drawOn(p, 50, y_position - len(student_table_data) * 20)

    # Finalize
    p.showPage()
    p.save()

    return response




def review_payment_receipt(request):
    return render(request, "technician/review_payment_receipt.html")



from django.contrib.auth import logout

from django.shortcuts import redirect

def technician_logout(request):
    request.session.flush()  # Clears the session
    return redirect("/technician_login")  # Redirects to login without 'next'

# ---------------------------HOD --------------------------



from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum
from .models import ApparatusRequest, LabBatchAssignment, Student_cgpa
from django.utils.timezone import timedelta
from django.db.models.functions import TruncMinute

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.utils.timezone import timedelta
from .models import ApparatusRequest, LabBatchAssignment







from django.db.models import Count
from django.db.models.functions import TruncMinute
from datetime import timedelta
from django.shortcuts import render
from .models import ApparatusRequest, ApparatusRequestDamage, LabBatchAssignment, Student_cgpa

from django.db.models import Count
from django.db.models.functions import TruncMinute
from datetime import timedelta
from django.shortcuts import render, redirect
from django.db.models import Q
from .models import ApparatusRequest, ApparatusRequestDamage, LabBatchAssignment, Student_cgpa, User

# Department Mapping: HOD Department -> Student Department
DEPARTMENT_MAPPING = {
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
    "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
    "INFORMATION TECHNOLOGY": "B.TECH IT",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
    "MECHANICAL ENGINEERING": "B.E ME",
}

def hod_dashboard(request):
    # Get the logged-in HOD user ID from the session
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/hod_login")

    # Retrieve user details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    
    # Get the HOD's department and map it to the student department format
    hod_department = user_data.Department.strip().upper()  # Ensure consistency
    student_department = DEPARTMENT_MAPPING.get(hod_department, hod_department)  # Fallback if not in mapping
    print(hod_department, student_department)

    # Get filter parameters from the request
    section_filter = request.GET.get("section", "")
    course_code_filter = request.GET.get("course_code", "")
    experiment_name_filter = request.GET.get("experiment_name", "")

    # 🔹 1. Get damaged apparatus requests pending HOD approval (filtered by department)
    
    qs = ApparatusRequest.objects.filter(
        status="Damaged",
        hod_approval=False,
        # student__department__iexact=student_department  # Filtering by mapped department
    ).select_related("student", "lab_batch", "apparatus")

    # Apply additional filters if provided
    if section_filter:
        qs = qs.filter(lab_batch__section__icontains=section_filter)
    if course_code_filter:
        qs = qs.filter(lab_batch__course_code__icontains=course_code_filter)
    if experiment_name_filter:
        qs = qs.filter(apparatus__experiment_name__icontains=experiment_name_filter)

    # 🔹 2. Group requests by student, lab batch, and apparatus
    grouped = (
        qs.annotate(request_minute=TruncMinute("request_date"))
        .values(
            "student__reg_no",
            "lab_batch__course_code",
            "apparatus__ex_no",
            "apparatus__department",
            "lab_batch__lab_batch_no",
            "status",
            "request_minute",
            "apparatus__experiment_name",
            "apparatus__practical_course",
        )
        .annotate(apparatus_count=Count("id"))
        .order_by("student__reg_no", "lab_batch__lab_batch_no", "request_minute")
    )

    grouped_list = list(grouped)

    # 🔹 3. Fetch all students from the rit_cgpatrack database
    students = Student_cgpa.objects.using("rit_cgpatrack").all()
    student_dict = {student.reg_no.strip().upper(): student.student_name for student in students}

    # 🔹 4. Add apparatus details (fine, remarks) and total fine amount to each group
    for group in grouped_list:
        student_reg = group["student__reg_no"].strip().upper()
        group["student_name"] = student_dict.get(student_reg, "Unknown")
        course = group["lab_batch__course_code"]
        exp_no = group["apparatus__ex_no"]
        dept = group["apparatus__department"]
        lab_batch = group["lab_batch__lab_batch_no"]
        req_min = group["request_minute"]

        apparatus_details = ApparatusRequestDamage.objects.filter(
            apparatus_request__student__reg_no=student_reg,
            apparatus_request__lab_batch__course_code=course,
            apparatus_request__apparatus__ex_no=exp_no,
            apparatus_request__apparatus__department=dept,
            apparatus_request__lab_batch__lab_batch_no=lab_batch,
            apparatus_request__request_date__gte=req_min,
            apparatus_request__request_date__lt=req_min + timedelta(minutes=1),
        ).select_related("apparatus_request__apparatus").values(
            "apparatus_request__apparatus__apparatus_name",
            "apparatus_request__apparatus__range_specification",
            "apparatus_request__apparatus__quantity_available",
            "fine_amount",
            "remarks",
        )

        group["apparatus_details"] = [
            {
                "apparatus_name": detail["apparatus_request__apparatus__apparatus_name"],
                "range_specification": detail["apparatus_request__apparatus__range_specification"],
                "quantity_available": detail["apparatus_request__apparatus__quantity_available"],
                "fine_amount": detail["fine_amount"] or 0,
                "remarks": detail["remarks"] or "",
            }
            for detail in apparatus_details
        ]

        group["total_fine_amount"] = sum(detail["fine_amount"] for detail in group["apparatus_details"])

        lab_batch_assignments = LabBatchAssignment.objects.filter(
            course_code=course,
            lab_batch_no=lab_batch,
            ex_no=exp_no,
        )

        group["lab_batch_students"] = [
            {
                "student_id": assignment.student_id,
                "student_name": student_dict.get(assignment.student_id.strip().upper(), "Unknown"),
                "department": assignment.department,
                "section": assignment.section,
                "assessment": assignment.assessment,
            }
            for assignment in lab_batch_assignments
        ]

    # 🔹 5. Get distinct filter values related to the logged-in HOD's department
    # Get distinct sections from LabExercise
    sections = LabBatchAssignment.objects.filter(department__iexact=student_department) \
    .order_by("section").values_list("section", flat=True).distinct()

# Get distinct course codes from LabExercise
    course_codes = LabExercise.objects.filter(department__iexact=student_department) \
    .order_by("course_code").values_list("course_code", flat=True).distinct()

# Get distinct experiment names from LabExercise
    experiment_names = LabExercise.objects.filter(department__iexact=student_department) \
    .order_by("Ex_no").values_list("Ex_no", flat=True).distinct()


    context = {
        "grouped_requests": grouped_list,
        "section_filter": section_filter,
        "course_code_filter": course_code_filter,
        "experiment_name_filter": experiment_name_filter,
        "sections": sections,
        "course_codes": course_codes,
        "experiment_names": experiment_names,
    }

    return render(request, "faculty/hod/hod_dashboard.html", context)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ApparatusRequest

@csrf_exempt
def approve_request(request):
    if request.method == "POST":
        request_id = request.POST.get("request_id")  # Example: "22BCS101_1_5"
        print(f"Received request_id: {request_id}")

        if not request_id:
            return JsonResponse({"success": False, "error": "Request ID is missing."})

        try:
            # 🔹 Split the request_id into meaningful parts
            student_reg_no, lab_batch_no, ex_no = request_id.split("_")

            # 🔹 Find all apparatus requests matching this group
            apparatus_requests = ApparatusRequest.objects.filter(
                student__reg_no=student_reg_no,
                lab_batch__lab_batch_no=lab_batch_no,
                apparatus__ex_no=ex_no,
                status="Damaged"
            )

            if apparatus_requests.exists():
                apparatus_requests.update(hod_approval=True)
                return JsonResponse({"success": True})
            else:
                return JsonResponse({"success": False, "error": "No matching requests found."})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})


def faculty_logout(request):
    request.session.flush()
    return redirect('faculty_login')




