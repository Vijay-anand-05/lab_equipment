from django.shortcuts import render, redirect, get_object_or_404
from .models import Student, User
from django.contrib import messages
import hashlib


DEPARTMENT_MAPPING = {
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
    "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
    "INFORMATION TECHNOLOGY": "B.TECH IT",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
    "MECHANICAL ENGINEERING": "B.E ME",
    "ELECTRONICS AND COMMUNICATION ENGINEERING" : "B.E ECE",
    "CIVIL ENGINEERING" : "B.E CIVIL",
    "COMPUTER SCIENCE AND BUSINESS SYSTEM" : "B.TECH CSBS",
    
}


def manual(request):
    return render(request, "student/manual.html")



from django.shortcuts import render

def custom_404_view(request, exception):
    return render(request, "404.html", status=404)

def custom_500_view(request):
    return render(request, "500.html", status=500)

def custom_403_view(request, exception):
    return render(request, "403.html", status=403)


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
        regno = request.POST.get("regno")  # Get student registration number
        password = request.POST.get("password")  # Get password

        print(f"Attempting to log in with regno: {regno} and password: {password}")

        try:
            # Fetch student details from `placement_portal` database
            student = Student.objects.using("placement_portal").get(student_regno=regno)
            
            # Check if the password matches (assuming hashing is used)
            if encrypt_password(password) == student.student_password:
                
                # Fetch additional student details from `rit_cgpatrack` database
                student_details = Student_cgpa.objects.using("rit_cgpatrack").get(reg_no=regno)

                print("Authentication successful!")

                # Store required details in session
                request.session["student_regno"] = regno  # Store regno (used as primary key)
                request.session["student_name"] = student_details.student_name  # Store name
                request.session["department"] = student_details.department  # Store department
                request.session["batch"] = student_details.batch  # Store batch
                request.session["cgpa"] = student_details.cgpa  # Store CGPA

                return redirect("student_dashboard")  # Redirect to student dashboard
            else:
                print("Authentication failed! Incorrect password.")
        
        except Student.DoesNotExist:
            print("Authentication failed! Student not found.")
        except Student_cgpa.DoesNotExist:
            print("Authentication failed! Student details not found.")

        return render(request, "student_login.html", {"error": "Invalid credentials!"})

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


# @student_required  # Ensure the user is logged in as a student.
# def student_dashboard(request):
#     page_name = "student_dashboard"
#     student_regno = request.session.get("student_regno")
#     department = request.session.get('department')
    
    
#     if not student_regno:
#         return render(
#             request,
#             "error.html",
#             {"message": "Student registration number not found in session."},
#         )

#     try:
#         # Retrieve student details
#         student_details = Student_cgpa.objects.using("rit_cgpatrack").get(
#             reg_no=student_regno
#         )
#     except Student_cgpa.DoesNotExist:
#         return render(request, "error.html", {"message": "Student details not found."})

#     # Retrieve student's lab batch assignments
#     student_assignments = LabBatchAssignment.objects.filter(
#         student=student_details,
#         technician_id__isnull=False
#     ).order_by("created_at")
    

#     # Organize lab batch members by Course Code and Lab Batch No
#     lab_batch_members = {}
#     for assignment in student_assignments:
#         course_code = assignment.course_code
#         lab_batch_no = assignment.lab_batch_no
        

#         if course_code not in lab_batch_members:
#             lab_batch_members[course_code] = {}

#         if lab_batch_no not in lab_batch_members[course_code]:
#             lab_batch_members[course_code][lab_batch_no] = []

#         # Add all students assigned to this batch
#         lab_batch_members[course_code][lab_batch_no] = list(
#             LabBatchAssignment.objects.filter(lab_batch_no=lab_batch_no, technician_id=assignment.technician_id)
#             .order_by("created_at")
#         )

#     context = {
#         "student_details": student_details,
#         "student_assignments": student_assignments,  # List of assignments
#         "lab_batch_members": lab_batch_members,  # Members grouped by course & batch
#         "page_name" : page_name
#     }
#     return render(request, "student/student_dashboard.html", context)

@student_required  # Ensure the user is logged in as a student.
def student_dashboard(request):
    page_name = "student_dashboard"
    student_regno = request.session.get("student_regno")
    department = request.session.get("department")
    print(department)

    if not student_regno:
        return render(
            request,
            "error.html",
            {"message": "Student registration number not found in session."},
        )

    try:
        # Retrieve student details including department (if applicable)
        student_details = Student_cgpa.objects.using("rit_cgpatrack").get(
            reg_no=student_regno
        )
    except Student_cgpa.DoesNotExist:
        return render(request, "error.html", {"message": "Student details not found."})

    # Retrieve student's lab batch assignments (filtered by technician_id presence)
    student_assignments = LabBatchAssignment.objects.filter(
        student=student_details, technician_id__isnull=False
    ).order_by("created_at")

    # Extract relevant technician_ids, course_codes, and lab_batch_nos
    technician_ids = student_assignments.values_list("technician_id", flat=True)
    course_codes = student_assignments.values_list("course_code", flat=True)
    lab_batch_nos = student_assignments.values_list("lab_batch_no", flat=True)
    # dept = student_assignments.filter(department = department)
    # print(dept)

    # Fetch all relevant batch members in a single query
    all_batch_members = LabBatchAssignment.objects.filter(
        technician_id__in=technician_ids,
        course_code__in=course_codes,
        lab_batch_no__in=lab_batch_nos,
        # department = department
    ).order_by("created_at")
    # print(all_batch_members)

    # Organizing batch members efficiently
    lab_batch_members = {}
    for member in all_batch_members:
        course_code = member.course_code
        batch_no = member.lab_batch_no

        if course_code not in lab_batch_members:
            lab_batch_members[course_code] = {}

        if batch_no not in lab_batch_members[course_code]:
            lab_batch_members[course_code][batch_no] = []

        lab_batch_members[course_code][batch_no].append(member)
    # print(lab_batch_members)

    context = {
        "student_details": student_details,
        "student_assignments": student_assignments,  # List of assignments
        "lab_batch_members": lab_batch_members,  # Members grouped by course & batch
        "page_name": page_name,
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
    
    # Get the student's assigned lab batches
    lab_batches = LabBatchAssignment.objects.filter(student_id=student_regno)

    if not lab_batches.exists():
        messages.error(request, "You are not assigned to any lab batch.")
        # return redirect("apparatus_request")

    # Map course codes to technician IDs for this student
    technician_course_map = {batch.course_code: batch.technician_id for batch in lab_batches}
    print(technician_course_map)

    # Get relevant course codes for the student's department
    dept_course_codes = list(
        Course.objects.filter(department=student_department).values_list("course_code", flat=True)
    )

    # Fetch distinct values for dropdown filters
    ex_no_list = LabExercise.objects.filter(course_code__in=dept_course_codes).values_list("Ex_no", flat=True).distinct()
    course_code_list = dept_course_codes
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
    experiment_date = None

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
            experiment_date = first_apparatus.experiment_date

    # Handle POST request (Submit Apparatus Request)
    if request.method == "POST" and apparatus_list.exists():
        apparatus_requests = []

        for apparatus in apparatus_list:
            # Get the technician ID who assigned the lab batch for this course
            technician_id = technician_course_map.get(apparatus.course_code, None)

            if technician_id:
                apparatus_requests.append(
                    ApparatusRequest(
                        student_id=student_regno,
                        lab_batch=LabBatchAssignment.objects.filter(student_id=student_regno, course_code=apparatus.course_code).first(),
                        apparatus=apparatus,
                        course_code=apparatus.course_code,
                        status="Pending",
                        technician_id=technician_id,  # ✅ Store Technician ID
                    )
                )

        if apparatus_requests:
            ApparatusRequest.objects.bulk_create(apparatus_requests)
            messages.success(request, "Apparatus request submitted successfully!")
        else:
            messages.error(request, "No valid apparatus requests found.")

        return redirect("apparatus_request")

    context = {
        "apparatus_list": apparatus_list,
        "experiment_name": experiment_name,
        "experiment_no": experiment_no,
        "ex_no_list": ex_no_list,
        "course_code_list": course_code_list,
        "practical_course_list": practical_course_list,
        "student_department": student_department,
        "experiment_date" : experiment_date
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

from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncMinute
from datetime import timedelta
from .models import ApparatusRequest, LabBatchAssignment, Student_cgpa, LabExercise

def requested_apparatus_view(request):
    student_regno = request.session.get("student_regno")

    # 🔹 1. Get the logged-in student's details
    try:
        student = Student_cgpa.objects.using("rit_cgpatrack").get(reg_no=student_regno)
    except Student_cgpa.DoesNotExist:
        return render(request, "student/requested_apparatus.html", {"error": "Student not found"})

    # 🔹 2. Find the lab batches the student is assigned to (with technician info)
    assigned_batches = LabBatchAssignment.objects.filter(student=student).values(
        "lab_batch_no", "course_code", "technician_id", "experiment_date"
    )
    print(assigned_batches)
    if not assigned_batches:
        return render(request, "student/requested_apparatus.html", {"error": "No lab batch assigned."})

    # 🔹 3. Create a map of course_code -> technician_id for the student
    technician_course_map = {batch["course_code"]: batch["technician_id"] for batch in assigned_batches}

    # 🔹 4. Find all students assigned to the same lab batches
    batch_numbers = [batch["lab_batch_no"] for batch in assigned_batches]
    batch_students = LabBatchAssignment.objects.filter(lab_batch_no__in=batch_numbers).values_list("student__reg_no", flat=True)

    # 🔹 5. Get all apparatus requests for students in the same lab batch **filtered by technician**
    qs = ApparatusRequest.objects.filter(student__reg_no__in=batch_students)

    # 🔹 6. Annotate requests for grouping
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
            "lab_batch__technician_id",  # ✅ Get assigned technician
        )
        .annotate(apparatus_count=Count("id"))
        .order_by("student__reg_no", "lab_batch__lab_batch_no", "request_minute")
    )

    grouped_list = []

    # 🔹 7. Filter the requests to only show the ones assigned by the correct technician
    for group in grouped:
        course = group["lab_batch__course_code"]
        assigned_technician = group["lab_batch__technician_id"]

        # ✅ Only include requests where the technician matches the student's assigned technician for that course
        if course in technician_course_map and technician_course_map[course] == assigned_technician:
            student_reg = group["student__reg_no"]
            exp_no = group["apparatus__ex_no"]
            dept = group["apparatus__department"]
            lab_batch = group["lab_batch__lab_batch_no"]
            req_min = group["request_minute"]
            
            
            request_id = ApparatusRequest.objects.filter(
        student__reg_no=group["student__reg_no"],
        lab_batch__course_code=group["lab_batch__course_code"],
        apparatus__ex_no=group["apparatus__ex_no"]
    ).values_list("id", flat=True).first()
            
            experiment_date = next(
            (batch["experiment_date"] for batch in assigned_batches if batch["course_code"] == course), None
        )

            paid = ApparatusRequest.objects.filter(
    student__reg_no=group["student__reg_no"],
    lab_batch__course_code=group["lab_batch__course_code"],
    apparatus__ex_no=group["apparatus__ex_no"],
    verified=True  # ✅ Check if all requests for this student & experiment are verified
).exists()

            payment_status = "Paid" if paid else "Not Paid"

            verified = (payment_status == "Paid")
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
                    lab_exercise_data = lab_exercise_qs.first()
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
            group["experiment_date"] = experiment_date
            group["payment_status"] = payment_status
            group["request_id"] = request_id
            grouped_list.append(group)

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





