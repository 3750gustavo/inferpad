from flask import Flask, render_template, request, Response
import json
import requests
import sseclient
from threading import Event

app = Flask(__name__)

API_URL = "https://api.totalgpt.ai/completions"
API_KEY = "sk-"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    prompt = request.json['prompt']
    cancel_event = Event()

    def generate_text():
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        data = {
            "model": "L3-70B-Euryale-v2.1",
            "prompt": prompt,
            "stream": True,
            "max_tokens": 120,
            "temperature": 1.17,
            "top_p": 0.95,
            "min_p": 0.1,
            "seed": -1,
            "top_k": -1,
            "presence_penalty": 0.0,
        }

        try:
            with requests.post(API_URL, json=data, headers=headers, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if cancel_event.is_set():
                        yield f"data: {json.dumps({'done': True})}\n\n"
                        return
                    if line:
                        try:
                            event_data = json.loads(line.decode('utf-8').split('data: ', 1)[1])
                            if 'choices' in event_data and len(event_data['choices']) > 0:
                                chunk = event_data['choices'][0].get('text', '')
                                if chunk:
                                    yield f"data: {json.dumps({'text': chunk})}\n\n"
                            elif 'error' in event_data:
                                yield f"data: {json.dumps({'error': event_data['error']})}\n\n"
                        except (json.JSONDecodeError, KeyError, IndexError) as e:
                            continue  # Skip invalid lines
                yield f"data: {json.dumps({'done': True})}\n\n"
        except requests.exceptions.RequestException as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate_text(), content_type='text/event-stream')

@app.route('/cancel', methods=['POST'])
def cancel():
    # In a real application, you'd need to manage multiple requests and their cancel events
    # For simplicity, we're not implementing this here
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)