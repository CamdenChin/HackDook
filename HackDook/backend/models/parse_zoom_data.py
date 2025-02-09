#!/usr/bin/env python3
"""
zoom_parser.py

This module provides functions to:
  - Parse Zoom VTT transcript files and chat logs.
  - Combine and stem the parsed messages.
  - Load a CSV file of n‑grams and their associated categories (with word stemming for consistency).
  - Categorize each message by matching stemmed n‑grams from the external file.
  - Quantify the relevancy of each message to a lesson plan using semantic similarity with sentence embeddings.
  - Write the combined data to a CSV file (with optional assigned category and lesson relevancy score).

Usage as a command‐line tool:
  python zoom_parser.py --vtt transcript.vtt --chat chat_log.txt --output output.csv --ngrams ngrams.csv [--lesson lesson_plan.txt]

Usage as an importable module:
  import zoom_parser
  transcript = zoom_parser.parse_vtt("transcript.vtt")
  chat_log = zoom_parser.parse_chat_log("chat_log.txt")
  combined = zoom_parser.combine_data(transcript, chat_log)
  ngrams = zoom_parser.load_ngrams("ngrams.csv")  # optional
  # Optionally extract lesson keywords from a lesson plan string using model_classifier:
  # from model_classifier import extract_keywords
  # lesson_keywords = extract_keywords(lesson_plan_string)
  for entry in combined:
      msg = entry.get("text", "") if entry.get("type") == "transcript" else entry.get("message", "")
      entry["assigned_category"] = zoom_parser.categorize_message(msg, ngrams)
      entry["lesson_relevancy"] = zoom_parser.compute_semantic_similarity(msg, lesson_embedding, model)
  zoom_parser.write_csv(combined, "output.csv", ngrams, lesson_embedding, model)
"""

import re
import csv
import argparse
from nltk.stem.porter import PorterStemmer

# For semantic similarity we use SentenceTransformer.
from sentence_transformers import SentenceTransformer, util

# Try to import the extract_keywords function from model_classifier.
try:
    from model_classifier import extract_keywords