import qrcode
import base64
from io import BytesIO
from django.shortcuts import render, redirect
from .forms import PaymentProofForm
from .models import Payment, Student_cgpa
from django.contrib.auth.decorators import login_required

# @login_required


from io import BytesIO
import base64
import qrcode
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student_cgpa, ApparatusRequestDamage, Payment
from .forms import PaymentProofForm

def payment_upload(request):
    # Get the logged-in student based on session
    student_regno = request.session.get("student_regno")
    if not student_regno:
        messages.error(request, "Please log in to continue.")
        return redirect("student_login")  # Redirect if no student is logged in

    try:
        student = Student_cgpa.objects.using("rit_cgpatrack").get(reg_no=student_regno)
    except Student_cgpa.DoesNotExist:
        messages.error(request, "Invalid student registration number. Please try again.")
        return redirect("student_login")

    # **Fetch Fine Details** (Grouped by Course, Lab Batch, and Experiment)
    fine_records = ApparatusRequestDamage.objects.filter(
        apparatus_request__student__reg_no=student_regno,
        apparatus_request__status="Damaged"
    ).select_related("apparatus_request__lab_batch", "apparatus_request__apparatus")

    # **Grouping Fine Records**
    grouped_fines = {}
    damaged_apparatus_ids = []  # To store damaged apparatus IDs
    technician_ids = set()  # To track responsible technicians

    for record in fine_records:
        apparatus_request = record.apparatus_request
        lab_batch = apparatus_request.lab_batch
        apparatus = apparatus_request.apparatus

        key = (lab_batch.course_code, lab_batch.lab_batch_no, apparatus.experiment_name)

        if key not in grouped_fines:
            grouped_fines[key] = {
                "course_code": lab_batch.course_code,
                "lab_batch_no": lab_batch.lab_batch_no,
                "ex_no" : lab_batch.ex_no,
                "experiment_name": apparatus.experiment_name,
                "experiment_date": apparatus_request.request_date,
                "damaged_apparatus": [],
                "total_fine": 0
            }

        # Append damaged apparatus details
        grouped_fines[key]["damaged_apparatus"].append({
            "apparatus_id": record.id,  # Store damaged apparatus ID
            "apparatus_name": apparatus.apparatus_name,
            "fine_amount": record.fine_amount or 0,
            "remarks": record.remarks or ""
        })

        # Sum up total fine amount
        grouped_fines[key]["total_fine"] += record.fine_amount or 0

        # Collect damaged apparatus IDs
        damaged_apparatus_ids.append(record.id)

        # **Get Technician ID responsible for this apparatus request**
        if lab_batch.technician_id:
            technician_ids.add(lab_batch.technician_id)  # Collect unique technician IDs

    fine_records_list = list(grouped_fines.values())

    # **Ensure a Payment Record Exists and Link to Damaged Apparatus**
    payment, created = Payment.objects.get_or_create(student=student)

    # **Store Technician ID in Payment Model**
    if technician_ids:
        payment.technician_id = list(technician_ids)[0]  # Assign the first technician (adjust as needed)
        payment.save()

    # **Link Damaged Apparatus to Payment**
    if hasattr(payment, "damaged_apparatus"):  # Ensure field exists in Payment model
        payment.damaged_apparatus.set(damaged_apparatus_ids)  # ManyToManyField update

    # **Handle File Upload**
    if request.method == "POST":
        form = PaymentProofForm(request.POST, request.FILES, instance=payment)
        if form.is_valid():
            form.save()
            
            messages.success(request, "Payment proof uploaded successfully!")
            
            return redirect("payment_upload")  # Refresh page after successful upload
        else:
            messages.error(request, "Error uploading payment proof. Please check your file and try again.")

    else:
        form = PaymentProofForm(instance=payment)

    # **Generate QR Code for Mobile Upload**
    mobile_upload_url = request.build_absolute_uri("/student/qr_code/")
    qr = qrcode.make(mobile_upload_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(
        request,
        "student/payment_upload.html",
        {
            "form": form,
            "payment": payment,
            "qr_base64": qr_base64,  # Pass QR code to template
            "student": student,
            "fine_records": fine_records_list,  # Pass grouped fine details
        }
    )


def upload_qr(request):
    return render(request, "student/upload_qr.html")





@student_required
def student_logout(request):
    logout(request)  # Clears session
    request.session.flush()  # Ensure all session data is cleared
    messages.success(request, "You have been logged out successfully.")
    return redirect("student_login")


###################################faculty######################################


from django.shortcuts import render, redirect
# from your_app.models import User  # Ensure correct import
# from your_app.utils import encrypt_password  # Ensure correct import

def faculty_login(request):
    if request.method == "POST":
        username = request.POST.get("username")  # Maps to `staff_id`
        password = request.POST.get("password")
        selected_role = request.POST.get("role")  # Get role from form

        print(f"Attempting to log in with staff_id: {username}, role: {selected_role}")

        try:
            users = User.objects.using("rit_e_approval").filter(staff_id=username, role=selected_role)
            print(users)

            if not users.exists():
                print("Authentication failed! User not found or role mismatch.")
                return render(request, "faculty_login.html", {"error": "Invalid credentials!"})

            for user in users:
                if encrypt_password(password) == user.Password:
                    request.session["user_id"] = user.id  
                    request.session["role"] = user.role  

                    print(f"Authentication successful for {user.role}!")

                    if user.role == "HOD":
                        return redirect("hod_overview")
                    elif user.role == "Principal":
                        return redirect("principle_dashboard")
                    elif user.role == "Vice_Principal":
                        return redirect("vice_principle_dashboard")

            print("Authentication failed! Incorrect password.")

        except Exception as e:
            print(f"Database error: {e}")

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

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .models import User
# from .utils import encrypt_password  # Ensure this function is correctly implemented

def technician_login(request):
    print("Request Method:", request.method)  # Debugging

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        next_url = request.GET.get("next")

        print("Login Attempt:", username, password)  # Debugging

        try:
            # Fetch all users with the same staff_id
            users = User.objects.using("rit_e_approval").filter(staff_id=username)

            if not users.exists():
                messages.error(request, "User not found!")
                return render(request, "technician_login.html")

            # Filter users with matching passwords
            valid_users = [user for user in users if encrypt_password(password) == user.Password]
            print(valid_users)

            if not valid_users:
                messages.error(request, "Invalid credentials!")
                return render(request, "technician_login.html")

            # Automatically select the best role
            user = next((u for u in valid_users if u.role == "Staff"), valid_users[0])  # Prefer Staff

            # Store session data
            request.session["user_id"] = user.id
            request.session["user_role"] = user.role

            print(f"Logged in User: {user.staff_id}, Role: {user.role}")  # Debugging

            # Redirect to appropriate dashboard
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            return redirect("technician_dashboard") if user.role == "Staff" else redirect("staff_dashboard")

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            print("Error:", e)  # Debugging

    return render(request, "technician_login.html")


from django.shortcuts import redirect
from functools import wraps

def technician_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get("user_id")
        user_role = request.session.get("user_role")

        if not user_id or user_role not in ["Staff", "Technician"]:
            return redirect("technician_login")  # Redirect to login if not authenticated

        return view_func(request, *args, **kwargs)

    return wrapper


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

# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
# }

@technician_required
def technician_dashboard(request):
    user_id = request.session.get("user_id", None)
    if user_id is None:
        return redirect("/technician_login")

    # Fetch logged-in technician's data
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    
    
    # Check if user is a technician and get department
    if user_data.role != "Staff":
        return redirect("/technician_login")

    # Map department name using the dictionary
    technician_department = DEPARTMENT_MAPPING.get(user_data.Department, user_data.Department)

    # Get filters from request
    status_filter = request.GET.get("status", "Pending")
    batch = request.GET.get("batch")
    course_code = request.GET.get("course_code")
    lab_batch_no = request.GET.get("lab_batch_no")
    experiment_no = request.GET.get("experiment_no")

    # Fetch only requests related to the mapped technician's department
    qs = ApparatusRequest.objects.filter(status=status_filter, technician_id=user_id)

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
        
        experiment_date = LabBatchAssignment.objects.filter(
        lab_batch_no=lab_batch, course_code=course, technician_id=user_id).values_list("experiment_date", flat=True).first()

        details_qs = ApparatusRequest.objects.filter(
            student__reg_no=student_reg,
            lab_batch__course_code=course,
            apparatus__ex_no=exp_no,
            apparatus__department=dept,
            lab_batch__lab_batch_no=lab_batch,
            request_date__gte=req_min,
            request_date__lt=req_min + timedelta(minutes=1),
            technician_id=user_id
        )
        group["details"] = list(
            details_qs.values(
                "apparatus__apparatus_name",
                "apparatus__range_specification",
                "apparatus__quantity_available",
            )
        )
        group["experiment_date"] = experiment_date

    def sorted_list(qs_values):
        return sorted(list(set(qs_values)))

    page_name = "technician_dashboard"
    context = {
        "grouped_requests": grouped_list,
        "status_filter": status_filter,
        "status_choices": ["Pending", "Accepted", "Rejected", "Returned", "Damaged"],
        "department_list": sorted_list(
            ApparatusRequest.objects.filter(technician_id=user_id)
            .values_list("apparatus__department", flat=True)
        ),
        "batch_list": sorted_list(
            ApparatusRequest.objects.filter(technician_id=user_id).values_list("apparatus__batch", flat=True)
        ),
        "course_code_list": sorted_list(
            ApparatusRequest.objects.filter(technician_id=user_id).values_list("lab_batch__course_code", flat=True)
        ),
        "lab_batch_no_list": sorted_list(
            ApparatusRequest.objects.filter(technician_id=user_id).values_list("lab_batch__lab_batch_no", flat=True)
        ),
        "experiment_no_list": sorted_list(
            ApparatusRequest.objects.filter(technician_id=user_id).values_list("apparatus__ex_no", flat=True)
        ),
        "page_name": page_name,
        "user_data" : user_data
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

@technician_required
@csrf_exempt  # Use proper CSRF handling in production
def accept_or_reject_apparatus_request(request):
    user_id = request.session.get("user_id", None)
    
    if user_id is None:
        return redirect("/technician_login")

    try:
        # Fetch logged-in technician's data
        user_data = User.objects.using("rit_e_approval").get(id=user_id)
        
        # Check if user is a technician
        if user_data.role != "Staff":
            return redirect("/technician_login")

        technician_department = user_data.Department  # Assuming the technician has a department field
        mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)
        
        if request.method == "POST":
            data = json.loads(request.body)
            student_reg = data.get("student_reg")
            course_code = data.get("course")
            exp_no = data.get("exp_no")
            lab_batch = data.get("lab_batch")
            req_min_str = data.get("request_minute")
            new_status = data.get("status")

            req_min = parse_datetime(req_min_str)
            if not req_min:
                return JsonResponse({"success": False, "message": "Invalid request timestamp."}, status=400)

            if new_status not in ["Accepted", "Rejected"]:
                return JsonResponse({"success": False, "message": "Invalid status."}, status=400)

            # Validate Course Department
            try:
                course = Course.objects.get(course_code=course_code)
                course_dept = course.department
            except Course.DoesNotExist:
                return JsonResponse({"success": False, "message": "Course not found."}, status=404)

            # if course_dept != mapped_department:
            #     return JsonResponse({"success": False, "message": "Unauthorized access."}, status=403)

            # Update the request
            updated = ApparatusRequest.objects.filter(
                student__reg_no=student_reg,
                lab_batch__course_code=course_code,
                apparatus__ex_no=exp_no,
                
                lab_batch__lab_batch_no=lab_batch,
                request_date__gte=req_min,
                request_date__lt=req_min + timedelta(minutes=1),
                status="Pending",
                technician_id=user_id
            ).update(status=new_status)

            if updated:
                return JsonResponse({"success": True, "message": f"Request updated to {new_status}."})
            else:
                return JsonResponse({"success": False, "message": "No matching records found or already processed."}, status=400)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

@technician_required
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


@technician_required
def add_subject_type(request):
    user_id = request.session.get("user_id", None)
    print(user_id)
    if not user_id:
        return redirect("/technician_login")

    # Get logged-in technician details
    try:
        user_data = User.objects.using("rit_e_approval").get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please log in again.")
        return redirect("/technician_login")

    if user_data.role != "Staff":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/technician_login")
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
        request, "technician/add_subject_type.html", {"subject_types": subject_types, "user_data" : user_data}
    )


