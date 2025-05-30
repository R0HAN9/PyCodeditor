import docker
import tempfile
import os
import time
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def run_python_code(code, user_input=""):
    """
    Execute Python code in a Docker container
    """
    client = None
    container = None
    
    try:
        # Connect to Docker
        client = docker.from_env()
        
        # Create temporary file with the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Prepare the command
        if user_input:
            # If input is provided, echo it to the python process
            cmd = f'echo "{user_input}" | python /app/code.py'
        else:
            cmd = 'python /app/code.py'
        
        # Run container
        container = client.containers.run(
            settings.DOCKER_IMAGE,
            command=['sh', '-c', cmd],
            volumes={temp_file: {'bind': '/app/code.py', 'mode': 'ro'}},
            network_disabled=True,
            mem_limit='128m',
            cpu_count=1,
            detach=True,
            remove=True,
            stdout=True,
            stderr=True
        )
        
        # Wait for completion with timeout
        start_time = time.time()
        while container.status != 'exited':
            if time.time() - start_time > settings.DOCKER_TIMEOUT:
                container.kill()
                return {
                    'output': '',
                    'error': 'Code execution timed out',
                    'needs_input': False
                }
            time.sleep(0.1)
            container.reload()
        
        # Get output
        logs = container.logs(stdout=True, stderr=True).decode('utf-8')
        
        # Separate stdout and stderr
        output = ""
        error = ""
        
        if container.attrs['State']['ExitCode'] == 0:
            output = logs
        else:
            error = logs
        
        return {
            'output': output,
            'error': error,
            'needs_input': 'input(' in code and not user_input
        }
        
    except docker.errors.ImageNotFound:
        return {
            'output': '',
            'error': 'Python runtime not available',
            'needs_input': False
        }
    except docker.errors.APIError as e:
        logger.error(f"Docker API error: {str(e)}")
        return {
            'output': '',
            'error': 'Docker service unavailable',
            'needs_input': False
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'output': '',
            'error': f'Execution error: {str(e)}',
            'needs_input': False
        }
    finally:
        # Cleanup
        try:
            if 'temp_file' in locals():
                os.unlink(temp_file)
        except:
            pass
        
        try:
            if container:
                container.remove(force=True)
        except:
            pass
        
        try:
            if client:
                client.close()
        except:
            pass