except ImportError:
    extract_keywords = None


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
    
    Each entry is a dictionary with the following keys:
      - type: "transcript"
      - block_index: Block index (string; may be empty)
      - timestamp: Start time (string)
      - time: Start time in seconds (float)
      - end: End timestamp (string)
      - speaker: Speaker name (if present)
      - text: Spoken text (with speaker name removed)
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

        # Extract speaker if the text contains a colon.
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
      
    Returns a list of chat entries (dictionaries) with the keys:
      - type: "chat"
      - timestamp: Chat time (string)
      - time: Chat time in seconds (float)
      - speaker: Speaker name (colon removed)
      - message: Chat message text
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
    """
    combined = transcript + chat_entries
    combined.sort(key=lambda x: x.get("time", 0))
    return combined


def stem_text(text, stemmer=None):
    """
    Stem the words in the provided text using NLTK's PorterStemmer.
    
    :param text: Input text.
    :param stemmer: An instance of a stemmer (if None, a PorterStemmer is used).
    :return: String with stemmed words.
    """
    if stemmer is None:
        stemmer = PorterStemmer()
    words = re.findall(r'\w+', text.lower())
    stemmed_words = [stemmer.stem(word) for word in words]
    return " ".join(stemmed_words)


def load_ngrams(ngrams_filename):
    """
    Load n‑grams from a CSV file. Each row in the CSV should have four columns:
      - id, ngram phrase, ngram type (e.g., unigram, bigram, trigram), category
      
    For consistency, each n‑gram phrase is stemmed using the same PorterStemmer as the messages.
    Precompiles a regex pattern for each stemmed n‑gram (with word boundaries) and returns a list of dictionaries.
    """
    ngrams = []
    stemmer = PorterStemmer()
    with open(ngrams_filename, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4:
                continue
            # Unpack columns (ignoring the id)
            _, phrase, ngram_type, category = row[0], row[1], row[2], row[3]
            # Stem the phrase for consistency.
            stemmed_phrase = stem_text(phrase, stemmer)
            # Compile a regex pattern to match the stemmed n‑gram as a whole word/phrase.
            pattern = re.compile(r'\b' + re.escape(stemmed_phrase) + r'\b')
            ngrams.append({
                "phrase": phrase,
                "ngram_type": ngram_type,
                "category": category,
                "stemmed_phrase": stemmed_phrase,
                "pattern": pattern
            })
    return ngrams


def categorize_message(message, ngrams_list):
    """
    Categorize a message by checking for the occurrence of any stemmed n‑grams.
    
    The message is first stemmed for consistency. For each n‑gram that matches, we count its category.
    The function returns the category (or categories, comma-separated if there is a tie) with the highest match count.
    If no n‑grams match, "uncategorized" is returned.
    
    :param message: The message text to categorize.
    :param ngrams_list: A list of n‑gram dictionaries (from load_ngrams).
    :return: A string representing the assigned category (or categories).
    """
    stemmer = PorterStemmer()
    message_stemmed = stem_text(message, stemmer)
    counts = {}
    for ngram in ngrams_list:
        if ngram["pattern"].search(message_stemmed):
            cat = ngram["category"]
            counts[cat] = counts.get(cat, 0) + 1
    if not counts:
        return "uncategorized"
    max_count = max(counts.values())
    matched_categories = [cat for cat, cnt in counts.items() if cnt == max_count]
    return ", ".join(matched_categories)


def compute_semantic_similarity(message, lesson_embedding, model):
    """
    Compute the semantic similarity (cosine similarity) between a message and the lesson plan.
    
    :param message: The message text.
    :param lesson_embedding: A tensor representing the precomputed lesson plan embedding.
    :param model: The SentenceTransformer model instance.
    :return: A float representing the cosine similarity (between 0 and 1).
    """
    message_embedding = model.encode(message, convert_to_tensor=True)
    similarity = util.cos_sim(message_embedding, lesson_embedding)
    return float(similarity)


def write_csv(data, output_filename, ngrams_list=None, lesson_embedding=None, model=None):
    """
    Write the combined data to a CSV file.
    
    Each entry in data should be a dictionary. The CSV will include these fields:
      type, block_index, timestamp, time, end, speaker, message, stemmed_message.
    If ngrams_list is provided, an extra field "assigned_category" will be added.
    If lesson_embedding and model are provided, an extra field "lesson_relevancy" will be added.
    
    :param data: List of dictionaries representing the combined entries.
    :param output_filename: Path to the output CSV file.
    :param ngrams_list: Optional list of n‑grams for categorizing messages.
    :param lesson_embedding: Optional precomputed lesson plan embedding (tensor).
    :param model: Optional SentenceTransformer model instance used for semantic similarity.
    """
    # Base fields.
    fieldnames = ["type", "block_index", "timestamp", "time", "end", "speaker", "message", "stemmed_message"]
    if ngrams_list is not None:
        fieldnames.append("assigned_category")
    if lesson_embedding is not None and model is not None:
        fieldnames.append("lesson_relevancy")
    
    stemmer = PorterStemmer()
    with open(output_filename, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in data:
            # For transcript entries, use the 'text' field; for chat entries, use 'message'
            message = entry.get("text", "") if entry.get("type") == "transcript" else entry.get("message", "")
            stemmed_message = stem_text(message, stemmer)
            row = {
                "type": entry.get("type", ""),
                "block_index": entry.get("block_index", ""),
                "timestamp": entry.get("timestamp", ""),
                "time": entry.get("time", ""),
                "end": entry.get("end", ""),
                "speaker": entry.get("speaker", ""),
                "message": message,
                "stemmed_message": stemmed_message,
            }
            if ngrams_list is not None:
                row["assigned_category"] = categorize_message(message, ngrams_list)
            if lesson_embedding is not None and model is not None:
                row["lesson_relevancy"] = compute_semantic_similarity(message, lesson_embedding, model)
            writer.writerow(row)


def process_zoom_data(vtt_filename, chat_filename, output_csv, ngrams_filename=None, lesson_plan=None):
    """
    Process Zoom data by parsing the VTT transcript and chat log,
    combining the entries, optionally categorizing each message using an n‑grams file,
    and optionally quantifying the relevancy of each message to the lesson plan using semantic similarity.
    The results are written to a CSV file.
    
    :param vtt_filename: Path to the VTT transcript file.
    :param chat_filename: Path to the chat log file.
    :param output_csv: Path to the output CSV file.
    :param ngrams_filename: Optional path to the n‑grams CSV file.
    :param lesson_plan: Optional path to a lesson plan text file.
    :return: Combined list of entries.
    """
    transcript = parse_vtt(vtt_filename)
    chat_log = parse_chat_log(chat_filename)
    combined = combine_data(transcript, chat_log)
    ngrams_list = load_ngrams(ngrams_filename) if ngrams_filename else None

    lesson_embedding = None
    semantic_model = None
    if lesson_plan is not None:
        # Read the lesson plan file.
        with open(lesson_plan, "r", encoding="utf-8") as f:
            lesson_content = f.read()
        # Optionally use extract_keywords if desired.
        # For semantic similarity, we use the full lesson content.
        semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        lesson_embedding = semantic_model.encode(lesson_content, convert_to_tensor=True)
    
    write_csv(combined, output_csv, ngrams_list, lesson_embedding, semantic_model)
    return combined


# When run as a script, use the CLI.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parse Zoom VTT transcript and chat log files, combine them, stem words, "
                    "categorize messages using n-grams, compute semantic relevancy to a lesson plan, and output to CSV."
    )
    parser.add_argument("--vtt", required=True, help="Path to the VTT transcript file")
    parser.add_argument("--chat", required=True, help="Path to the chat log file")
    parser.add_argument("--output", required=True, help="Path to the output CSV file")
    parser.add_argument("--ngrams", help="Optional path to the n-grams CSV file")
    parser.add_argument("--lesson", help="Optional path to a lesson plan text file")
    args = parser.parse_args()

    process_zoom_data(args.vtt, args.chat, args.output, args.ngrams, args.lesson)
    print(f"Combined CSV output written to {args.output}")