from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Category
from django.contrib.auth.decorators import login_required


  
def add_category(request):
    user_id = request.session.get("user_id", None)
    print(user_id)
    if not user_id:
        return redirect("/technician_login")

    # Get logged-in technician details
    try:
        user_data = User.objects.using("rit_e_approval").get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please log in again.")
        return redirect("/technician_login")

    if user_data.role != "Staff":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/technician_login")
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

    return render(request, "technician/add_category.html", {"user_data" : user_data})


from django.shortcuts import render, redirect
from django.contrib import messages
from equipment.models import *
from .forms import CourseForm


@technician_required
def add_course(request):
    user_id = request.session.get("user_id", None)
    print(user_id)
    if not user_id:
        return redirect("/technician_login")

    # Get logged-in technician details
    try:
        user_data = User.objects.using("rit_e_approval").get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please log in again.")
        return redirect("/technician_login")

    if user_data.role != "Staff":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/technician_login")

    # 🔹 Map technician department format
    technician_department = user_data.Department.strip().upper()
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)

    if request.method == "POST":
        form = CourseForm(request.POST)

        if form.is_valid():
            course = form.save(commit=False)

            # 🔹 Store technician's ID instead of using ForeignKey
            course.technician_id = user_data.id  # Store user ID
            # course.technician_name = user_data.username  # Store username instead

            # if course.department.strip().upper() != mapped_department:
            #     messages.error(request, "You can only add courses for your own department.")
            # else:
            course.save()
            messages.success(request, "Course added successfully!")
            return redirect("add_course")
        else:
            print("Form Errors:", form.errors)
            messages.error(request, f"Error adding course: {form.errors}")

    else:
        form = CourseForm()

    # 🔹 Show only the technician's department in the dropdown
    department_list = (
        Student_cgpa.objects.using("rit_cgpatrack").values_list("department", flat=True)
        .distinct()
    )

    sem = list(range(1, 9))  # Semesters from 1 to 8

    return render(
        request,
        "technician/add_course.html",
        {"form": form, "departments": department_list, "sem": sem, "user_data" : user_data},
    )



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LabExercise, Course
from .forms import LabExerciseForm


