import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from code_runner import run_python_code

logger = logging.getLogger(__name__)

def editor_view(request):
    """Render the main editor page"""
    return render(request, 'editor.html')

@csrf_exempt
@require_http_methods(["POST"])
def run_code_view(request):
    """Execute Python code and return results"""
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        user_input = data.get('input', '')
        
        if not code.strip():
            return JsonResponse({
                'success': False,
                'error': 'No code provided'
            })
        
        # Run the code
        result = run_python_code(code, user_input)
        
        return JsonResponse({
            'success': True,
            'output': result['output'],
            'error': result['error'],
            'needs_input': result['needs_input']
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Error running code: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })