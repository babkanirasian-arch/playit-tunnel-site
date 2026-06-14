import os
import re
import subprocess
import threading
from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)
playit_process = None
output_log = []
claim_url = None

def run_playit():
    global playit_process, claim_url, output_log
    
    # Файл теперь всегда скачивается заранее в системную папку /opt/render/project/src/playit
    executable = "./playit"

    if not os.path.exists(executable):
        output_log.append("❌ КРИТИЧЕСКАЯ ОШИБКА: Файл playit не найден на сервере!")
        return

    try:
        output_log.append("Запуск агента...")
        playit_process = subprocess.Popen([executable], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(playit_process.stdout.readline, ''):
            clean_line = line.strip()
            output_log.append(clean_line)
            if "playit.gg/claim/" in clean_line:
                match = re.search(r'(https://playit\.gg/claim/\S+)', clean_line)
                if match: claim_url = match.group(1)
    except Exception as e:
        output_log.append(f"Ошибка запуска: {str(e)}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><title>Playit Tunnel</title>
    <style>body{background:#111;color:#fff;font-family:sans-serif;text-align:center;padding:50px;}</style>
    <meta http-equiv="refresh" content="3">
</head>
<body>
    <h2>Управление Туннелем</h2>
    {% if not is_running %}
        <a href="/start"><button style="padding:15px 30px;background:green;color:white;font-weight:bold;border:none;border-radius:5px;cursor:pointer;">START TUNNEL</button></a>
    {% else %}
        <p style="color:green;">Туннель запущен в фоне облака!</p>
        <a href="/stop"><button style="padding:10px 20px;background:red;color:white;border:none;border-radius:5px;cursor:pointer;">STOP</button></a>
        {% if claim_url %}<p><a href="{{ claim_url }}" target="_blank" style="color:#00ffff;font-size:18px;">👉 НАЖМИ СЮДА ДЛЯ АКТИВАЦИИ ТУННЕЛЯ 👈</a></p>{% endif %}
    {% endif %}
    <div style="background:#000;color:#0f0;text-align:left;padding:15px;margin-top:30px;height:200px;overflow-y:auto;font-family:monospace;">
        {% for line in logs[-10:] %}{{ line }}<br>{% endfor %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    is_running = playit_process is not None and playit_process.poll() is None
    return render_template_string(HTML_TEMPLATE, is_running=is_running, claim_url=claim_url, logs=output_log)

@app.route('/start')
def start():
    global playit_process, claim_url, output_log
    if not (playit_process and playit_process.poll() is None):
        output_log = ["Инициализация..."]
        claim_url = None
        threading.Thread(target=run_playit, daemon=True).start()
    return redirect(url_for('index'))

@app.route('/stop')
def stop():
    global playit_process
    if playit_process: playit_process.terminate()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