@technician_required
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
    if user_data.role != "Staff":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/technician_login")

    # 🔹 Retrieve ALL Departments (For Dropdown)
    departments = (
        Student_cgpa.objects.using("rit_cgpatrack")
        .values_list("department", flat=True)
        .distinct()
    )

    # 🔹 Retrieve ALL Courses (For Dropdown)
    courses = Course.objects.filter(technician_id = user_id)  # Store ID, name, and department

    if request.method == "POST":
        form = LabExerciseForm(request.POST)
        if form.is_valid():
            # 🔹 Save form but do NOT commit yet
            lab_exercise = form.save(commit=False)
            lab_exercise.technician_id = str(user_id)  # Save Technician ID
            try:
                lab_exercise.save()  # Save to database
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
    batch_list = Course.objects.values_list("batch", flat=True).distinct()
    regulation_list = Course.objects.values_list("regulations", flat=True).distinct()

    context = {
        "form": form,
        "courses": courses,  # Pass all courses
        "sem": sem,
        "batches": batch_list,
        "regulations": regulation_list,
        "departments": departments,  # Pass all departments
        "mapped_department": mapped_department,  # Pass mapped technician department
        "user_data" : user_data
    }

    return render(request, "technician/add_lab_exercise.html", context)





  
from django.shortcuts import render
from django.http import JsonResponse
import json
from .models import Apparatus, LabExercise, Student_cgpa, User

# # Department Mapping
# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
# }

