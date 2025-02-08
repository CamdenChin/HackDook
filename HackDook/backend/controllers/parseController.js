// controllers/parseController.js
const fs = require('fs');
const path = require('path');
const { Session, Participant } = require('../models');

exports.uploadFiles = async (req, res) => {
  try {
    const { weekNumber } = req.body;

    // Create a new session for the given weekNumber
    const session = await Session.create({ weekNumber });

    // If files exist, parse them
    if (!req.files || !req.files.transcript || !req.files.chat) {
      return res.status(400).json({ message: 'Files not provided correctly.' });
    }

    // ---------- Parse Transcript ----------
    const transcriptPath = req.files.transcript[0].path;
    const transcriptData = fs.readFileSync(transcriptPath, 'utf8');
    
    // Simple line-by-line approach: each line with "Name:" or similar
    const transcriptLines = transcriptData.split('\n');
    const transcriptSpeakers = {};

    transcriptLines.forEach(line => {
      // Example format: "John Smith: Hello everyone..."
      const parts = line.split(':');
      if (parts.length > 1) {
        const name = parts[0].trim();
        if (!transcriptSpeakers[name]) {
          transcriptSpeakers[name] = 0;
        }
        transcriptSpeakers[name] += 1;
      }
    });

    // ---------- Parse Chat ----------
    const chatPath = req.files.chat[0].path;
    const chatData = fs.readFileSync(chatPath, 'utf8');
    
    // Each line might look like: "08:33:21 From John Smith to Everyone : Hello all!"
    const chatLines = chatData.split('\n');
    const chatSpeakers = {};

    chatLines.forEach(line => {
      // We look for "From <Name> to"
      // Example: "08:33:21 From John Smith to Everyone : Hello all!"
      const fromIndex = line.indexOf('From ');
      const toIndex = line.indexOf(' to ');
      if (fromIndex !== -1 && toIndex !== -1) {
        const partialStr = line.substring(fromIndex + 5, toIndex).trim(); 
        // partialStr should be the student's name, e.g., "John Smith"
        if (!chatSpeakers[partialStr]) {
          chatSpeakers[partialStr] = 0;
        }
        chatSpeakers[partialStr] += 1;
      }
    });

    // Combine data and store in DB
    // We'll assume the "name" in transcriptSpeakers and chatSpeakers should align exactly 
    // in a real scenario, might need more robust matching or email references
    const allNames = new Set([...Object.keys(transcriptSpeakers), ...Object.keys(chatSpeakers)]);

    for (let name of allNames) {
      const transcriptCount = transcriptSpeakers[name] || 0;
      const chatCount = chatSpeakers[name] || 0;

      await Participant.create({
        name,
        transcriptLines: transcriptCount,
        chatCount,
        sessionId: session.id
      });
    }

    res.status(200).json({ message: 'Files uploaded and parsed successfully', sessionId: session.id });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Error parsing files', error });
  }
};

exports.getEngagementByWeek = async (req, res) => {
  try {
    const { weekNumber } = req.params;
    const session = await Session.findOne({ where: { weekNumber } });
    if (!session) {
      return res.status(404).json({ message: `No session found for week ${weekNumber}` });
    }

    const participants = await Participant.findAll({ where: { sessionId: session.id } });

    res.json({ session, participants });
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: 'Error retrieving data', error });
  }
};
