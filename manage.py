#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import json
from pathlib import Path


DEBUG_LOG_PATH = Path(__file__).resolve().parent / 'debug-264829.log'


def _debug_log(hypothesis_id, location, message, data=None, run_id='initial'):
    # #region agent log
    payload = {
        'sessionId': '264829',
        'runId': run_id,
        'hypothesisId': hypothesis_id,
        'location': location,
        'message': message,
        'data': data or {},
        'timestamp': int(__import__('time').time() * 1000),
    }
    with open(DEBUG_LOG_PATH, 'a', encoding='utf-8') as log_file:
        log_file.write(json.dumps(payload) + '\n')
    # #endregion


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    _debug_log('H1', 'manage.py:27', 'manage.main entry', {
        'argv': sys.argv[:5],
        'python_executable': sys.executable,
        'cwd': os.getcwd(),
        'settings_module': os.environ.get('DJANGO_SETTINGS_MODULE'),
    })
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        _debug_log('H1', 'manage.py:31', 'django import failed', {'error': str(exc)})
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    _debug_log('H1', 'manage.py:38', 'django import succeeded')
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
