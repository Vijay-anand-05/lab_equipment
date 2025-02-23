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
            if student.student_password == encrypt_password(
                student_password
            ):  # Use hashing if passwords are encrypted
                request.session[
                    "student_regno"
                ] = student_regno  # Store student regno in session

                # Retrieve the department from Student_cgpa
                student_details = Student_cgpa.objects.using("rit_cgpatrack").get(
                    reg_no=student_regno
                )
                request.session[
                    "department"
                ] = student_details.department  # Store department in session
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
        return render(request, "error.html", {"message": "Student registration number not found in session."})

    try:
        # Retrieve the student's details from Student_cgpa.
        # (Assuming this model is stored in the "rit_cgpatrack" database.)
        student_details = Student_cgpa.objects.using("rit_cgpatrack").get(reg_no=student_regno)
    except Student_cgpa.DoesNotExist:
        return render(request, "error.html", {"message": "Student details not found."})

    # Retrieve the student's own lab batch assignment from the default database.
    student_assignment = LabBatchAssignment.objects.filter(student=student_details).first()

    lab_batch_members = None
    lab_batch_no = None
    if student_assignment:
        lab_batch_no = student_assignment.lab_batch_no
        # Retrieve all assignments in the same lab batch number.
        lab_batch_members = LabBatchAssignment.objects.filter(lab_batch_no=lab_batch_no).order_by("created_at")

    context = {
        "student_details": student_details,
        "student_assignment": student_assignment,
        "lab_batch_no": lab_batch_no,
        "lab_batch_members": lab_batch_members,
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
from .models import Apparatus, Course


def apparatus_request(request):
    # Retrieve the student's department from the session
    student_department = request.session.get("department")

    # Retrieve dropdown options based on the student's department
    dept_course_codes = Course.objects.filter(
        department=student_department
    ).values_list("course_code", flat=True)
    ex_no_list = (
        Apparatus.objects.filter(course_code__in=dept_course_codes)
        .values_list("ex_no", flat=True)
        .distinct()
    )
    course_code_list = dept_course_codes.distinct()  # Already filtered by department
    practical_course_list = (
        Apparatus.objects.filter(course_code__in=dept_course_codes)
        .values_list("practical_course", flat=True)
        .distinct()
    )

    # Get filter values from GET parameters
    ex_no = request.GET.get("ex_no", "").strip()
    course_code = request.GET.get("course_code", "").strip()
    practical_course = request.GET.get("practical_course", "").strip()

    # Initially, set apparatus queryset to none so that no data is displayed
    apparatus = Apparatus.objects.none()

    # Only if any filter parameter is provided, query the apparatus data
    if ex_no or course_code or practical_course:
        apparatus = Apparatus.objects.all()
        if ex_no:
            apparatus = apparatus.filter(ex_no=ex_no)
        if course_code:
            apparatus = apparatus.filter(course_code=course_code)
        if practical_course:
            apparatus = apparatus.filter(practical_course=practical_course)

        if apparatus.exists():
            experiment_name = apparatus.first().experiment_name
            experiment_no = apparatus.first().ex_no
        else:
            messages.warning(request, "No apparatus found matching the filters.")
            experiment_name = None
            experiment_no = None
    else:
        # No filter applied: do not display any data
        experiment_name = None
        experiment_no = None

    context = {
        "apparatus_list": apparatus,
        "experiment_name": experiment_name,
        "experiment_no": experiment_no,
        "ex_no_list": ex_no_list,
        "course_code_list": course_code_list,
        "practical_course_list": practical_course_list,
        'student_department' : student_department
    }
    return render(request, "student/apparatus_request.html", context)


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
                print(
                    encrypt_password(password), user.Password
                )  # Assuming passwords are hashed
                print("Authentication successful!")

                # Create a session or any custom login logic
                request.session["user_id"] = user.id  # Store user ID in session
                request.session["role"] = user.role  # Store the role if needed

                return redirect("faculty_dashbord")  # Redirect to the appropriate page
            else:
                print("Authentication failed! Incorrect password.")
        except User.DoesNotExist:
            print("Authentication failed! User not found.")

        return render(request, "faculty_login.html", {"error": "Invalid credentials!"})

    return render(request, "faculty_login.html")


from django.contrib.auth.decorators import login_required


@login_required
def faculty_dashbord(request):
    return render(request, "faculty/faculty_dashbord.html")


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


def technician_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        next_url = request.GET.get("next")  # Capture the `next` parameter

        try:
            user = User.objects.using("rit_e_approval").get(staff_id=username)
            if encrypt_password(password) == user.Password:
                request.session["user_id"] = user.staff_id
                request.session["role"] = user.role
                request.session["department"] = user.Department

                print(f"Session Data: {request.session.items()}")

                # Redirect to `next` if available, otherwise go to dashboard
                return redirect(next_url if next_url else "technician_dashboard")

            else:
                messages.error(request, "Invalid credentials!")
        except User.DoesNotExist:
            messages.error(request, "User not found!")

    return render(request, "technician_login.html")


from django.shortcuts import redirect


def technician_required(view_func):
    def wrapper(request, *args, **kwargs):
        if "user_id" not in request.session:  # Check if user is logged in
            return redirect("/technician_login?next=" + request.path)
        return view_func(request, *args, **kwargs)

    return wrapper


from django.contrib.auth.decorators import login_required


@technician_required
def technician_dashboard(request):
    return render(request, "technician/technician_dashboard.html")


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SubjectType, Category
from django.contrib.auth.decorators import login_required


@technician_required
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


@technician_required
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


@technician_required
def add_course(request):
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

    # Retrieve departments from 'rit_e_approval' database
    # department_list = Department.objects.using("rit_e_approval").all()
    department_list = (
        Student_cgpa.objects.using("rit_cgpatrack")
        .values_list("department", flat=True)
        .distinct()
    )
    for i in department_list:
        print(i)
    sem = list(range(1, 9))

    return render(
        request,
        "technician/add_course.html",
        {"form": form, "departments": department_list, "sem": sem},
    )


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import LabExercise, Course
from .forms import LabExerciseForm


@technician_required
def add_lab_exercise(request):
    courses = Course.objects.all()  # Fetch all courses
    departments = (
        Student_cgpa.objects.using("rit_cgpatrack")
        .values_list("department", flat=True)
        .distinct()
    )

    if request.method == "POST":
        form = LabExerciseForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Lab Exercise added successfully!")
                return redirect(
                    "add_lab_exercise"
                )  # Redirect to prevent duplicate form submission
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


@technician_required
def add_apparatus(request):
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
            semester = data.get("semester")
            experiment_name = str(data.get("experiment_name", "")).strip()
            apparatus_entries = data.get("apparatus_entries", [])

            # ✅ Validate required fields
            if not all(
                [
                    ex_no,
                    course_code,
                    practical_course,
                    regulation,
                    batch,
                    semester,
                    experiment_name,
                ]
            ):
                return JsonResponse({"error": "Missing required fields"}, status=400)

            # ✅ Validate experiment existence
            try:
                lab_exercise = LabExercise.objects.get(
                    Ex_no=ex_no, Ex_title=experiment_name
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

    # ✅ Load dropdown data efficiently
    sem_list = list(range(1, 9))
    dropdown_data = {
        "batches": list(LabExercise.objects.values_list("batch", flat=True).distinct()),
        "regulations": list(
            LabExercise.objects.values_list("regulations", flat=True).distinct()
        ),
        "course_code": list(
            LabExercise.objects.values_list("course_code", flat=True).distinct()
        ),
        "practical_course": list(
            LabExercise.objects.values_list("practical_course", flat=True).distinct()
        ),
        "ex_no": list(
            LabExercise.objects.values_list("Ex_no", flat=True).distinct()
        ),  # ✅ CharField values
        "experiment_name": list(
            LabExercise.objects.values_list("Ex_title", flat=True).distinct()
        ),
        "sem": sem_list,
        "department_list": list(
            Student_cgpa.objects.using("rit_cgpatrack")
            .values_list("department", flat=True)
            .distinct()
        ),
    }

    return render(request, "technician/add_apparatus.html", dropdown_data)


import itertools, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Student_cgpa, Department, Course, LabExercise, LabBatchAssignment

def add_batch(request):
    if request.method == 'POST':
        # Retrieve data from POST for new assignments
        lab_batch_no = request.POST.get('lab_batch_no', '').strip()
        course_code = request.POST.get('course_code', '').strip()
        experiment_no_input = request.POST.get('experiment_no', '').strip()  # Optional override
        assessment = request.POST.get('assessment', '').strip()  # Additional field
        selected_students = request.POST.getlist('selected_students')
        
        # Retrieve available experiment numbers from LabExercise
        exp_numbers = list(LabExercise.objects.values_list("Ex_no", flat=True).distinct())
        
        # Determine if we should continue the cycle or reset it (daily cycle example)
        last_assignment = LabBatchAssignment.objects.order_by('-created_at').first()
        
        if last_assignment and (timezone.now() - last_assignment.created_at) < datetime.timedelta(days=1):
            try:
                last_index = exp_numbers.index(last_assignment.ex_no)
                new_order = exp_numbers[last_index+1:] + exp_numbers[:last_index+1]
                exp_cycle = itertools.cycle(new_order)
            except ValueError:
                exp_cycle = itertools.cycle(exp_numbers)
        else:
            exp_cycle = itertools.cycle(exp_numbers)
        
        if not lab_batch_no:
            messages.error(request, "Please enter a lab batch number.")
        elif not selected_students:
            messages.error(request, "Please select at least one student.")
        else:
            success_count = 0
            for reg_no in selected_students:
                try:
                    student = Student_cgpa.objects.using('rit_cgpatrack').get(reg_no=reg_no)
                    # Use provided experiment number if given; otherwise, cycle
                    exp_no = experiment_no_input if experiment_no_input else next(exp_cycle)
                    LabBatchAssignment.objects.create(
                        student=student,
                        lab_batch_no=lab_batch_no,
                        course_code=course_code,
                        ex_no=exp_no,
                        assessment=assessment,
                        # Store the student's department and section at assignment time
                        department=student.department,
                        section=student.section,
                    )
                    success_count += 1
                except Student_cgpa.DoesNotExist:
                    messages.warning(request, f"Student with registration number {reg_no} does not exist.")
                    continue
            if success_count > 0:
                messages.success(request, f"Lab batch assignment saved for {success_count} student(s).")
            else:
                messages.error(request, "No lab batch assignments were made.")
            return redirect('add_batch')
    
    # GET request: Filtering students
    batch_filter = request.GET.get('batch', '').strip()
    department_filter = request.GET.get('department', '').strip()
    section_filter = request.GET.get('section', '').strip()
    
    filtered = batch_filter or department_filter or section_filter
    
    students = Student_cgpa.objects.using('rit_cgpatrack').none()
    if filtered:
        students = Student_cgpa.objects.using('rit_cgpatrack').all()
        if batch_filter:
            students = students.filter(batch=batch_filter)
        if department_filter:
            students = students.filter(department=department_filter)
        if section_filter:
            students = students.filter(section=section_filter)
        students = students.order_by('-gender')
        # Exclude students already assigned
        assigned_regnos = list(LabBatchAssignment.objects.values_list('student__reg_no', flat=True))
        students = students.exclude(reg_no__in=assigned_regnos)
    
    # Retrieve filter options:
    batches = Course.objects.values_list('batch', flat=True).distinct()
    department_list = Student_cgpa.objects.using('rit_cgpatrack').values_list('department', flat=True).distinct()
    section_options = Student_cgpa.objects.using('rit_cgpatrack').values_list('section', flat=True).distinct()
    # Additional select options from LabExercise:
    course_codes = list(LabExercise.objects.values_list("course_code", flat=True).distinct())
    ex_nos = list(LabExercise.objects.values_list("Ex_no", flat=True).distinct())
    
    # Retrieve existing assignments (you can filter by date if needed)
    lab_assignments = LabBatchAssignment.objects.all().order_by('-created_at')
    
    context = {
        'students': students,
        'filtered': filtered,
        'batch_filter': batch_filter,
        'department_filter': department_filter,
        'section_filter': section_filter,
        'batches': batches,
        'departments': department_list,
        'section_options': section_options,
        'course_code': course_codes,
        'ex_no': ex_nos,
        'lab_assignments': lab_assignments,
    }
    return render(request, 'technician/add_batch.html', context)



from django.shortcuts import render
from .models import LabBatchAssignment, LabExercise

def view_batches(request):
    """
    Display Lab Batch Assignments only when filters are applied.
    Initially, no data is shown.
    """
    # Retrieve filter values from GET request
    course_code_filter = request.GET.get('course_code', '')
    department_filter = request.GET.get('department', '')
    section_filter = request.GET.get('section', '')
    assessment_filter = request.GET.get('assessment', '')
    lab_batch_no_filter = request.GET.get('lab_batch_no', '')

    # Check if any filter is applied
    filters_applied = any([course_code_filter, department_filter, section_filter, assessment_filter, lab_batch_no_filter])

    # Initially, do not fetch any records until at least one filter is applied
    assignments = LabBatchAssignment.objects.none()  # Empty queryset

    if filters_applied:
        assignments = LabBatchAssignment.objects.all().order_by('-created_at')

        # Apply filters
        if course_code_filter:
            assignments = assignments.filter(course_code=course_code_filter)
        if department_filter:
            assignments = assignments.filter(department=department_filter)
        if section_filter:
            assignments = assignments.filter(section=section_filter)
        if assessment_filter:
            assignments = assignments.filter(assessment=assessment_filter)
        if lab_batch_no_filter:
            assignments = assignments.filter(lab_batch_no=lab_batch_no_filter)

    # Retrieve distinct values for dropdowns
    course_codes = LabExercise.objects.values_list('course_code', flat=True).distinct().order_by('course_code')
    departments = LabBatchAssignment.objects.values_list('department', flat=True).distinct().order_by('department')
    sections = LabBatchAssignment.objects.values_list('section', flat=True).distinct().order_by('section')
    lab_batches = LabBatchAssignment.objects.values_list('lab_batch_no', flat=True).distinct().order_by('lab_batch_no')
    assessments = LabBatchAssignment.objects.values_list('assessment', flat=True).distinct().order_by('assessment')

    context = {
        'assignments': assignments,
        'course_codes': course_codes,
        'departments': departments,
        'sections': sections,
        'assessments': assessments,
        'lab_batch_nos': lab_batches,
        'filters_applied': filters_applied,  # Send filter status to template
    }
    return render(request, 'technician/view_batches.html', context)


def edit_lab_batch_assignment(request, assignment_id):
    """
    Edit a specific Lab Batch Assignment.
    """
    assignment = get_object_or_404(LabBatchAssignment, id=assignment_id)
    # Retrieve additional select options from LabExercise:
    course_codes = list(LabExercise.objects.values_list("course_code", flat=True).distinct())
    ex_nos = list(LabExercise.objects.values_list("Ex_no", flat=True).distinct())

    if request.method == 'POST':
        lab_batch_no = request.POST.get('lab_batch_no', '').strip()
        course_code = request.POST.get('course_code', '').strip()
        experiment_no = request.POST.get('experiment_no', '').strip()
        assessment = request.POST.get('assessment', '').strip()
        
        if not lab_batch_no:
            messages.error(request, "Lab batch number is required.")
        else:
            assignment.lab_batch_no = lab_batch_no
            assignment.course_code = course_code
            assignment.ex_no = experiment_no
            assignment.assessment = assessment
            assignment.save()
            messages.success(request, "Lab batch assignment updated successfully.")
            return redirect('view_batches')  # Redirect back to the batches page
    
    context = {
        'assignment': assignment,
        'course_codes': course_codes,
        'ex_nos': ex_nos,
    }
    return render(request, 'technician/edit_lab_batch.html', context)


from django.contrib.auth import logout

@technician_required
def technician_logout(request):
    logout(request)  # Clear session and log out user
    return redirect("technician_login")  # Redirect to login page
