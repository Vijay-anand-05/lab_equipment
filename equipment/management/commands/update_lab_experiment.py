import itertools
from django.core.management.base import BaseCommand
from django.utils import timezone
from equipment.models import LabBatchAssignment, LabExercise

class Command(BaseCommand):
    help = "Cycle the experiment number for LabBatchAssignment records created today."

    def handle(self, *args, **options):
        # Get available experiment numbers from LabExercise
        exp_numbers = list(LabExercise.objects.values_list("Ex_no", flat=True).distinct())
        if not exp_numbers:
            self.stdout.write(self.style.ERROR("No experiment numbers found in LabExercise."))
            return

        # Get today's date
        today = timezone.now().date()

        # Retrieve LabBatchAssignment records created today
        assignments = LabBatchAssignment.objects.filter(created_at__date=today)
        if not assignments.exists():
            self.stdout.write("No lab batch assignments created today.")
            return

        updated_count = 0
        for assignment in assignments:
            # Determine the next experiment number in the cycle
            try:
                current_index = exp_numbers.index(assignment.ex_no)
                next_index = (current_index + 1) % len(exp_numbers)
                new_ex_no = exp_numbers[next_index]
            except ValueError:
                # If current ex_no isn't in our list, default to the first experiment number
                new_ex_no = exp_numbers[0]
            
            assignment.ex_no = new_ex_no
            assignment.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Updated experiment numbers for {updated_count} assignments."))
