from datetime import timezone
from django.db import models

####################### student################
class Student(models.Model):
    student_regno = models.CharField(max_length=255, primary_key=True)
    student_dob = models.DateField(null=True, blank=True)
    student_password = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "core_student"
        managed = False

    # ------------------------ RIT CGPA TRACK ------------#


from django.db import models  # type: ignore


class Student_cgpa(models.Model):
    reg_no = models.CharField(max_length=20, primary_key=True)
    batch = models.CharField(max_length=100)
    student_name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    section = models.CharField(
        max_length=10, blank=True, null=True
    )  # New field for section
    gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female")],
        blank=True,
        null=True,
    )  # New field for gender
    cgpa = models.FloatField()
    sslc = models.FloatField()
    hsc = models.CharField(max_length=20, blank=True, null=True)
    diploma = models.CharField(max_length=20, blank=True, null=True)
    bag_of_log = models.IntegerField()
    history_of_arrear = models.IntegerField()
    admission_type = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)

    # Semester fields as CharField to store grades or GPAs
    semester1 = models.CharField(max_length=20, blank=True, null=True)
    semester2 = models.CharField(max_length=20, blank=True, null=True)
    semester3 = models.CharField(max_length=20, blank=True, null=True)
    semester4 = models.CharField(max_length=20, blank=True, null=True)
    semester5 = models.CharField(max_length=20, blank=True, null=True)
    semester6 = models.CharField(max_length=20, blank=True, null=True)
    semester7 = models.CharField(max_length=20, blank=True, null=True)
    semester8 = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = "application_student"
        managed = False  # Since the table already exists in the database


##################### faculty ##########################
class User(models.Model):
    Name = models.CharField(max_length=100)
    user_name = models.CharField(max_length=100)
    staff_id = models.CharField(max_length=100)
    Department = models.CharField(max_length=100)
    Department_code = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    default_role = models.CharField(max_length=200, null=True, blank=True)
    Password = models.CharField(max_length=100)
    confirm_Password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.Name}-({self.role}-{self.staff_id})"

    class Meta:
        db_table = "application_user"
        managed = False


# ------------------------------ Course Master ------------------------

from django.db import models


class SubjectType(models.Model):
    type_name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "subject_type_table"  # Custom table name

    def __str__(self):
        return self.type_name


from django.db import models


class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "category_table"  # Custom table name

    def __str__(self):
        return self.category_name


class Course(models.Model):

    batch = models.CharField(max_length=50)
    regulations = models.CharField(max_length=20)
    # degree = models.CharField(max_length=10)
    department = models.CharField(max_length=50)
    semester = models.IntegerField()
    course_code = models.CharField(max_length=10, unique=True)
    course_title = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subject_type = models.ForeignKey(SubjectType, on_delete=models.CASCADE)
    lecturer = models.IntegerField()
    tutorial = models.IntegerField()
    practical = models.IntegerField()
    total_contact_periods = models.IntegerField()
    credits = models.IntegerField()

    class Meta:
        db_table = "course"

    def __str__(self):
        return f"{self.course_code} - {self.course_title}"


class Department(models.Model):  # Keeping the lowercase model name
    dept_code = models.CharField(max_length=200, primary_key=True)
    department = models.CharField(max_length=500)

    class Meta:
        db_table = "application_departments"  # Mapping to existing table
        managed = False  # Since it's from an external DB


class LabExercise(models.Model):
    Ex_no = models.CharField(max_length=50)  # Exercise Code
    practical_course = models.CharField(max_length=255)
    course_code = models.CharField(max_length=10)
    Ex_title = models.CharField(max_length=255)
    description = models.TextField()
    regulations = models.CharField(max_length=50)
    batch = models.CharField(max_length=50)
    sem = models.IntegerField()
    department = models.CharField(max_length=50)

    def _str_(self):
        return f"{self.title} ({self.lab.name})"


class Apparatus(models.Model):
    ex_no = models.CharField(max_length=50)
    course_code = models.CharField(max_length=50)
    practical_course = models.CharField(max_length=255)
    experiment_name = models.CharField(max_length=255)
    regulation = models.CharField(max_length=50)
    batch = models.CharField(max_length=50)
    semester = models.IntegerField()
    apparatus_name = models.CharField(max_length=255)
    range_specification = models.CharField(max_length=100, blank=True, null=True)
    quantity_available = models.CharField(max_length=10)
    department = models.CharField(max_length=50)
    remarks = models.TextField(blank=True, null=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'equipment_apparatus'  # Specify the correct table name

class LabBatchAssignment(models.Model):
    
    """
    Stores the lab batch assignment details for a student.
    Now includes an 'assessment' field and also stores the student's
    department and section at the time of assignment.
    """

    student = models.ForeignKey(Student_cgpa, on_delete=models.CASCADE, related_name="lab_assignments")
    lab_batch_no = models.CharField(max_length=50)
    course_code = models.CharField(max_length=10)
    ex_no = models.CharField(max_length=50)
    assessment = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    section = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lab_batch_assignment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.reg_no} - {self.student.student_name}"



# Apparatus Request Model
class ApparatusRequest(models.Model):
    REQUEST_TYPES = [
        ("Request", "Request"),
        ("Return", "Return"),
    ]
    technician_staff_id = models.CharField(max_length=100, null=True, blank=True)
    student = models.ForeignKey(Student_cgpa, on_delete=models.CASCADE)
    lab_batch = models.ForeignKey(LabBatchAssignment, on_delete=models.CASCADE, null=True, blank=True)
    apparatus = models.ForeignKey(Apparatus, on_delete=models.CASCADE, null=True, blank=True)
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPES, default="Request")
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Accepted", "Accepted"),
            ("Rejected", "Rejected"),
            ("Returned", "Returned"),
            ("Damaged", "Damaged"),
        ],
        default="Pending",
    )
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    technician_remarks = models.TextField(blank=True, null=True)
    accepted_message = models.TextField(blank=True, null=True)
    return_date = models.DateTimeField(null=True, blank=True)
    hod_approval = models.BooleanField(default=False)
    damaged_apparatus = models.ManyToManyField(
        "Apparatus",
        through="ApparatusRequestDamage",  # Use the through model
        related_name="damaged_requests",
        blank=True,
    )
    course_code = models.CharField(max_length=20, blank=True, null=True)
    verified = models.BooleanField(default=False)
    verified_date = models.DateTimeField(null=True, blank=True)
    damaged_apparatus = models.ManyToManyField(
    "Apparatus",
    through="ApparatusRequestDamage",  # Use the through model
    related_name="damaged_requests",
    blank=True,
)

    class Meta:
        db_table = "apparatus_request"
        ordering = ["-request_date"]

    def __str__(self):
        return f"{self.student.student_name} - {self.apparatus.apparatus_name} - {self.status} ({self.request_type})"

class ApparatusRequestDamage(models.Model):
    apparatus_request = models.ForeignKey(ApparatusRequest, on_delete=models.CASCADE)
    apparatus = models.ForeignKey(Apparatus, on_delete=models.CASCADE)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    

    class Meta:
        db_table = "apparatus_request_damage"