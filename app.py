from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger('app')

app = Flask(__name__)

# Path to the log file
LOG_FILE = "device_logs.json"

# Device state storage
DEVICE_STATE = {
    "light": "off",
    "fan": "off",
    "music": "stopped",
    "front_door": "locked",
    "ac_temp": 22
}

# Load device logs for UI
def load_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as file:
                logs = json.load(file)
            return logs
        return []
    except Exception as e:
        logger.error(f"Error loading logs: {str(e)}")
        return []

# UI for controlling devices
@app.route("/")
def home():
    return render_template("index.html")

# Endpoint to get device logs
@app.route("/logs", methods=["GET"])
def get_logs():
    try:
        logs = load_logs()
        return jsonify({"logs": logs, "devices": DEVICE_STATE})
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Dynamic responses for commands
def get_dynamic_response(command):
    responses = {
        "turn_on_light": "💡 Lights turned ON. Let there be light!",
        "turn_off_light": "🌑 Lights turned OFF. Going dark...",
        "turn_on_fan": "🌀 Fan is spinning! Cooling things down...",
        "turn_off_fan": "❄️ Fan turned OFF. Calm and quiet now.",
        "play_music": "🎵 Music started! Let's vibe to some beats!",
        "stop_music": "🔇 Music stopped. Silence restored.",
        "lock_front_door": "🔒 Front door locked. Home secured.",
        "unlock_front_door": "🔓 Front door unlocked. Be careful!",
        "activate_movie_mode": "🎬 Movie mode activated! Grab some popcorn!",
        "activate_night_mode": "🌙 Night mode activated. Sleep tight!",
        "activate_away_mode": "🏡 Away mode activated. Be safe!",
        "set_ac_temperature": "🌡️ Temperature set successfully! Adjusting climate control..."
    }
    return responses.get(command, "✅ Command executed successfully!")

# Update device state based on command
def update_device_state(command, params=None):
    if command == "turn_on_light":
        DEVICE_STATE["light"] = "on"
    elif command == "turn_off_light":
        DEVICE_STATE["light"] = "off"
    elif command == "turn_on_fan":
        DEVICE_STATE["fan"] = "on"
    elif command == "turn_off_fan":
        DEVICE_STATE["fan"] = "off"
    elif command == "play_music":
        DEVICE_STATE["music"] = "playing"
    elif command == "stop_music":
        DEVICE_STATE["music"] = "stopped"
    elif command == "lock_front_door":
        DEVICE_STATE["front_door"] = "locked"
    elif command == "unlock_front_door":
        DEVICE_STATE["front_door"] = "unlocked"
    elif command == "set_ac_temperature" and params and "temperature" in params:
        DEVICE_STATE["ac_temp"] = params["temperature"]
    elif command == "activate_movie_mode":
        DEVICE_STATE.update({"light": "off", "fan": "on", "music": "playing"})
    elif command == "activate_night_mode":
        DEVICE_STATE.update({"light": "off", "fan": "off", "front_door": "locked"})
    elif command == "activate_away_mode":
        DEVICE_STATE.update({"light": "off", "fan": "off", "front_door": "locked", "music": "stopped"})


# Endpoint to control devices
@app.route("/command", methods=["POST"])
def handle_command():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON data."}), 400
            
        command = data.get("command")
        params = data.get("params", {})
        
        if not command:
            return jsonify({"status": "error", "message": "No command received."}), 400
        
        # Update device state
        update_device_state(command, params)
        
        # Get a fun, interactive response
        response_text = get_dynamic_response(command)
        if command == "set_ac_temperature" and "temperature" in params:
            temp = params["temperature"]
            response_text = f"🌡️ Temperature set to {temp}°C. Adjusting climate control..."

        # Log the command with timestamp
        log_entry = {
            "command": command,
            "params": params,
            "status": "success",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save log to file
        logs = load_logs()
        logs.append(log_entry)
        try:
            with open(LOG_FILE, "w") as file:
                json.dump(logs, file, indent=4)
        except Exception as e:
            logger.error(f"Error saving log: {str(e)}")
            return jsonify({"status": "warning", "message": response_text, 
                           "log_error": "Command executed but logging failed"}), 200
        
        return jsonify({"status": "success", "message": response_text})
    
    except Exception as e:
        logger.error(f"Error in command handler: {str(e)}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

# Health check endpoint with device states
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "devices": DEVICE_STATE
    })

@app.route("/command/text", methods=["POST"])
def handle_text_command():
    try:
        data = request.get_json()
        command = data.get("command", "").lower()
        
        # Import functionality from voice_assistant
        from voice_assistant import predict_intent, extract_temperature
        
        intent = predict_intent(command)
        
        if intent == "set_ac_temperature":
            temp = extract_temperature(command)
            if temp:
                params = {"temperature": temp}
                update_device_state(intent, params)
                response_text = f"🌡️ Temperature set to {temp}°C. Adjusting climate control..."
            else:
                return jsonify({"status": "error", "message": "Please specify a valid temperature (16-30°C)"}), 400
        else:
            update_device_state(intent)
            response_text = get_dynamic_response(intent)
            
        return jsonify({"status": "success", "message": response_text})
    except Exception as e:
        logger.error(f"Error in text command handler: {str(e)}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')