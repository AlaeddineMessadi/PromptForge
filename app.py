from flask import Flask, send_from_directory, jsonify, request, make_response
import os
import json
import socket

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Serve images with caching completely disabled
@app.route('/images/<path:filename>')
def serve_images(filename):
    file_path = os.path.join('images', filename)
    if not os.path.isfile(file_path):
        return jsonify({"error": "Image not found"}), 404

    # Serve the file with no caching
    response = make_response(send_from_directory('images', filename))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/pages', methods=['GET'])
def list_pages():
    files = [
        f for f in os.listdir('.') 
        if f.endswith('.json') and f not in ['prompts.json', 'package.json', 'tsconfig.json']
    ]
    return jsonify(files)

@app.route('/api/pages/<path:filename>', methods=['GET'])
def get_page(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 500

@app.route('/api/pages', methods=['POST'])
def save_page():
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    
    if not filename or content is None:
        return jsonify({"error": "Missing filename or content"}), 400
    
    if not filename.endswith('.json'):
        filename += '.json'
        
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({"error": "Invalid filename"}), 400

    try:
        with open(filename, 'w') as f:
            json.dump(content, f, indent=2)
        return jsonify({"message": "Saved successfully", "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------
# Image upload with New Prompt safety
# ----------------------------
@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    file = request.files.get('image')
    prompt_tag = request.form.get('prompt_tag')  # Required: prompt card title
    
    if not file or not prompt_tag:
        return jsonify({"error": "Missing file or prompt_tag"}), 400

    os.makedirs('images', exist_ok=True)

    # Convert spaces in prompt_tag to underscores
    safe_name = prompt_tag.replace(' ', '_') + '.png'
    
    # Safety: prevent overwriting New_Prompt.png
    if prompt_tag.strip() == "New Prompt":
        return jsonify({"error": "Please edit the card name before adding an image!"}), 400

    file_path = os.path.join('images', safe_name)
    
    # Save the file
    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"error": f"Failed to save image: {str(e)}"}), 500

    return jsonify({"message": "Image saved", "filename": safe_name})

def _find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """Return an open port, scanning sequentially from start_port."""
    port = start_port
    for _ in range(max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                port += 1
    raise RuntimeError(f"No available port found starting at {start_port}")


if __name__ == '__main__':
    env_port = int(os.environ.get('PORT', 5000))
    chosen_port = _find_available_port(env_port)
    if chosen_port != env_port:
        print(f"Port {env_port} in use; falling back to {chosen_port}")

    app.run(
        host='0.0.0.0',
        port=chosen_port,
        debug=os.environ.get('FLASK_DEBUG') == '1'
    )