@technician_required
def add_apparatus(request):
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/technician_login")

    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)

    if user_data.role != "Staff":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/technician_login")

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("✅ Received Data:", data) 

            ex_no = str(data.get("ex_no", "")).strip()
            course_code = str(data.get("course_code", "")).strip()
            practical_course = str(data.get("practical_course", "")).strip()
            regulation = str(data.get("regulation", "")).strip()
            batch = str(data.get("batch", "")).strip()
            department = str(data.get("department", "")).strip()
            semester = data.get("semester")
            experiment_name = str(data.get("experiment_name", "")).strip()
            apparatus_entries = data.get("apparatus_entries", [])

            if not all([ex_no, course_code, practical_course, regulation, batch, department, semester, experiment_name]):
                return JsonResponse({"error": "Missing required fields"}, status=400)

            try:
                lab_exercise = LabExercise.objects.get(Ex_no=ex_no, Ex_title=experiment_name)
                experiment_date = lab_exercise.experiment_date  # ✅ Fetch experiment_date
            except LabExercise.DoesNotExist:
                return JsonResponse({"error": "Invalid experiment number or experiment name"}, status=400)

            print("✅ Found LabExercise:", lab_exercise, "with Experiment Date:", experiment_date)

            saved_apparatus = []
            for entry in apparatus_entries:
                apparatus_name = str(entry.get("apparatus_name", "")).strip()
                range_specification = str(entry.get("range_specification", "")).strip()
                quantity_available = str(entry.get("quantity_available", "")).strip()

                if apparatus_name and quantity_available:
                    apparatus = Apparatus.objects.create(
                        ex_no=ex_no,
                        course_code=course_code,
                        practical_course=practical_course,
                        experiment_name=experiment_name,
                        regulation=regulation,
                        batch=batch,
                        semester=semester,
                        apparatus_name=apparatus_name,
                        range_specification=range_specification,
                        quantity_available=quantity_available,
                        department=department,
                        technician_id=user_id,
                        experiment_date=experiment_date  # ✅ Save experiment_date
                    )
                    saved_apparatus.append(apparatus.apparatus_name)

            print(f"✅ Apparatus saved successfully: {saved_apparatus}")
            return JsonResponse({"message": "Apparatus saved successfully!"}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            print(f"❌ Error: {e}")
            return JsonResponse({"error": str(e)}, status=400)

    sem_list = list(range(1, 9))
    departments = Student_cgpa.objects.using('rit_cgpatrack').values_list('department', flat=True).distinct()

    dropdown_data = {
        "batches": list(LabExercise.objects.filter(technician_id=user_id).values_list("batch", flat=True).distinct()),
        "regulations": list(LabExercise.objects.filter(technician_id=user_id).values_list("regulations", flat=True).distinct()),
        "course_code": list(LabExercise.objects.filter(technician_id=user_id).values_list("course_code", flat=True).distinct()),
        "practical_course": list(LabExercise.objects.filter(technician_id=user_id).values_list("practical_course", flat=True).distinct()),
        "ex_no": list(LabExercise.objects.filter(technician_id=user_id).values_list("Ex_no", flat=True).distinct()),
        "experiment_name": list(LabExercise.objects.filter(technician_id=user_id).values_list("Ex_title", flat=True).distinct()),
        "sem": sem_list,
        "department_list": departments,
        "user_data": user_data
    }
    return render(request, "technician/add_apparatus.html", dropdown_data)



import itertools
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Student_cgpa, Course, LabExercise, LabBatchAssignment, User

# Department Mapping
# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
# }



import itertools
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LabExercise, LabBatchAssignment

def get_next_experiment(course_code, lab_batch_no, user_id):
    """Cycle through experiments for the given course & batch."""
    exp_numbers = list(
        LabExercise.objects.filter(course_code=course_code, technician_id=user_id)
        .values_list("Ex_no", flat=True)
        .distinct()
    )

    last_assignment = LabBatchAssignment.objects.filter(
        course_code=course_code, lab_batch_no=lab_batch_no
    ).order_by("-created_at").first()

    if last_assignment and last_assignment.ex_no in exp_numbers:
        try:
            last_index = exp_numbers.index(last_assignment.ex_no)
            new_order = exp_numbers[last_index + 1:] + exp_numbers[:last_index + 1]
            exp_cycle = itertools.cycle(new_order)
        except ValueError:
            exp_cycle = itertools.cycle(exp_numbers)
    else:
        exp_cycle = itertools.cycle(exp_numbers)

    return next(exp_cycle) if exp_numbers else None  # Return next experiment or None












@technician_required
def add_batch(request):
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/technician_login")

    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    technician_department = user_data.Department.strip().upper()
    mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)

    if user_data.role != "Staff":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/technician_login")

    if request.method == "POST":
        lab_batch_no = request.POST.get("lab_batch_no", "").strip()
        course_code = request.POST.get("course_code", "").strip()
        experiment_no_input = request.POST.get("experiment_no", "").strip()
        assessment = request.POST.get("assessment", "").strip()
        selected_students = request.POST.getlist("selected_students")

        if not LabExercise.objects.filter(course_code=course_code).exists():
            messages.error(request, "Unauthorized course selection.")
            return redirect("add_batch")

        existing_batch = LabBatchAssignment.objects.filter(
            lab_batch_no=lab_batch_no, course_code=course_code
        ).first()

        if existing_batch:
            exp_no = existing_batch.ex_no
        else:
            if experiment_no_input:
                exp_no = experiment_no_input
            else:
                exp_no = get_next_experiment(course_code, lab_batch_no, user_id)  # ✅ Use cycling function

        # ✅ Fetch experiment date from LabExercise
        try:
            lab_exercise = LabExercise.objects.filter(course_code=course_code, Ex_no=exp_no).first()
            experiment_date = lab_exercise.experiment_date if lab_exercise else None  # ✅ Safe fetch

        except LabExercise.DoesNotExist:
            messages.error(request, "Invalid experiment number or experiment name.")
            return redirect("add_batch")

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

                    # ✅ Save batch assignment with experiment date
                    LabBatchAssignment.objects.create(
                        student=student,
                        lab_batch_no=lab_batch_no,
                        course_code=course_code,
                        ex_no=exp_no,
                        assessment=assessment,
                        department=student.department,
                        section=student.section,
                        technician_id=user_id,
                        experiment_date=experiment_date  # ✅ Save experiment date
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
        students = Student_cgpa.objects.using("rit_cgpatrack").filter(department=department_filter)

        if batch_filter:
            students = students.filter(batch=batch_filter)
        if section_filter:
            students = students.filter(section=section_filter)
        students = students.order_by("-gender")

        assigned_regnos = list(
            LabBatchAssignment.objects.filter(
                course_code=course_code,
                lab_batch_no=batch_filter,
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
    course_codes = list(
        LabExercise.objects.filter(technician_id=user_id)
        .values_list("course_code", flat=True)
        .distinct()
    )
    ex_nos = list(
        LabExercise.objects.filter(technician_id=user_id)
        .values_list("Ex_no", flat=True)
        .distinct()
    )

    lab_assignments = LabBatchAssignment.objects.filter(technician_id=user_id).order_by("-created_at")
    departments = LabExercise.objects.filter(technician_id=user_id).values_list('department', flat=True)

    context = {
        "students": students,
        "filtered": filtered,
        "batch_filter": batch_filter,
        "department_filter": department_filter,
        "section_filter": section_filter,
        "batches": batches,
        "departments": departments,
        "section_options": section_options,
        "course_code": course_codes,
        "ex_no": ex_nos,
        "lab_assignments": lab_assignments,
        "user_data": user_data
    }
    return render(request, "technician/add_batch.html", context)


from django.shortcuts import render, redirect
from .models import LabBatchAssignment, LabExercise, User

# Department Mapping
# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
# }


@technician_required
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
    if user_data.role != "Staff":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/technician_login")

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
        assignments = LabBatchAssignment.objects.filter(technician_id=user_id).order_by("-created_at")

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
        LabExercise.objects.filter(technician_id=user_id)
        .values_list("course_code", flat=True)
        .distinct()
        .order_by("course_code")
    )
    departments = (
        LabExercise.objects.filter(technician_id=user_id)
        .values_list("department", flat=True)
        .distinct()
        .order_by("course_code")
    )
    sections = (
        LabBatchAssignment.objects.filter(technician_id=user_id)
        .values_list("section", flat=True)
        .distinct()
        .order_by("section")
    )
    lab_batches = (
        LabBatchAssignment.objects.filter(technician_id=user_id)
        .values_list("lab_batch_no", flat=True)
        .distinct()
        .order_by("lab_batch_no")
    )
    assessments = (
        LabBatchAssignment.objects.filter(technician_id=user_id)
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
        "departments" : departments,
        "user_data" : user_data
    }
    return render(request, "technician/view_batches.html", context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import LabBatchAssignment, LabExercise, User

# Department Mapping
# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
# }

@technician_required
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
    # if assignment.department != mapped_department:
    #     messages.error(request, "You are not authorized to edit this lab batch assignment.")
    #     return redirect("view_batches")

    # Retrieve available course codes and experiment numbers (only for technician's department)
    course_codes = (
        LabExercise.objects.filter(technician_id=user_id)
        .values_list("course_code", flat=True)
        .distinct()
        .order_by("course_code")
    )
    ex_nos = (
        LabExercise.objects.filter(technician_id=user_id)
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
# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
# }

from .models import User, ApparatusRequest, Apparatus  # Ensure correct imports

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.timezone import now
from django.db.models import Count
from .models import ApparatusRequest, ApparatusRequestDamage, LabBatchAssignment, LabExercise
# from .decorators import technician_required
from django.http import HttpResponse

from django.utils.timezone import now

# @technician_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from .models import (
    ApparatusRequest, ApparatusRequestDamage, Student_cgpa,
    LabBatchAssignment, LabExercise, User
)

# Department Mapping
# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
# }

@technician_required
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

        first_request = ApparatusRequest.objects.filter(id=return_request_id, technician_id=user_id).first()

        if not first_request:
            messages.error(request, "❌ Request not found.")
            return redirect("damaged_apparatus")

        # 🔹 Ensure technician can only manage their department’s apparatus
        # if first_request.apparatus.department != mapped_department:
        #     messages.error(request, "❌ You are not authorized to update this apparatus.")
        #     return redirect("damaged_apparatus")

        reg_no = first_request.student_id
        student = Student_cgpa.objects.using("rit_cgpatrack").filter(reg_no=reg_no).first()
        student_reg_no = student.reg_no if student else first_request.student.reg_no

        # Get all related requests
        related_requests = ApparatusRequest.objects.filter(
            student__reg_no=student_reg_no,
            lab_batch__course_code=first_request.lab_batch.course_code,
            apparatus__ex_no=first_request.apparatus.ex_no,
            # apparatus__department=mapped_department,  # 🔹 Restrict by technician department
            lab_batch__lab_batch_no=first_request.lab_batch.lab_batch_no,
            request_date=first_request.request_date,
            technician_id=user_id
        )

        # Retrieve selected apparatus IDs
        if action in ["verify", "not_verify"]:
            if related_requests.exists():
                if action == "verify":
                    updated = related_requests.update(verified=True, verified_date=timezone.now())
                    messages.success(request, f"✅ {updated} apparatus requests have been verified.")
                elif action == "not_verify":
                    updated = related_requests.update(verified=False, verified_date=None)
                    messages.warning(request, f"⚠️ Verification removed for {updated} apparatus requests.")
            else:
                messages.error(request, "❌ No apparatus found to verify.")
            return redirect("damaged_apparatus")
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
                apparatus_request_obj = ApparatusRequest.objects.get(id=apparatus_id,technician_id=user_id)
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
                defaults={"fine_amount": fine_amount, "remarks": technician_remarks},
                technician_id=user_id
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
        # Handle verification
        # Check if action is for verification (skip selection requirement)
        



        # return redirect("damaged_apparatus")

    # 🔹 Filtered queryset - Only damaged apparatus from the technician's department
    qs = ApparatusRequest.objects.filter(status="Damaged", technician_id=user_id)

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
            lab_batch__lab_batch_no=group["lab_batch__lab_batch_no"], request_date=group["request_date"],
            technician_id=user_id
        )
        first_request = details_qs.first()
        group["request_id"] = first_request.id if first_request else None
        group["verified"] = all(req.verified for req in details_qs)
        
        experiment_date = LabBatchAssignment.objects.filter(
        lab_batch_no=group["lab_batch__lab_batch_no"],
        course_code=group["lab_batch__course_code"], technician_id=user_id
    ).values_list("experiment_date", flat=True).first()

        # Get fine amount and remarks from ApparatusRequestDamage
        damage_details = {
            entry.apparatus_request_id: {"fine_amount": entry.fine_amount or 0, "remarks": entry.remarks or ""}
            for entry in ApparatusRequestDamage.objects.filter(apparatus_request__in=details_qs, technician_id=user_id)
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
        group["experiment_date"] = experiment_date
        grouped_list.append(group)

    departments = LabBatchAssignment.objects.filter(technician_id=user_id).values_list("department", flat=True).distinct().order_by("department")
    course_codes = LabExercise.objects.filter(technician_id=user_id).values_list("course_code", flat=True).distinct().order_by("course_code")

    context = {
        "damaged_apparatus_requests": grouped_list,
        "departments": departments,
        "course_codes": course_codes,
        "page_name": page_name,
        "user_data" : user_data
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
# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
# }

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
# from xhtml2pdf import pisa
from django.db.models import Count, Sum
from .models import LabBatchAssignment, LabExercise, ApparatusRequest, ApparatusRequestDamage


@technician_required
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
    qs = ApparatusRequest.objects.filter(status="Damaged", technician_id=user_id)
    
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
            "lab_batch__lab_batch_no", "status", "verified", "lab_batch__experiment_date"
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
            technician_id=user_id
        )
        
        first_request = details_qs.first()
        group["request_id"] = first_request.id if first_request else None
        group["remarks"] = first_request.technician_remarks if first_request else ""
        group["experiment_date"] = first_request.lab_batch.experiment_date if first_request else None  # 🔹 Added
        
        damage_details = {
            entry.apparatus_request_id: {"fine_amount": entry.fine_amount or 0, "remarks": entry.remarks or ""}
            for entry in ApparatusRequestDamage.objects.filter(apparatus_request__in=details_qs, technician_id=user_id)
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
    technician_id=user_id
).values_list("department", flat=True).distinct().order_by("department")

    course_codes = LabExercise.objects.filter(technician_id=user_id).values_list("course_code", flat=True).distinct().order_by("course_code")
    
    context = {
        "departments": departments,
        "course_codes": course_codes,
        "damaged_apparatus_requests": grouped_list,
        "page_name": page_name,
        "user_data" : user_data
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

import os
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
import os
from PIL import Image
from django.conf import settings

# @technician_required
def generate_payment_pdf(request, request_id):
    apparatus_request = get_object_or_404(ApparatusRequest, id=request_id)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="payment_receipt.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Load Logo
    logo_path = os.path.join(settings.STATICFILES_DIRS[0], "images", "logo.jpg")
    logo_path_1 = os.path.join(settings.STATICFILES_DIRS[0], "images", "bg_logo.png")
    if os.path.exists(logo_path) and os.path.exists(logo_path_1):
        logo = ImageReader(logo_path_1)

        # 🔹 Draw the first image (Top-Left) without transparency
        p.drawImage(logo, 50, height - 100, width=450, height=80, mask="auto")

        # 🔹 Load the logo again for the second (centered) image with transparency
        img = Image.open(logo_path).convert("RGBA")  # Ensure RGBA format
        alpha = img.split()[3]  # Extract alpha channel
        alpha = alpha.point(lambda p: p * 0.4)  # Reduce opacity to 30%
        img.putalpha(alpha)

        # 🔹 Convert image to in-memory bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)  # Reset pointer

        # 🔹 Use the in-memory image for the second draw
        transparent_logo = ImageReader(img_bytes)
        logo_width, logo_height = 150, 150  # Set fixed dimensions

        # **Calculate center position**
        logo_x = (width - logo_width) / 2
        logo_y = (height - logo_height) / 2

        # 🔹 Draw the semi-transparent second image (Centered)
        p.drawImage(transparent_logo, logo_x, logo_y, width=logo_width, height=logo_height, mask="auto")

        

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 120, "Fine Payment Confirmation – Lab Equipment")

    # Line separator
    p.setStrokeColor(colors.black)
    p.line(50, height - 130, width - 50, height - 130)

    # Define text positions
    y_position = height - 180
    row_height = 25

    def draw_row(label, value, y_offset):
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_offset, label)
        p.setFont("Helvetica", 12)
        p.drawString(200, y_offset, str(value))  # Adjust for alignment
        return y_offset - row_height

    # Display essential details
    y_position = draw_row("Experiment Name :", apparatus_request.apparatus.experiment_name, y_position)
    y_position = draw_row("Experiment Date   :", apparatus_request.apparatus.experiment_date, y_position)
    y_position = draw_row("Practical Course   :", apparatus_request.apparatus.practical_course, y_position)
    y_position = draw_row("Payment Verified  :", "Paid" if apparatus_request.verified else "Not Paid", y_position)
    y_position = draw_row("Date                      :", apparatus_request.verified_date if apparatus_request.verified_date else "NIL", y_position)
    y_position = draw_row("Course Code         :", apparatus_request.course_code, y_position)
    y_position = draw_row("Experiment No      :", apparatus_request.lab_batch.ex_no, y_position)
    y_position = draw_row("Department           :", apparatus_request.apparatus.department, y_position)
    y_position = draw_row("Lab Batch No        :", apparatus_request.lab_batch.lab_batch_no, y_position)
    y_position = draw_row("Status                    :", apparatus_request.status, y_position)

    # Fetch Fine Details
    student = get_object_or_404(Student_cgpa.objects.using("rit_cgpatrack"), reg_no=apparatus_request.student_id)

    fine_records = ApparatusRequestDamage.objects.filter(
        apparatus_request__student__reg_no=student.reg_no,
        apparatus_request__status="Damaged"
    ).select_related("apparatus_request__lab_batch", "apparatus_request__apparatus")

    # Group Fine Records
    table_data = [["Apparatus Name", "Fine Amount (INR)", "Remarks"]]
    total_fine = 0

    for record in fine_records:
        apparatus = record.apparatus_request.apparatus
        table_data.append([
            apparatus.apparatus_name,
            f" {record.fine_amount or 0}",
            record.remarks or "No remarks",
        ])
        total_fine += record.fine_amount or 0

    # Append total fine amount
    table_data.append(["", f"Total:  {total_fine}", ""])

    # Create and Style Table
    table = Table(table_data, colWidths=[150, 150, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (1, len(table_data) - 1), (1, len(table_data) - 1), colors.lightgrey),
        ("FONTNAME", (1, len(table_data) - 1), (1, len(table_data) - 1), "Helvetica-Bold"),
    ]))

    # Draw Fine Details Table
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
        lab_batch_students.append([
            student_id,
            student_name,
            assignment.department,
            assignment.section,
            assignment.assessment,
        ])

    # Lab Batch Students Table
    y_position -= len(table_data) * 20 + 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Lab Batch Students:")

    y_position -= 20
    student_table_data = [["Student ID", "Student Name", "Department", "Section", "Assessment"]] + lab_batch_students

    student_table = Table(student_table_data, colWidths=[100, 150, 100, 80, 100])
    student_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Draw Student Table
    student_table.wrapOn(p, width, height)
    student_table.drawOn(p, 50, y_position - len(student_table_data) * 20)

    # Add new page for payment proof
    p.showPage()

    # Fetch Payment Proof
    payment = Payment.objects.filter(student=student).first()

   

    if payment and payment.payment_proof:
        proof_path = os.path.join(settings.MEDIA_ROOT, str(payment.payment_proof))
        if os.path.exists(proof_path):
            proof = ImageReader(proof_path)

            # Get the actual dimensions of the image
            with Image.open(proof_path) as img:
                img_width, img_height = img.size

            # Set the desired width while maintaining aspect ratio
            max_width = 300  # Maximum allowed width
            max_height = 300  # Maximum allowed height
            
            # Maintain aspect ratio
            aspect_ratio = img_width / img_height
            if img_width > max_width or img_height > max_height:
                if img_width > img_height:
                    image_width = max_width
                    image_height = max_width / aspect_ratio
                else:
                    image_height = max_height
                    image_width = max_height * aspect_ratio
            else:
                image_width = img_width
                image_height = img_height

            # Calculate X and Y positions to center the image
            x_position = (width - image_width) / 2  
            y_position = (height - image_height) / 2  

            # Draw the centered image
            p.drawImage(proof, x_position, y_position, width=image_width, height=image_height)



    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, height - 50, "Payment Proof")

    # Finalize
    p.showPage()
    p.save()

    return response







