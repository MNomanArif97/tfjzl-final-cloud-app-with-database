from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Course, Lesson, Instructor, Learner, Enrollment, Question, Choice, Submission
import logging

logger = logging.getLogger(__name__)

class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        return Course.objects.order_by('-pub_date')[:10]


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'


def enroll(request, course_id):
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=course_id)
        if not Enrollment.objects.filter(user=request.user, course=course).exists():
            Enrollment.objects.create(user=request.user, course=course, mode='honor')
        return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))


# Task 6: Form Submission Processing View
def submit(request, course_id):
    if not request.user.is_authenticated:
        return redirect('onlinecourse:login')
        
    course = get_object_or_404(Course, pk=course_id)
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=course)
    except Enrollment.DoesNotExist:
        return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))

    if request.method == 'POST':
        submission = Submission.objects.create(enrollment=enrollment)
        selected_choice_ids = []
        
        for key, value in request.POST.items():
            if key.startswith('choice_'):
                selected_choice_ids.append(int(value))
                
        choices = Choice.objects.filter(id__in=selected_choice_ids)
        submission.choices.add(*choices)
        submission.save()
        
        return redirect('onlinecourse:show_exam_result', course_id=course.id, submission_id=submission.id)


# Task 7: Evaluation & Exam Results View
def show_exam_result(request, course_id, submission_id):
    if not request.user.is_authenticated:
        return redirect('onlinecourse:login')

    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    selected_choices = submission.choices.all()
    selected_ids = [c.id for c in selected_choices]
    
    total_score = 0
    earned_score = 0
    questions_results = []

    for question in course.question_set.all():
        total_score += question.grade
        is_correct = question.is_get_score(selected_ids)
        if is_correct:
            earned_score += question.grade
        questions_results.append({
            'question': question,
            'is_correct': is_correct
        })

    passed = earned_score >= (total_score * 0.6) if total_score > 0 else False

    context = {
        'course': course,
        'submission': submission,
        'earned_score': earned_score,
        'total_score': total_score,
        'passed': passed,
        'questions_results': questions_results,
        'selected_ids': selected_ids
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)

# Placeholder authentication views (ensure your existing registration/login/logout match your boilerplate template logic)
def registration_request(request):
    pass

def login_request(request):
    pass

def logout_request(request):
    pass