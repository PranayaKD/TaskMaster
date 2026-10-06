from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views import View
from django.db.models import Q, Count

from .models import Task
from .forms import TaskForm


def home(request):
    """Public landing page — no auth required."""
    return render(request, "tasks/home.html")


class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    login_url = 'login'

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.filter(user=user)

        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        search = self.request.GET.get('search', '').strip()

        if status:
            qs = qs.filter(status=status)

        if priority:
            qs = qs.filter(priority=priority)

        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 🔥 Sidebar counts in ONE query
        counts = (
            Task.objects
            .filter(user=user)
            .values('status')
            .annotate(total=Count('id'))
        )

        status_map = {c['status']: c['total'] for c in counts}

        context['todo_count'] = status_map.get('todo', 0)
        context['in_progress_count'] = status_map.get('in_progress', 0)
        context['done_count'] = status_map.get('done', 0)

        # 🔥 Pagination range (template-safe)
        page_obj = context['page_obj']
        paginator = context['paginator']

        start = max(page_obj.number - 2, 1)
        end = min(page_obj.number + 2, paginator.num_pages)
        context['has_filters'] = any([
    self.request.GET.get('status'),
    self.request.GET.get('priority'),
    self.request.GET.get('search'),
])

        context['page_range'] = range(start, end + 1)

        return context

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    login_url = 'login'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')
    login_url = 'login'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.completed = (form.instance.status == 'done')
        messages.success(self.request, 'Task created successfully!')
        return super().form_valid(form)


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')
    login_url = 'login'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj

    def form_valid(self, form):
        form.instance.completed = (form.instance.status == 'done')
        messages.success(self.request, 'Task updated successfully!')
        return super().form_valid(form)


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')
    login_url = 'login'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Task deleted successfully!')
        return super().form_valid(form)



@login_required(login_url='login')
def toggle_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)

    task.completed = not task.completed
    task.status = 'done' if task.completed else 'todo'
    task.save(update_fields=['completed', 'status'])

    messages.success(
        request,
        f'Task "{task.title}" {"completed" if task.completed else "marked incomplete"}'
    )
    return redirect('task-list')



class SignupView(View):

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('task-list')
        return render(request, 'tasks/signup.html', {
            'form': UserCreationForm()
        })

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('task-list')

        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! 🎉")
            return redirect('task-list')

        return render(request, 'tasks/signup.html', {'form': form})