# def review_payment_receipt(request):
#     # return render(request, "technician/review_payment_receipt.html")
#     # Get filter values from request
#     department = request.GET.get("department")
#     course_code = request.GET.get("course_code")
#     payment_status = request.GET.get("payment_status")  # Paid or Not Paid

#     # Base queryset for damaged apparatus requests
#     qs = ApparatusRequest.objects.filter(status="Damaged")

#     if department:
#         qs = qs.filter(apparatus__department=department)
#     if course_code:
#         qs = qs.filter(lab_batch__course_code=course_code)
#     if payment_status:
#         qs = qs.filter(verified=(payment_status == "paid"))  # Using verified field

#     grouped_list = []
#     grouped = (
#         qs.values(
#             "student__reg_no", "lab_batch__course_code", "apparatus__ex_no", "apparatus__department",
#             "lab_batch__lab_batch_no", "status", "verified"
#         )
#         .annotate(total_fine=Sum("apparatusrequestdamage__fine_amount"))  # Summing fine amounts
#         .order_by("student__reg_no", "lab_batch__lab_batch_no")
#     )

#     for group in grouped:
#         details_qs = ApparatusRequest.objects.filter(
#             student__reg_no=group["student__reg_no"],
#             lab_batch__course_code=group["lab_batch__course_code"],
#             apparatus__ex_no=group["apparatus__ex_no"],
#             apparatus__department=group["apparatus__department"],
#             lab_batch__lab_batch_no=group["lab_batch__lab_batch_no"],
#         )
        
#         first_request = details_qs.first()
#         group["request_id"] = first_request.id if first_request else None
#         group["remarks"] = first_request.technician_remarks if first_request else ""
#         group["apparatus_list"] = [
#             {
#                 "id": detail.apparatus.id,
#                 "apparatus_name": detail.apparatus.apparatus_name,
#                 "fine_amount": detail.apparatusrequestdamage_set.first().fine_amount if detail.apparatusrequestdamage_set.exists() else 0,
#                 "remarks": detail.apparatusrequestdamage_set.first().remarks if detail.apparatusrequestdamage_set.exists() else "",
#             }
#             for detail in details_qs if detail.apparatus
#         ]
#         grouped_list.append(group)

#     departments = LabBatchAssignment.objects.values_list("department", flat=True).distinct().order_by("department")
#     course_codes = LabExercise.objects.values_list("course_code", flat=True).distinct().order_by("course_code")

#     context = {
#         "departments": departments,
#         "course_codes": course_codes,
#         "damaged_apparatus_requests": grouped_list,
#     }

#     return render(request, "technician/review_payment_receipt.html", context)

# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
# }

from django.shortcuts import render, redirect
from .models import Payment, ApparatusRequestDamage
# from core.models import Student_cgpa, User
from django.db.models import Prefetch

# Department Mapping (if used elsewhere, move to settings or a constants file)

from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import Payment, ApparatusRequestDamage, User

from django.shortcuts import render, redirect
from django.db.models import Sum, Q
from .models import Payment, ApparatusRequestDamage, User

from django.shortcuts import render, redirect
from django.db.models import Sum, Q
from .models import Payment, ApparatusRequestDamage, User, Student

from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import Payment, ApparatusRequestDamage, User, Student_cgpa

# Department Mapping


from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import Payment, ApparatusRequestDamage, User, Student_cgpa, LabExercise

# Department Mapping
# @technician_required
# def review_payment_receipt(request):
#     page_name = "review_payment_receipt"
#     user_id = request.session.get("user_id")
#     if not user_id:
#         return redirect("/technician_login")
    

#     # Fetch technician's department
#     try:
#         user_data = User.objects.using("rit_e_approval").get(id=user_id)
#         technician_department = user_data.Department.strip().upper()
#         mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)
#     except User.DoesNotExist:
#         return render(request, "technician/review_payment_receipt.html", {"payments": []})

