from flask import Flask, render_template, request, Response, jsonify
import json
import requests
import sseclient
from threading import Event
import asyncio
from generate_voice import generate_voice

app = Flask(__name__)

# Server-side state
last_prompt = ""
last_generated_text = ""
full_text = ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    global last_prompt, last_generated_text, full_text
    data = request.json
    last_prompt = data['prompt']
    api_url = "https://api.totalgpt.ai/completions"
    api_key = "Bearer sk-"
    full_text = data['fullText']
    last_generated_text = ""
    cancel_event = Event()

    def generate_text():
        global last_generated_text, full_text
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "model": "L3-70B-Euryale-v2.1",
            "prompt": last_prompt,
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
            with requests.post(api_url, json=data, headers=headers, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if cancel_event.is_set():
                        yield f"data: {json.dumps({'done': True})}\n\n"
                        asyncio.run(generate_voice(last_generated_text))
                        return
                    if line:
                        try:
                            event_data = json.loads(line.decode('utf-8').split('data: ', 1)[1])
                            if 'choices' in event_data and len(event_data['choices']) > 0:
                                chunk = event_data['choices'][0].get('text', '')
                                if chunk:
                                    last_generated_text += chunk
                                    full_text += chunk
                                    yield f"data: {json.dumps({'text': chunk})}\n\n"
                            elif 'error' in event_data:
                                yield f"data: {json.dumps({'error': event_data['error']})}\n\n"
                        except (json.JSONDecodeError, KeyError, IndexError) as e:
                            continue
                yield f"data: {json.dumps({'done': True})}\n\n"
                asyncio.run(generate_voice(last_generated_text))
        except requests.exceptions.RequestException as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate_text(), content_type='text/event-stream')

@app.route('/cancel', methods=['POST'])
def cancel():
    # In a real application, you'd need to manage multiple requests and their cancel events
    return '', 204

@app.route('/undo', methods=['POST'])
def undo():
    global full_text, last_generated_text
    full_text = full_text[:-len(last_generated_text)]
    last_generated_text = ""
    return jsonify({'text': full_text})

@app.route('/retry', methods=['POST'])
def retry():
    global last_prompt, full_text, last_generated_text
    full_text = full_text[:-len(last_generated_text)]
    last_generated_text = ""
    return jsonify({'prompt': last_prompt, 'fullText': full_text})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)