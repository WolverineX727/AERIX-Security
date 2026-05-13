from flask import Flask, jsonify, render_template, request
import threading, time, random, os
from plyer import notification

app = Flask(__name__, static_folder='static', template_folder='templates')

# ================== SHARED STATE ==================
state = {
    'monitoring': False,
    'systemStats': {
        'cpuUsage': 0,
        'memoryUsage': 0,
        'networkActivity': 0,
        'processCount': 0,
        'blockedThreats': 0
    },
    'vertexAIStats': {
        'modelsRunning': 3,
        'predictionsToday': 0,
        'accuracy': 97.8
    },
    'geminiAnalysis': None,
    'activeProcesses': [],
    'networkConnections': [],
    'threats': [],
    'monitoredDomains': []
}

# ================== AI URL DETECTION (DEMO MODE) ==================
def ai_check_url(url):
    """
    Simulated AI + Threat Intelligence
    """
    url = url.lower()

    critical_keywords = [
        'malware', 'trojan', 'ransom', 'virus',
        'phishing', 'keylogger', 'c2', 'exploit',
        'payload', 'stealer', 'botnet'
    ]

    suspicious_keywords = [
        'free', 'login', 'verify', 'update',
        'secure', 'bonus', 'unknown', 'redirect'
    ]

    for k in critical_keywords:
        if k in url:
            return 'THREAT_DETECTED', 'MALWARE'

    for k in suspicious_keywords:
        if k in url:
            return 'SUSPICIOUS', 'LOW_REPUTATION_DOMAIN'

    return 'SAFE', None

# ================== THREAT LOGGER ==================
def add_threat(level, description):
    lvl = (level or '').lower()
    if lvl in ('high', 'critical', 'malicious'):
        severity = 'high'
        category = 'malicious'
    elif lvl in ('medium', 'suspicious'):
        severity = 'medium'
        category = 'suspicious'
    else:
        severity = 'low'
        category = 'info'

    threat = {
        'id': ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(8)),
        'severity': severity,
        'category': category,
        'description': description,
        'time': time.strftime('%H:%M:%S')
    }

    try:
        state['threats'].insert(0, threat)
        state['threats'] = state['threats'][:30]
    except Exception:
        # Keep the server stable if state mutation unexpectedly fails
        pass

    if severity == 'high':
        try:
            notification.notify(
                title="🚨 CRITICAL THREAT",
                message=description,
                timeout=10
            )
        except Exception:
            # Some environments (headless servers) raise errors when sending notifications;
            # swallow them so the API call doesn't return 500.
            pass
# ================== PROCESS SIMULATION ==================
def gen_process():
    legit = ['chrome.exe','explorer.exe','node.exe','python.exe','code.exe']
    bad = ['svch0st.exe','winlogin32.exe','sys_update.exe','payload.exe']

    is_bad = random.random() > 0.85
    name = random.choice(bad if is_bad else legit)

    return {
        'name': name,
        'pid': random.randint(1000, 50000),
        'cpu': round(random.random() * 40, 1),
        'isSuspicious': is_bad
    }

# ================== NETWORK SIMULATION ==================
def gen_connection():
    good = ['google.com', 'github.com', 'cloudflare.com']
    bad = ['c2-server.xyz', 'malware-drop.ru', 'phishing-login.net']

    is_bad = random.random() > 0.88
    domain = random.choice(bad if is_bad else good)

    return {
        'domain': domain,
        'ip': '.'.join(str(random.randint(1, 254)) for _ in range(4)),
        'port': random.choice([80, 443, 8080]),
        'status': 'blocked' if is_bad else 'allowed'
    }

# ================== BACKGROUND LOOP ==================
def simulation_loop():
    while True:
        if state['monitoring']:
            cpu = random.randint(10, 95)
            mem = random.randint(10, 95)

            state['systemStats']['cpuUsage'] = cpu
            state['systemStats']['memoryUsage'] = mem
            state['systemStats']['processCount'] = random.randint(120, 220)

            # Processes
            p = gen_process()
            if p['isSuspicious']:
                add_threat('medium', f"Suspicious process blocked: {p['name']}")
                state['systemStats']['blockedThreats'] += 1
            state['activeProcesses'] = [p]

            # Connections
            c = gen_connection()
            if c['status'] == 'blocked':
                add_threat('high', f"Malicious connection blocked: {c['domain']}")
                state['systemStats']['blockedThreats'] += 1
            state['networkConnections'] = [c]

            # Gemini AI message
            if random.random() > 0.7:
                state['geminiAnalysis'] = random.choice([
                    "Behavioral analysis complete – no anomalies",
                    "AI detected suspicious traffic pattern",
                    "Zero-day exploit behavior simulated",
                    "Threat intelligence updated successfully"
                ])

            state['vertexAIStats']['predictionsToday'] += random.randint(10, 40)

        time.sleep(2)

threading.Thread(target=simulation_loop, daemon=True).start()

# ================== ROUTES ==================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    return jsonify(state)

@app.route('/api/start', methods=['POST'])
def start():
    state['monitoring'] = True
    return jsonify({'ok': True})

@app.route('/api/stop', methods=['POST'])
def stop():
    state['monitoring'] = False
    return jsonify({'ok': True})

@app.route('/api/check-url', methods=['POST'])
def check_url():
    url = request.json.get('url', '').strip()
    if not url:
        return jsonify({'status': 'ERROR'})

    status, threat = ai_check_url(url)

    if status == 'THREAT_DETECTED':
        add_threat('high', f"AI blocked malicious website: {url}")
        state['systemStats']['blockedThreats'] += 1
        return jsonify({'status': status, 'threats': [{'threatType': threat}]})

    if status == 'SUSPICIOUS':
        add_threat('medium', f"AI flagged suspicious website: {url}")
        return jsonify({'status': status})

    return jsonify({'status': 'SAFE'})

@app.route('/api/add-domain', methods=['POST'])
def add_domain():
    url = request.json.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL required'}), 400

    status, threat = ai_check_url(url)

    if status == 'THREAT_DETECTED':
        add_threat('high', f"Blocked malicious domain: {url}")
        state['systemStats']['blockedThreats'] += 1
        return jsonify({'status': 'THREAT_DETECTED'})

    if url not in state['monitoredDomains']:
        state['monitoredDomains'].append(url)

    return jsonify({'status': status})

@app.route('/api/monitored-domains')
def monitored_domains():
    return jsonify({'domains': state['monitoredDomains']})

@app.route('/api/remove-domain', methods=['POST'])
def remove_domain():
    url = request.json.get('url')
    if url in state['monitoredDomains']:
        state['monitoredDomains'].remove(url)
    return jsonify({'ok': True})


if __name__ == '__main__':
    # ensure folders exist
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)
    app.run(host='0.0.0.0', port=5500, debug=True)