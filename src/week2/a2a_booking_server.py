"""
src/week2/a2a_booking_server.py
================================
Week 2, Lab 5: A2A Venue Booking Agent — Flask app implementing the A2A protocol.

GET  /.well-known/agent.json  → Agent Card
POST /a2a/tasks/send          → Submit task (returns 202 with task ID)
GET  /a2a/tasks/<task_id>     → Poll state (submitted → working → completed/failed)
"""

import json
import threading
import time
import uuid
from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory task store
_tasks = {}


AGENT_CARD = {
    "name": "Edinburgh Venue Booking Agent",
    "description": "Books Edinburgh venues for events. Checks capacity and dietary requirements.",
    "version": "1.0.0",
    "capabilities": ["venue_booking", "capacity_check", "vegan_menu_check"],
    "protocol": "a2a/v1",
    "endpoints": {
        "task_send": "/a2a/tasks/send",
        "task_status": "/a2a/tasks/{task_id}",
    },
}


def process_booking(task_id: str, task_text: str) -> None:
    """
    Background thread: processes a booking request.

    Checks for "160" and "vegan" in the task text to determine success.

    Args:
        task_id: Unique task identifier.
        task_text: The task description text.
    """
    _tasks[task_id]["state"] = "working"
    time.sleep(1)  # Simulate processing time

    text_lower = task_text.lower()
    has_capacity = "160" in task_text or "one hundred sixty" in text_lower
    has_vegan = "vegan" in text_lower

    if has_capacity and has_vegan:
        _tasks[task_id]["state"] = "completed"
        _tasks[task_id]["artifact"] = {
            "type": "text",
            "name": "booking_confirmation",
            "parts": [
                {
                    "text": (
                        "Booking confirmed at The Albanach, 2 Hunter Square, Edinburgh. "
                        "Capacity: 180 (requested 160). Vegan menu available. "
                        "Status: Available. Confirmation reference: EDI-2025-0042."
                    )
                }
            ],
        }
    elif not has_capacity:
        _tasks[task_id]["state"] = "failed"
        _tasks[task_id]["error"] = "Could not determine required capacity from task description."
    elif not has_vegan:
        _tasks[task_id]["state"] = "completed"
        _tasks[task_id]["artifact"] = {
            "type": "text",
            "name": "booking_confirmation",
            "parts": [
                {
                    "text": (
                        "Booking confirmed at The Guilford Arms, 1 West Register Street, Edinburgh. "
                        "Capacity: 200. Note: Vegan options not confirmed. "
                        "Confirmation reference: EDI-2025-0043."
                    )
                }
            ],
        }


@app.route("/.well-known/agent.json", methods=["GET"])
def agent_card():
    """Return the A2A Agent Card."""
    return jsonify(AGENT_CARD)


@app.route("/a2a/tasks/send", methods=["POST"])
def submit_task():
    """Submit a new booking task. Returns 202 with task ID."""
    data = request.get_json(force=True)
    task_text = data.get("text", "")

    if not task_text:
        return jsonify({"error": "Missing 'text' field in request body"}), 400

    task_id = str(uuid.uuid4())
    _tasks[task_id] = {
        "id": task_id,
        "state": "submitted",
        "text": task_text,
        "artifact": None,
        "error": None,
    }

    # Process in background
    thread = threading.Thread(target=process_booking, args=(task_id, task_text))
    thread.daemon = True
    thread.start()

    return jsonify({"task_id": task_id, "state": "submitted"}), 202


@app.route("/a2a/tasks/<task_id>", methods=["GET"])
def get_task(task_id: str):
    """Poll task state by ID."""
    task = _tasks.get(task_id)
    if not task:
        return jsonify({"error": f"Task not found: {task_id}"}), 404

    response = {
        "id": task["id"],
        "state": task["state"],
    }
    if task["artifact"]:
        response["artifact"] = task["artifact"]
    if task["error"]:
        response["error"] = task["error"]

    return jsonify(response)


if __name__ == "__main__":
    print("A2A Venue Booking Agent | http://localhost:8080")
    print("Agent Card: http://localhost:8080/.well-known/agent.json")
    app.run(host="0.0.0.0", port=8080, debug=False)
