from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    """
    Form for creating and updating tasks.
    Widgets are fully styled here so templates can simply render {{ form.field }}.
    """

    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'status', 'due_date']

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'What do you need to do?',
                'autofocus': True,
                'id': 'id_title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add details about this task...',
                'id': 'id_description',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_priority',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_status',
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'id': 'id_due_date',
            }),
        }

        labels = {
            'title': 'Task Title',
            'description': 'Description',
            'priority': 'Priority',
            'status': 'Status',
            'due_date': 'Due Date',
        }

        help_texts = {
            'due_date': 'Optional: Set a deadline for this task',
        }

    # Override choice labels with emoji for better UX in the select dropdowns
    PRIORITY_CHOICES_DISPLAY = [
        ('low', '🟢 Low Priority'),
        ('medium', '🟡 Medium Priority'),
        ('high', '🔴 High Priority'),
    ]

    STATUS_CHOICES_DISPLAY = [
        ('todo', '⏳ To Do'),
        ('in_progress', '🔄 In Progress'),
        ('done', '✅ Done'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Replace choices with emoji-labeled versions
        self.fields['priority'].choices = self.PRIORITY_CHOICES_DISPLAY
        self.fields['status'].choices = self.STATUS_CHOICES_DISPLAY

    def clean(self):
        cleaned_data = super().clean()
        # Sync completed boolean based on status
        status = cleaned_data.get('status')
        if status == 'done':
            cleaned_data['completed'] = True
        else:
            cleaned_data['completed'] = False
        return cleaned_data