#!/usr/bin/env python3
"""
zoom_engagement_api.py

This Flask API exposes an endpoint for processing Zoom data and aggregating engagement metrics.
The frontend team can send a POST request with file uploads for:
  - Transcript (VTT)
  - Chat log (TXT)
  - Roster (TXT)
Optionally:
  - N-grams (CSV)
  - Lesson plan (TXT)

The API returns aggregated engagement metrics in JSON format.
"""

import os
import tempfile
import json
from flask import Flask, request, jsonify
from zoom_parser import process_zoom_data  # our parser module
from aggregate_engagement import load_roster, aggregate_engagement

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

def save_file(file_storage):
    """
    Save an uploaded file (Flask FileStorage) to a temporary path and return the path.
    """
    filename = file_storage.filename
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_storage.save(path)
    return path

@app.route("/api/process", methods=["POST"])
def process_data():
    # Get files from request (they are optional except transcript, chat, and roster).
    transcript_file = request.files.get("transcript")
    chat_file = request.files.get("chat")
    roster_file = request.files.get("roster")
    ngrams_file = request.files.get("ngrams")
    lesson_file = request.files.get("lesson")
    
    if not (transcript_file and chat_file and roster_file):
        return jsonify({"error": "Transcript, chat log, and roster files are required."}), 400

    transcript_path = save_file(transcript_file)
    chat_path = save_file(chat_file)
    roster_path = save_file(roster_file)
    ngrams_path = save_file(ngrams_file) if ngrams_file else None
    lesson_path = save_file(lesson_file) if lesson_file else None

    # Process Zoom data to generate a parsed CSV file.
    parsed_csv_path = os.path.join(app.config['UPLOAD_FOLDER'], "parsed_output.csv")
    process_zoom_data(transcript_path, chat_path, parsed_csv_path, ngrams_path, lesson_path)
    
    # Aggregate engagement metrics.
    roster_set = load_roster(roster_path)
    aggregate_data, categories = aggregate_engagement(parsed_csv_path, roster_set)
    
    # Return the aggregated data as JSON.
    return jsonify(aggregate_data)

if __name__ == "__main__":
    app.run(debug=True)
