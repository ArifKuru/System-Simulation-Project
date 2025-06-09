from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.shortcuts import render, redirect
from pages.forms import ProjectForm
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import re

from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_http_methods

import math
import random

import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google import genai
from google.genai import types
from pages.models import Projects, Stocks, Events, Effects


@csrf_exempt
def generate_simulation_from_prompt(request):
    try:
        body = json.loads(request.body)
        prompt = body.get("prompt")
        project_id = body.get("project_id")

        if not prompt or not project_id:
            return JsonResponse({"success": False, "error": "Missing prompt or project_id"}, status=400)

        # Google GenAI setup
        client = genai.Client(api_key="AIzaSyCDAwuMk-_1Sno9-KKFb-3mYIBj7R-t_Ds")
        model = "gemini-2.5-flash-preview-04-17"

        # System instruction
        system_instruction = types.Part.from_text(text="""You are a Simulation Creator AI. Your task is to generate JSON configuration for a stock-based simulation system.

### Output Format:
Your output must be in valid JSON.

### Core Structure:
The system consists of:
1. **Stocks** (name, value, events[])
2. **Events** (name, stock, possibility, effects[])
3. **Effects** (event, target_stock, effect_expression)

### Expressions can use stock('X') format and include logic like '*2', '+ stock('Y')', etc.

### Output Example:
{
  "stocks": [
    {
      "name": "Stock A",
      "value": 100,
      "events": [
        {
          "name": "Double",
          "stock": "Stock A",
          "possibility": "2",
          "effects": [
            {
              "event": "Double",
              "target_stock": "Stock A",
              "effect_expression": "*2"
            }
          ]
        }
      ]
    }
  ]
}
""")

        # Prepare generation request
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=[system_instruction],
        )

        # Generate from Gemini
        output = ""
        for chunk in client.models.generate_content_stream(model=model, contents=contents, config=config):
            output += chunk.text

        # Parse JSON from Gemini response
        # Try to extract JSON between code block fences
        match = re.search(r"```json\n(.*?)```", output, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            json_str = output  # fallback

        data = json.loads(json_str)

        stocks_data = data.get("stocks", [])

        # Fetch project
        project = Projects.objects.get(id=project_id)

        # Insert into DB
        for stock_data in stocks_data:
            stock = Stocks.objects.create(
                project=project,
                name=stock_data["name"],
                value=stock_data["value"],
            )
            for event_data in stock_data.get("events", []):
                event = Events.objects.create(
                    stock=stock,
                    name=event_data["name"],
                    possibility=event_data["possibility"]
                )
                for effect_data in event_data.get("effects", []):
                    target_stock = Stocks.objects.filter(project=project, name=effect_data["target_stock"]).first()
                    if target_stock:
                        Effects.objects.create(
                            event=event,
                            target_stock=target_stock,
                            effect_expression=effect_data["effect_expression"]
                        )

        return JsonResponse({"success": True, "message": "Simulation created successfully", "raw_json": data})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_effect(request, effect_id):
    try:
        Effects.objects.get(id=effect_id).delete()
        return JsonResponse({"success": True})
    except Effects.DoesNotExist:
        return JsonResponse({"success": False, "error": "Effect not found"}, status=404)

@require_GET
def read_effect(request, effect_id):
    try:
        effect = Effects.objects.select_related("event", "target_stock").get(id=effect_id)
        data = {
            "id": effect.id,
            "event": effect.event.name,
            "target_stock": effect.target_stock.name,
            "effect_expression": effect.effect_expression
        }
        return JsonResponse({"success": True, "effect": data})
    except Effects.DoesNotExist:
        return JsonResponse({"success": False, "error": "Effect not found"}, status=404)

@require_GET
def list_effects(request):
    event_id = request.GET.get("event_id")
    if not event_id:
        return JsonResponse({"success": False, "error": "Missing event_id"}, status=400)

    effects = Effects.objects.filter(event_id=event_id).select_related("target_stock")
    data = [
        {
            "id": effect.id,
            "target_stock": effect.target_stock.name,
            "effect_expression": effect.effect_expression
        }
        for effect in effects
    ]
    return JsonResponse({"success": True, "effects": data})

@csrf_exempt
@require_http_methods(["POST"])
def create_effect(request):
    try:
        data = json.loads(request.body)
        event_id = data.get("event_id")
        stock_id = data.get("target_stock_id")
        expr = data.get("effect_expression")

        if not all([event_id, stock_id, expr]):
            return JsonResponse({"success": False, "error": "Missing fields"}, status=400)

        event = Events.objects.get(id=event_id)
        target_stock = Stocks.objects.get(id=stock_id)

        effect = Effects.objects.create(
            event=event,
            target_stock=target_stock,
            effect_expression=expr
        )

        return JsonResponse({"success": True, "effect_id": effect.id})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

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
    # Retrieve the specified project
    project = Projects.objects.get(id=project_id)

    # This list will store the results of each simulation step
    results = []

    # Loop through the number of steps to simulate
    for i in range(step_count):
        # Run a single simulation step
        result = run_simulation(project_id)

        # Safely extract the selected event, if any
        selected_event = result.get("selected_event", {})
        event_name = selected_event.get("name") if selected_event else None

        # Get the current values of all stocks in the project
        stock_values = {
            stock.name: stock.value
            for stock in Stocks.objects.filter(project=project)
        }

        # Collect detailed stock update info for this step
        stock_updates = []
        for update in result.get("stock_updated", []):
            stock_updates.append({
                "stock_name": update.get("stock"),
                "old_value": update.get("old_value"),
                "new_value": update.get("new_value"),
                "effect": update.get("effect")
            })

        # Append the step result with all relevant data
        results.append({
            "step": i + 1,                        # Step number (1-based)
            "time": result.get("time"),           # Time until this event occurred
            "event": event_name,                  # The name of the event that was triggered
            "stock_updates": stock_updates,       # Detailed list of stock changes
            "stock_values": stock_values          # Current values of all stocks at this step
        })

    # Return the full list of simulation step results
    return results


# This view allows running multiple simulation steps at once for a given project.
# It is CSRF-exempt to allow POST requests from the frontend (e.g., via AJAX or fetch API).
@csrf_exempt
def simulate_multiple(request, project_id):
    try:
        # Parse the incoming JSON payload
        data = json.loads(request.body)

        # Get the number of steps to simulate, default to 100 if not provided
        steps = int(data.get("steps", 100))

        # Run the simulation for the given number of steps
        results = run_simulation_steps(project_id, steps)

        # Return the simulation results as a JSON response
        return JsonResponse({"success": True, "results": results})

    except Exception as e:
        # If an error occurs, return the error message and set HTTP status to 500
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# This view handles the simulation request for a specific project.
# It is marked as csrf_exempt since it may be triggered via JavaScript (e.g., from an AJAX request).
@csrf_exempt
def simulate_project(request, project_id):
    try:
        # Run the simulation logic for the given project ID.
        result = run_simulation(project_id)

        # Return the simulation result as a JSON response.
        return JsonResponse({"success": True, "result": result})

    except Exception as e:
        # If an error occurs during simulation, return the error message with HTTP 500 status.
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def run_simulation(project_id):
    # Retrieve the project using the given ID
    project = Projects.objects.get(id=project_id)

    # Fetch all events related to the project's stocks and preload their effects
    events = Events.objects.filter(stock__project=project).prefetch_related("effects")

    # Step 1: Evaluate the possibility expression for each event
    for event in events:
        # The evaluated numeric probability is temporarily stored in a private attribute
        event._parsed_possibility = evaluate_expression(event.possibility, project)

    # Calculate the total probability (sum of all event possibilities)
    total_p = sum(e._parsed_possibility for e in events if e._parsed_possibility)

    # Step 2: Determine the time to the next event using an exponential distribution
    rand = random.random()
    time = -math.log(1 - rand) / total_p if total_p > 0 else float('inf')

    # Step 3: Select an event using roulette wheel (probabilistic) selection
    random_factor = random.random()
    cumulative = 0
    selected_event = None

    for e in events:
        p = e._parsed_possibility or 0
        # Check if the random value falls within this event's probability range
        if cumulative <= random_factor < cumulative + (p / total_p):
            selected_event = e
            break
        cumulative += (p / total_p)

    # Prepare the result structure
    result = {
        "time": round(time, 3),  # Time until the next event
        "selected_event": None,  # Details of the triggered event
        "stock_updated": []  # List of all stock updates caused by this event
    }

    if selected_event:
        updated = []

        # Apply each effect of the selected event
        for effect in selected_event.effects.all():
            target = effect.target_stock
            old_value = target.value
            try:
                # Compute the new value by evaluating the effect expression
                new_value = evaluate_expression(f"{old_value}{effect.effect_expression}", project)
                target.value = new_value
                target.save()

                # Record the change
                updated.append({
                    "stock": target.name,
                    "old_value": old_value,
                    "new_value": new_value,
                    "effect": effect.effect_expression
                })
            except Exception as e:
                # If an error occurs during evaluation, skip this effect
                continue

        # Store selected event and its updates in the result
        result["selected_event"] = {
            "id": selected_event.id,
            "name": selected_event.name,
        }
        result["stock_updated"] = updated

    # Return the complete simulation step result
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
    events = Events.objects.filter(stock_id=stock_id).values('id', 'name', 'possibility')
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
