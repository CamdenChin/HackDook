#!/usr/bin/env python3
import re
import csv
import argparse
from nltk.stem.porter import PorterStemmer

def timestamp_to_seconds(timestamp_str):
    """
    Convert a timestamp string (HH:MM:SS or HH:MM:SS.mmm) to seconds (as a float).
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
    
    Each entry is a dictionary with:
      - type: "transcript"
      - block_index: (if available) the block index as a string
      - timestamp: the start time (string)
      - time: the start time in seconds (float)
      - end: the end timestamp (string)
      - speaker: the speaker name (if found)
      - text: the spoken text (with the speaker name removed)
    """
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    # Split the file into blocks separated by blank lines.
    blocks = content.strip().split("\n\n")

    # Remove the header (usually "WEBVTT") if present.
    if blocks and blocks[0].strip().startswith("WEBVTT"):
        blocks = blocks[1:]

    transcript = []

    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue

        # Check if the first line is a block index (a number)
        if re.match(r"^\d+$", lines[0].strip()):
            block_index = lines[0].strip()
            timestamp_line = lines[1].strip() if len(lines) > 1 else ""
            text_lines = lines[2:] if len(lines) > 2 else []
        else:
            block_index = ""
            timestamp_line = lines[0].strip()
            text_lines = lines[1:] if len(lines) > 1 else []

        # Parse the timestamp line; expected format: "00:00:03.090 --> 00:00:05.760"
        start, end = None, None
        timestamp_parts = timestamp_line.split("-->")
        if len(timestamp_parts) == 2:
            start = timestamp_parts[0].strip()
            end = timestamp_parts[1].strip()

        # Combine text lines into a single string.
        text = " ".join(text_lines).strip()

        # Extract the speaker if the text begins with "Speaker Name:".
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
      
    Returns a list of chat entries, each as a dictionary with:
      - type: "chat"
      - timestamp: the chat time (string)
      - time: the chat time in seconds (float)
      - speaker: the speaker name (colon removed)
      - message: the chat message text
    """
    chat_entries = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Split each line by tab
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
    Combine transcript and chat log entries into one list sorted by time.
    """
    combined = transcript + chat_entries
    combined.sort(key=lambda x: x.get("time", 0))
    return combined

def stem_text(text, stemmer):
    """
    Stem the words in a given text using the provided stemmer.
    This function extracts alphanumeric words, stems each, and rejoins them.
    """
    # Extract words using regex (lowercase them)
    words = re.findall(r'\w+', text.lower())
    stemmed_words = [stemmer.stem(word) for word in words]
    return " ".join(stemmed_words)

def main():
    parser = argparse.ArgumentParser(
        description="Parse Zoom VTT transcript and chat log files, combine them, stem words, and output to CSV."
    )
    parser.add_argument("--vtt", required=True, help="Path to the VTT transcript file")
    parser.add_argument("--chat", required=True, help="Path to the chat log file")
    parser.add_argument("--output", required=True, help="Path to the output CSV file")
    args = parser.parse_args()

    transcript = parse_vtt(args.vtt)
    chat_log = parse_chat_log(args.chat)
    combined_data = combine_data(transcript, chat_log)

    # Initialize the stemmer
    stemmer = PorterStemmer()

    # Define CSV field names.
    fieldnames = ["type", "block_index", "timestamp", "time", "end", "speaker", "message", "stemmed_message"]

    # Open the CSV file for writing.
    with open(args.output, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in combined_data:
            # For transcript entries, the message is in 'text'; for chat entries, in 'message'
            if entry["type"] == "transcript":
                message = entry.get("text", "")
            else:
                message = entry.get("message", "")
            # Compute the stemmed version of the message.
            stemmed_message = stem_text(message, stemmer)
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

    print(f"Combined CSV output written to {args.output}")

if __name__ == "__main__":
    main()
