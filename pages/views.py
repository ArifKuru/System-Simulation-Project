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
import re

from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

import math
import random
from .models import Projects, Events, Stocks
@csrf_exempt
def reset_project_stocks(request, project_id):
    try:
        stocks = Stocks.objects.filter(project_id=project_id)
        for stock in stocks:
            stock.value = stock.initial_value
            stock.save()
        return JsonResponse({"success": True, "message": "All stock values reset to initial values."})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def run_simulation_steps(project_id, step_count):
    project = Projects.objects.get(id=project_id)
    stock_names = list(Stocks.objects.filter(project=project).values_list("name", flat=True))

    results = []

    for i in range(step_count):
        result = run_simulation(project_id)

        # tüm stockların anlık değerlerini al
        stock_values = {
            stock.name: stock.value
            for stock in Stocks.objects.filter(project=project)
        }

        results.append({
            "step": i + 1,
            "time": result["time"],
            "event": result["selected_event"]["name"] if result["selected_event"] else None,
            "stock": result["stock_updated"]["name"] if result["stock_updated"] else None,
            "old_value": result["stock_updated"]["old_value"] if result["stock_updated"] else None,
            "new_value": result["stock_updated"]["new_value"] if result["stock_updated"] else None,
            "stock_values": stock_values
        })

    return results



@csrf_exempt
def simulate_multiple(request, project_id):
    try:
        data = json.loads(request.body)
        steps = int(data.get("steps", 100))
        results = run_simulation_steps(project_id, steps)
        return JsonResponse({"success": True, "results": results})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
def simulate_project(request, project_id):
    try:
        result = run_simulation(project_id)
        return JsonResponse({"success": True, "result": result})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

def run_simulation(project_id):
    project = Projects.objects.get(id=project_id)
    events = Events.objects.filter(stock__project=project)

    # 1. possibility'leri float'a çevir
    for event in events:
        event._parsed_possibility = evaluate_expression(event.possibility, project)

    total_p = sum(e._parsed_possibility for e in events if e._parsed_possibility)

    # 2. time hesapla
    rand = random.random()
    time = -math.log(1 - rand) / total_p if total_p > 0 else float('inf')

    # 3. random seçim
    random_factor = random.random()
    cumulative = 0
    selected_event = None

    for e in events:
        p = e._parsed_possibility or 0
        if cumulative <= random_factor < cumulative + (p / total_p):
            selected_event = e
            break
        cumulative += (p / total_p)

    result = {
        "time": round(time, 3),
        "selected_event": None,
        "stock_updated": None
    }

    # 4. etkiyi uygula
    if selected_event:
        stock = selected_event.stock
        old_value = stock.value
        effect_result = evaluate_expression(f"{old_value}{selected_event.effect}", project)
        stock.value = effect_result
        stock.save()

        result["selected_event"] = {
            "id": selected_event.id,
            "name": selected_event.name,
            "effect": selected_event.effect,
            "stock": stock.name
        }
        result["stock_updated"] = {
            "name": stock.name,
            "old_value": old_value,
            "new_value": effect_result
        }
    return result


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_stock(request, stock_id):
    try:
        Stocks.objects.get(id=stock_id).delete()
        return JsonResponse({'success': True})
    except Stocks.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Stock not found'}, status=404)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_event(request, event_id):
    try:
        Events.objects.get(id=event_id).delete()
        return JsonResponse({'success': True})
    except Events.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Event not found'}, status=404)

def stock_variables(request):
    project_id = request.GET.get("project_id")
    try:
        stocks = Stocks.objects.filter(project_id=project_id).values_list('name', flat=True)
        return JsonResponse({"success": True, "variables": list(stocks)})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
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



from .models import Events

def read_stock(request, stock_id):
    try:
        stock = Stocks.objects.get(id=stock_id)
        data = {'id': stock.id, 'name': stock.name, 'value': stock.value}
        return JsonResponse({'success': True, 'stock': data})
    except Stocks.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Stock not found'}, status=404)

def list_events(request):
    stock_id = request.GET.get('stock_id')
    events = Events.objects.filter(stock_id=stock_id).values('id', 'name', 'possibility', 'effect')
    return JsonResponse({'success': True, 'events': list(events)})

@csrf_exempt
def create_event(request):
    try:
        data = json.loads(request.body)
        stock = Stocks.objects.get(id=data['stock_id'])
        Events.objects.create(
            stock=stock,
            name=data['name'],
            possibility=data['possibility'],
            effect=data['effect']
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def evaluate_expression(expr, context_project):
    """
    Evaluates a string expression like 'stock("X") * 0.5' dynamically.
    Replaces stock("Name") with the actual value from that stock.
    """
    pattern = r"stock\('([^']+)'\)"

    def stock_lookup(match):
        stock_name = match.group(1)
        try:
            stock = Stocks.objects.get(project=context_project, name=stock_name)
            return str(stock.value)
        except Stocks.DoesNotExist:
            return "0"  # or raise error

    safe_expr = re.sub(pattern, stock_lookup, expr)

    try:
        return eval(safe_expr)
    except Exception as e:
        return None  # or log error
