from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .models import Projects
from django.shortcuts import render, redirect
from .forms import ProjectForm
from django.shortcuts import render, get_object_or_404
from .models import Projects
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Projects, Stocks

from django.views.decorators.http import require_GET

@require_GET
def list_stocks_api(request):
    project_id = request.GET.get('project_id')
    try:
        project = Projects.objects.get(id=project_id)
        stocks = project.stocks.all().values('id', 'name', 'value')
        return JsonResponse({'success': True, 'stocks': list(stocks)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)



@csrf_exempt
def create_stock_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            project_id = data.get('project_id')
            name = data.get('name')
            value = data.get('value')

            if not all([project_id, name, value]):
                return JsonResponse({'success': False, 'error': 'Missing fields'}, status=400)

            project = Projects.objects.get(id=project_id)
            Stocks.objects.create(project=project, name=name, value=value)
            return JsonResponse({'success': True, 'message': 'Stock created successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


def project_detail(request, project_id):
    project = get_object_or_404(Projects, id=project_id)
    return render(request, 'pages/project_detail.html', {'project': project})

def home(request):
    projects = Projects.objects.all().order_by('-created_at')
    return render(request, 'pages/home.html', {'projects': projects})


def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProjectForm()
    return render(request, 'pages/create.html', {'form': form})