#     # Get filter parameters
#     reg_no_filter = request.GET.get("reg_no", "").strip()
#     course_code_filter = request.GET.get("course_code", "").strip()

#     # Step 1: Get students who uploaded payment proof
#     student_payments = Payment.objects.filter(payment_proof__isnull=False)

#     # Step 2: Get student IDs from payments
#     student_ids = student_payments.values_list("student_id", flat=True)

#     # Step 3: Get total fine per student
#     student_payment_data = (
#         ApparatusRequestDamage.objects
#         .filter(apparatus_request__student_id__in=student_ids, technician_id=user_id)
#         .values("apparatus_request__student_id")  
#         .annotate(total_fine=Sum("fine_amount"))  
#         .order_by("apparatus_request__student__reg_no")
#     )

#     # Step 4: Fetch student details from Student_cgpa model & filter by department
#     filtered_students = []
#     for data in student_payment_data:
#         student = Student_cgpa.objects.using('rit_cgpatrack').filter(reg_no=data["apparatus_request__student_id"]).first()
#         payment = student_payments.filter(student_id=data["apparatus_request__student_id"]).first()

#         if not student:
#             continue  # Skip if student details are missing

#         # Ensure student belongs to the mapped department
#         # if student.department.strip().upper() != mapped_department:
#         #     continue

#         # Apply Reg No filter
#         if reg_no_filter and student.reg_no != reg_no_filter:
#             continue

#         # Apply Course Code filter (if course code exists in LabExercise)
#         if course_code_filter:
#             course_exists = LabExercise.objects.filter(
#                 technician_id=user_id,
#                 course_code__iexact=course_code_filter
#             ).exists()
#             if not course_exists:
#                 continue

#         filtered_students.append({
#             "reg_no": student.reg_no,
#             "section": student.section,
#             "department": student.department,
#             "total_fine": data["total_fine"],
#             "payment_proof": payment.payment_proof.url if payment and payment.payment_proof else None,

#         })

#     # Fetch course codes for dropdown
#     course_codes = LabExercise.objects.filter(technician_id=user_id).values_list("course_code", flat=True).distinct()

#     # Step 5: Pass to template
#     context = {
#         "student_payment_data": filtered_students,
#         "course_codes": course_codes,
#         "reg_no_filter": reg_no_filter,
#         "course_code_filter": course_code_filter
#     }
    
#     return render(request, "technician/review_payment_receipt.html", context)



@technician_required
def review_payment_receipt(request):
    page_name = "review_payment_receipt"
    user_id = request.session.get("user_id")
    
    if not user_id:
        return redirect("/technician_login")

    # Fetch technician's department
    try:
        user_data = User.objects.using("rit_e_approval").get(id=user_id)
        technician_department = user_data.Department.strip().upper()
        mapped_department = DEPARTMENT_MAPPING.get(technician_department, technician_department)
    except User.DoesNotExist:
        return render(request, "technician/review_payment_receipt.html", {"payments": []})

    # Get filter parameters
    reg_no_filter = request.GET.get("reg_no", "").strip()
    course_code_filter = request.GET.get("course_code", "").strip()

    # Step 1: Get students who uploaded payment proof
    student_payments = Payment.objects.filter(payment_proof__isnull=False)

    # Step 2: Get student IDs from payments (Only students with proof)
    student_ids = student_payments.values_list("student_id", flat=True)

    # Step 3: Get total fine per student (Only students with proof)
    student_payment_data = (
        ApparatusRequestDamage.objects
        .filter(apparatus_request__student_id__in=student_ids, technician_id=user_id)
        .values("apparatus_request__student_id")  
        .annotate(total_fine=Sum("fine_amount"))  
        .order_by("apparatus_request__student__reg_no")
    )

    # Step 4: Fetch student details (Only if they uploaded an image)
    filtered_students = []
    for data in student_payment_data:
        student = Student_cgpa.objects.using('rit_cgpatrack').filter(reg_no=data["apparatus_request__student_id"]).first()
        payment = student_payments.filter(student_id=data["apparatus_request__student_id"]).first()

        # Skip if no student record or payment proof is missing
        if not student or not payment or not payment.payment_proof:
            continue  

        # Apply Reg No filter
        if reg_no_filter and student.reg_no != reg_no_filter:
            continue

        # Apply Course Code filter (Only include students from the selected course)
        if course_code_filter:
            course_exists = LabExercise.objects.filter(
                technician_id=user_id,
                course_code__iexact=course_code_filter
            ).exists()
            if not course_exists:
                continue

        # Add student details to the list
        filtered_students.append({
            "reg_no": student.reg_no,
            "section": student.section,
            "department": student.department,
            "total_fine": data["total_fine"],
            "payment_proof": payment.payment_proof.url if payment.payment_proof else None,
        })

    # Step 5: Fetch course codes for dropdown
    course_codes = LabExercise.objects.filter(technician_id=user_id).values_list("course_code", flat=True).distinct()

    # Step 6: Pass to template
    context = {
        "student_payment_data": filtered_students,
        "course_codes": course_codes,
        "reg_no_filter": reg_no_filter,
        "course_code_filter": course_code_filter,
        "user_data" : user_data
    }

    return render(request, "technician/review_payment_receipt.html", context)


from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from .models import ApparatusRequest, ApparatusRequestDamage, User

from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from .models import ApparatusRequest, ApparatusRequestDamage, User, LabBatchAssignment

def hod_overview(request):
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/faculty_login")

    # Retrieve user details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)

    # Get HOD's department
    hod_department = user_data.Department.strip().upper()

    # Get all technicians under the HOD's department
    technicians_in_dept = list(User.objects.using('rit_e_approval').filter(
        role="Staff",
        Department__iexact=hod_department
    ).values_list("id", flat=True))

    # Base queryset without filters
    report_qs = ApparatusRequest.objects.filter(technician_id__in=technicians_in_dept)

    # Aggregate counts
    total_money = ApparatusRequestDamage.objects.filter(
        apparatus_request__technician_id__in=technicians_in_dept
    ).aggregate(total_fine=Sum("fine_amount"))["total_fine"] or 0

    total_reports = report_qs.values("student__reg_no", "lab_batch__lab_batch_no").distinct().count()
    pending_reports = report_qs.filter(status="Pending").values("student__reg_no", "lab_batch__lab_batch_no").distinct().count()
    total_damaged_reports = report_qs.filter(status="Damaged").values("student__reg_no", "lab_batch__lab_batch_no").distinct().count()
    hod_approved_reports = report_qs.filter(hod_approval=True).values("student__reg_no", "lab_batch__lab_batch_no").distinct().count()
    hod_not_approved_reports = report_qs.filter(hod_approval=False).values("student__reg_no", "lab_batch__lab_batch_no").distinct().count()
    payment_verified_reports = report_qs.filter(verified=True).values("student__reg_no", "lab_batch__lab_batch_no").distinct().count()

    # Get unique departments & sections for dropdown (optional if filters are removed)
    departments = ApparatusRequest.objects.filter(technician_id__in=technicians_in_dept).values_list("apparatus__department", flat=True).distinct()
    sections = list(set(
        section.strip().upper() for section in
        LabBatchAssignment.objects.filter(technician_id__in=technicians_in_dept)
        .values_list("section", flat=True)
        .distinct()
        if section  # Ensure no None values
    ))

    context = {
        "user_data": user_data,
        "total_money": total_money,
        "total_reports": total_reports,
        "pending_reports": pending_reports,
        "total_damaged_reports": total_damaged_reports,
        "hod_approved_reports": hod_approved_reports,
        "hod_not_approved_reports": hod_not_approved_reports,
        "payment_verified_reports": payment_verified_reports,
        "departments": departments,  # Optional if filters are removed
        "sections": sections,  # Optional if filters are removed
        "role": user_data.role,
    }
    return render(request, "faculty/hod_overview.html", context)

from django.contrib.auth import logout

from django.shortcuts import redirect


@technician_required
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
# DEPARTMENT_MAPPING = {
#     "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "B.TECH AD",
#     "COMPUTER SCIENCE AND ENGINEERING": "B.E CSE",
#     "INFORMATION TECHNOLOGY": "B.TECH IT",
#     "ELECTRICAL AND ELECTRONICS ENGINEERING": "B.E EEE",
#     "MECHANICAL ENGINEERING": "B.E ME",
#     "ELECTRONICS AND COMMUNICATION ENGINEERING" : "B.E ECE",
#     "CIVIL ENGINEERING" : "B.E CIVIL",
#     "COMPUTER SCIENCE AND BUSINESS SYSTEM" : "B.TECH CSBS",
    
# }

from datetime import timedelta
from django.db.models.functions import TruncMinute
from django.db.models import Count
from django.shortcuts import render, redirect

