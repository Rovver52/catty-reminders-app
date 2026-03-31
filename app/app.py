from flask import Flask
import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return f'''
    <h1>DevOps Lab 1 - Webhook Demo</h1>
    <p>Student: abdulkhanov</p>
    <p>Last deploy: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p>Version: 1.0</p>
    '''

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8181)
