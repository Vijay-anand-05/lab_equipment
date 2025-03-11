from django import forms
from .models import Course, Department  # Assuming Department is the model for application_departments

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Retrieve departments from the `rit_e_approval` database
        self.fields["department"].queryset = Department.objects.using("rit_e_approval").all()


from django import forms
from .models import LabExercise

class LabExerciseForm(forms.ModelForm):
    class Meta:
        model = LabExercise
        fields = "__all__"  # Includes all fields from the model
        
        
        
from django import forms
from .models import Payment

class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["payment_proof"]  # Only allow proof upload

