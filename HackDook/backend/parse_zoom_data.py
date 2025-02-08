#!/usr/bin/env python3
"""
zoom_parser.py

This module provides functions to parse Zoom VTT transcript files and chat logs,
combine their data into a unified timeline, perform word stemming using NLTK's
PorterStemmer, and write the output to a CSV file.

Usage as a command-line tool:
    python zoom_parser.py --vtt <transcript.vtt> --chat <chat_log.txt> --output <output.csv>

Usage as an importable module:
    import zoom_parser
    transcript = zoom_parser.parse_vtt("transcript.vtt")
    chat_log = zoom_parser.parse_chat_log("chat_log.txt")
    combined = zoom_parser.combine_data(transcript, chat_log)
    # Optionally write to CSV:
    zoom_parser.write_csv(combined, "output.csv")
"""
import re
import csv
import argparse
from nltk.stem.porter import PorterStemmer

def timestamp_to_seconds(timestamp_str):
    """
    Convert a timestamp string (HH:MM:SS or HH:MM:SS.mmm) to seconds (as a float).

    :param timestamp_str: Timestamp as a string.
    :return: Time in seconds (float).
    """
    parts = timestamp_str.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}")
    hours, minutes = int(parts[0]), int(parts[1])
    sec_parts = parts[2].split(".")
    seconds = int(sec_parts[0])
    milliseconds = int(sec_parts[1]) if len(sec_parts) == 2 else 0
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

def parse_vtt(filename):
    """
    Parse a VTT file (WebVTT format) and return a list of transcript entries.

    Each entry is a dictionary with the following keys:
      - type: "transcript"
      - block_index: Block index (as a string; may be empty)
      - timestamp: Start time (string)
      - time: Start time in seconds (float)
      - end: End timestamp (string)
      - speaker: Speaker name (if present)
      - text: Spoken text (with speaker name removed)

    :param filename: Path to the VTT file.
    :return: List of transcript entries (dictionaries).
    """
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # Split content into blocks separated by blank lines.
    blocks = content.strip().split("\n\n")

    # Remove header if present.
    if blocks and blocks[0].strip().startswith("WEBVTT"):
        blocks = blocks[1:]

    transcript = []
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue

        # If the first line is a number, use it as the block index.
        if re.match(r"^\d+$", lines[0].strip()):
            block_index = lines[0].strip()
            timestamp_line = lines[1].strip() if len(lines) > 1 else ""
            text_lines = lines[2:] if len(lines) > 2 else []
        else:
            block_index = ""
            timestamp_line = lines[0].strip()
            text_lines = lines[1:] if len(lines) > 1 else []

        # Expected timestamp format: "00:00:03.090 --> 00:00:05.760"
        start, end = None, None
        timestamp_parts = timestamp_line.split("-->")
        if len(timestamp_parts) == 2:
            start = timestamp_parts[0].strip()
            end = timestamp_parts[1].strip()

        text = " ".join(text_lines).strip()

        # Extract speaker if the text begins with "Speaker:".
        speaker = ""
        message = text
        if ":" in text:
            possible_speaker, possible_message = text.split(":", 1)
            speaker = possible_speaker.strip()
            message = possible_message.strip()

        transcript.append({
            "type": "transcript",
            "block_index": block_index,
            "timestamp": start,
            "time": timestamp_to_seconds(start) if start else None,
            "end": end,
            "speaker": speaker,
            "text": message
        })
    return transcript

def parse_chat_log(filename):
    """
    Parse a chat log file where each line is formatted as:
        timestamp[TAB]Speaker Name:[TAB]Message text

    Returns a list of chat entries. Each entry is a dictionary with the keys:
      - type: "chat"
      - timestamp: Chat time (string)
      - time: Chat time in seconds (float)
      - speaker: Speaker name (colon removed)
      - message: Chat message text

    :param filename: Path to the chat log file.
    :return: List of chat entries (dictionaries).
    """
    chat_entries = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 3:
                continue  # Skip malformed lines

            timestamp = parts[0].strip()
            speaker = parts[1].strip()
            if speaker.endswith(":"):
                speaker = speaker[:-1].strip()
            message = parts[2].strip()

            chat_entries.append({
                "type": "chat",
                "timestamp": timestamp,
                "time": timestamp_to_seconds(timestamp),
                "speaker": speaker,
                "message": message
            })
    return chat_entries

def combine_data(transcript, chat_entries):
    """
    Combine transcript and chat log entries into one list, sorted by time.

    :param transcript: List of transcript entries.
    :param chat_entries: List of chat log entries.
    :return: Combined and sorted list of entries.
    """
    combined = transcript + chat_entries
    combined.sort(key=lambda x: x.get("time", 0))
    return combined

def stem_text(text, stemmer=None):
    """
    Stem the words in a given text using NLTK's PorterStemmer.

    :param text: Input text to stem.
    :param stemmer: An instance of a stemmer; if None, a PorterStemmer is used.
    :return: A string with stemmed words.
    """
    if stemmer is None:
        stemmer = PorterStemmer()
    words = re.findall(r'\w+', text.lower())
    stemmed_words = [stemmer.stem(word) for word in words]
    return " ".join(stemmed_words)

def write_csv(data, output_filename):
    """
    Write the combined data to a CSV file.

    Each entry in data should be a dictionary. The CSV will include the following fields:
        type, block_index, timestamp, time, end, speaker, message, stemmed_message

    :param data: List of dictionaries representing the combined entries.
    :param output_filename: Path to the output CSV file.
    """
    fieldnames = ["type", "block_index", "timestamp", "time", "end", "speaker", "message", "stemmed_message"]
    with open(output_filename, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in data:
            # For transcript entries, use the 'text' key; for chat entries, use 'message'
            message = entry.get("text", "") if entry.get("type") == "transcript" else entry.get("message", "")
            stemmed_message = stem_text(message)
            row = {
                "type": entry.get("type", ""),
                "block_index": entry.get("block_index", ""),
                "timestamp": entry.get("timestamp", ""),
                "time": entry.get("time", ""),
                "end": entry.get("end", ""),
                "speaker": entry.get("speaker", ""),
                "message": message,
                "stemmed_message": stemmed_message
            }
            writer.writerow(row)

def process_zoom_data(vtt_filename, chat_filename, output_csv):
    """
    Process Zoom data by parsing the VTT transcript and chat log, combining the entries,
    and writing the result to a CSV file.

    :param vtt_filename: Path to the VTT transcript file.
    :param chat_filename: Path to the chat log file.
    :param output_csv: Path to the output CSV file.
    :return: Combined list of entries.
    """
    transcript = parse_vtt(vtt_filename)
    chat_log = parse_chat_log(chat_filename)
    combined = combine_data(transcript, chat_log)
    write_csv(combined, output_csv)
    return combined

if __name__ == "__main__":
    # CLI for standalone usage.
    parser = argparse.ArgumentParser(
        description="Parse Zoom VTT transcript and chat log files, combine them, stem words, and output to CSV."
    )
    parser.add_argument("--vtt", required=True, help="Path to the VTT transcript file")
    parser.add_argument("--chat", required=True, help="Path to the chat log file")
    parser.add_argument("--output", required=True, help="Path to the output CSV file")
    args = parser.parse_args()

    process_zoom_data(args.vtt, args.chat, args.output)
    print(f"Combined CSV output written to {args.output}")
