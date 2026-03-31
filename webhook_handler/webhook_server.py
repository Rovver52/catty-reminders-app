from flask import Flask, request, jsonify
import subprocess
import os
import hashlib
import hmac
import requests

app = Flask(__name__)

# Конфигурация
REPO_PATH = os.path.expanduser('~/webhook-deploy/app')
GITHUB_SECRET = ''  # Можно установить секрет для проверки
GITHUB_TOKEN = ''  # Ваш GitHub token (опционально)

def verify_signature(payload_body, secret_token, signature_header):
    """Проверка подписи GitHub (опционально)"""
    if not secret_token:
        return True
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)

def deploy_app():
    """Функция развертывания приложения"""
    try:
        result = {
            'success': True,
            'message': '',
            'steps': []
        }
        
        # Шаг 1: Git pull
        result['steps'].append("Updating code from repository...")
        try:
            os.chdir(REPO_PATH)
            git_result = subprocess.run(['git', 'pull'], capture_output=True, text=True, timeout=30)
            if git_result.returncode == 0:
                result['steps'].append("✓ Code updated successfully")
            else:
                result['steps'].append(f"✗ Git pull failed: {git_result.stderr}")
        except Exception as e:
            result['steps'].append(f"✗ Git error: {str(e)}")
        
        # Шаг 2: Установка зависимостей
        result['steps'].append("Installing dependencies...")
        try:
            pip_result = subprocess.run(
                ['pip3', 'install', '-r', 'requirements.txt'],
                capture_output=True, text=True, timeout=60
            )
            if pip_result.returncode == 0:
                result['steps'].append("✓ Dependencies installed")
            else:
                result['steps'].append(f"✗ Pip install failed: {pip_result.stderr}")
        except Exception as e:
            result['steps'].append(f"✗ Pip error: {str(e)}")
        
        # Шаг 3: Перезапуск приложения
        result['steps'].append("Restarting application...")
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'myapp'], timeout=10)
            result['steps'].append("✓ Application restarted")
        except Exception as e:
            result['steps'].append(f"✗ Restart failed: {str(e)}")
        
        result['message'] = "Deployment completed"
        return result
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Deployment failed: {str(e)}",
            'steps': []
        }

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return 'Webhook server is running', 200
    
    if request.method == 'POST':
        # Получаем заголовок события
        event = request.headers.get('X-GitHub-Event')
        
        # Проверяем подпись (опционально)
        signature_header = request.headers.get('X-Hub-Signature-256', '')
        if not verify_signature(request.data, GITHUB_SECRET, signature_header):
            return 'Invalid signature', 401
        
        # Обрабатываем push события
        if event == 'push':
            data = request.json
            branch = data.get('ref', '').replace('refs/heads/', '')
            
            print(f"Received push event for branch: {branch}")
            
            # Запускаем развертывание
            deploy_result = deploy_app()
            
            # Отправляем статус в GitHub (опционально)
            # send_status_to_github(data, deploy_result)
            
            if deploy_result['success']:
                return jsonify(deploy_result), 200
            else:
                return jsonify(deploy_result), 500
        
        return 'Event ignored', 200

@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