def hod_dashboard(request):
    # Get the logged-in HOD user ID from the session
    user_id = request.session.get("user_id", None)
    if not user_id:
        return redirect("/faculty_login")

    # Retrieve user details
    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    print(user_data.role)
    
    # Get HOD's department
    hod_department = user_data.Department.strip().upper()  
    student_department = DEPARTMENT_MAPPING.get(hod_department, hod_department)  # Ensure consistency
    print(hod_department, student_department)

    # Get filter parameters
    section_filter = request.GET.get("section", "")
    course_code_filter = request.GET.get("course_code", "")
    experiment_name_filter = request.GET.get("experiment_name", "")

    # 🔹 1. Get Technicians Assigned to the Department
    technicians_in_dept = list(User.objects.using('rit_e_approval').filter(
    role="Staff",
    Department__iexact=hod_department
).values_list("id", flat=True))  # Force evaluation
  # Fetch technician IDs
    print("Technicians in Dept:", technicians_in_dept)

    # 🔹 2. Get all apparatus requests (HOD’s department + Technician-handled requests)
    qs = ApparatusRequest.objects.filter(
        status="Damaged",
        hod_approval=False
    ).filter(
        technician_id__in=technicians_in_dept
    ).select_related("student", "lab_batch", "apparatus")

    # Fetch all Apparatus Request Damage entries assigned to these technicians
    technician_requests = ApparatusRequestDamage.objects.filter(
        apparatus_request__lab_batch__technician_id__in=technicians_in_dept
    ).values_list("apparatus_request_id", flat=True)

    # Merge both queries (Department + Technician)
    qs = qs.filter(id__in=technician_requests)

    # Apply additional filters
    if section_filter:
        qs = qs.filter(lab_batch__section__icontains=section_filter)
    if course_code_filter:
        qs = qs.filter(lab_batch__course_code__icontains=course_code_filter)
    if experiment_name_filter:
        qs = qs.filter(apparatus__experiment_name__icontains=experiment_name_filter)

    # 🔹 3. Group requests by student, lab batch, and apparatus
    grouped = (
        qs.annotate(request_minute=TruncMinute("request_date"))
        .values(
            "student__reg_no",
            "lab_batch__course_code",
            "apparatus__ex_no",
            "lab_batch__lab_batch_no",
            "lab_batch__department",
            "lab_batch__section",
            "status",
            "request_minute",
            "apparatus__experiment_name",
            "apparatus__practical_course",
            "lab_batch__experiment_date"
        )
        .annotate(apparatus_count=Count("id"))
        .order_by("student__reg_no", "lab_batch__lab_batch_no", "request_minute")
    )

    grouped_list = list(grouped)

    # 🔹 4. Fetch all students using the Technician ID from LabBatchAssignment
    students = Student_cgpa.objects.using("rit_cgpatrack").all()
    student_dict = {student.reg_no.strip().upper(): student.student_name for student in students}

    # 🔹 5. Add apparatus details (fine, remarks) and total fine amount to each group
    for group in grouped_list:
        student_reg = group["student__reg_no"].strip().upper()
        group["student_name"] = student_dict.get(student_reg, "Unknown")

        course = group["lab_batch__course_code"]
        exp_no = group["apparatus__ex_no"]
        lab_batch = group["lab_batch__lab_batch_no"]
        req_min = group["request_minute"]

        apparatus_details = ApparatusRequestDamage.objects.filter(
            apparatus_request__student__reg_no=student_reg,
            apparatus_request__lab_batch__course_code=course,
            apparatus_request__apparatus__ex_no=exp_no,
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

        # Fetch students assigned by the Technician ID
        lab_batch_assignments = LabBatchAssignment.objects.filter(
            course_code=course,
            lab_batch_no=lab_batch,
            ex_no=exp_no,
            technician_id__in=technicians_in_dept  # Filter by assigned technicians
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

    # 🔹 6. Get distinct filter values related to the logged-in HOD's department
    sections = LabBatchAssignment.objects.filter(technician_id__in=technicians_in_dept).order_by("section").values_list("section", flat=True).distinct()

    course_codes = LabExercise.objects.filter(
        technician_id__in=technicians_in_dept
    ).order_by("course_code").values_list("course_code", flat=True).distinct()

    experiment_names = LabExercise.objects.filter(
        technician_id__in=technicians_in_dept
    ).order_by("Ex_no").values_list("Ex_title", flat=True).distinct()

    context = {
        "grouped_requests": grouped_list,
        "section_filter": section_filter,
        "course_code_filter": course_code_filter,
        "experiment_name_filter": experiment_name_filter,
        "sections": sections,
        "course_codes": course_codes,
        "experiment_names": experiment_names,
        "role": user_data.role,
        "user_data" : user_data
    }

    return render(request, "faculty/hod_dashboard.html", context)



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


from django.shortcuts import render, redirect
from django.db.models import Sum
# from control_room.models import User
# from application.models import ApparatusRequest, ApparatusRequestDamage, LabBatchAssignment

from django.shortcuts import render, redirect
from django.db.models import Sum
# from control_room.models import User
# from application.models import ApparatusRequest, ApparatusRequestDamage, LabBatchAssignment

def hod_damaged_apparatus_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("/faculty_login")

    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    user_role = user_data.role.lower()
    
    # HOD's department
    hod_department = user_data.Department.strip().upper() if user_role == "hod" else None

    # Get all technicians assigned to the HOD’s department
    technicians_in_dept = list(User.objects.using('rit_e_approval').filter(
        role="Staff",
        Department__iexact=hod_department
    ).values_list("id", flat=True))

    print("Technicians in HOD's Dept:", technicians_in_dept)

    # Get filter values from request
    department_filter = request.GET.get("department", "").strip()
    payment_status = request.GET.get("payment_status", "").strip()

    # Fetch all apparatus requests handled by these technicians (even if from other departments)
    qs = ApparatusRequest.objects.filter(
        status="Damaged",
        technician_id__in=technicians_in_dept  # Filter by HOD’s department technicians
    )

    # Apply additional filters
    if department_filter:
        qs = qs.filter(apparatus__department=department_filter)
    if payment_status:
        qs = qs.filter(verified=(payment_status.lower() == "paid"))

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

    # Get distinct departments handled by the HOD’s technicians (even if from different departments)
    departments = (
        LabBatchAssignment.objects.filter(technician_id__in=technicians_in_dept)
        .values_list("department", flat=True)
        .distinct()
        .order_by("department")
    )

    context = {
        "departments": departments,  
        "damaged_apparatus_requests": grouped_list,
        "page_name": "hod_damaged_apparatus",
        "role": user_data.role,
        "user_data" : user_data
    }
    return render(request, "faculty/hod_damage_apparatus_view.html", context)


def faculty_logout(request):
    request.session.flush()
    return redirect('faculty_login')



from django.shortcuts import render, redirect
from django.db.models import Sum
from .models import User, ApparatusRequest, ApparatusRequestDamage, LabBatchAssignment
# from .constants import DEPARTMENT_MAPPING

def principle_dashboard(request):
    """
    Principal can view and filter damaged apparatus requests across all departments.
    """
    # Principal Authentication
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("/faculty_login")

    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    

    # Get filter values from request
    department = request.GET.get("department")
    payment_status = request.GET.get("payment_status")

    # Base queryset for all damaged apparatus requests
    qs = ApparatusRequest.objects.filter(status="Damaged")

    if department:
        qs = qs.filter(apparatus__department=department)
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

    # Fetch all unique departments for filtering
    departments = LabBatchAssignment.objects.values_list("department", flat=True).distinct().order_by("department")

    context = {
        "departments": departments,  # Now shows all departments
        "damaged_apparatus_requests": grouped_list,
        "page_name": "principle_dashboard",
        "role" : user_data.role,
        "user_data" : user_data
    }
    return render(request, "faculty/principle_dashboard.html", context)



def vice_principle_dashboard(request):
    """
    Principal can view and filter damaged apparatus requests across all departments.
    """
    # Principal Authentication
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("home")

    user_data = User.objects.using("rit_e_approval").get(id=user_id)
    

    # Get filter values from request
    department = request.GET.get("department")
    payment_status = request.GET.get("payment_status")

    # Base queryset for all damaged apparatus requests
    qs = ApparatusRequest.objects.filter(status="Damaged")

    if department:
        qs = qs.filter(apparatus__department=department)
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

    # Fetch all unique departments for filtering
    departments = LabBatchAssignment.objects.values_list("department", flat=True).distinct().order_by("department")

    context = {
        "departments": departments,  # Now shows all departments
        "damaged_apparatus_requests": grouped_list,
        "page_name": "principle_dashboard",
        "role" : user_data.role,
        "user_data" : user_data
    }
    return render(request, "faculty/vice_principle_dashboard.html", context)
