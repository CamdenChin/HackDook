import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [weekNumber, setWeekNumber] = useState('');
  const [transcript, setTranscript] = useState(null);
  const [chat, setChat] = useState(null);
  const [engagementData, setEngagementData] = useState([]);
  const [error, setError] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!weekNumber || !transcript || !chat) {
      setError('Please provide a week number, transcript, and chat file.');
      return;
    }

    const formData = new FormData();
    formData.append('weekNumber', weekNumber);
    formData.append('transcript', transcript);
    formData.append('chat', chat);

    try {
      const response = await axios.post('http://localhost:5001/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      alert('Files uploaded successfully!');
    } catch (err) {
      console.error(err);
      setError('Error uploading files. Please try again.');
    }
  };

  const fetchEngagement = async () => {
    try {
      const response = await axios.get(`http://localhost:5001/api/engagement/${weekNumber}`);
      setEngagementData(response.data.participants);
    } catch (err) {
      console.error(err);
      setError('Error fetching engagement data.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Zoom Engagement Tracker</h1>

      <form onSubmit={handleUpload}>
        <div>
          <label>Week Number:</label>
          <input
            type="number"
            value={weekNumber}
            onChange={(e) => setWeekNumber(e.target.value)}
            required
          />
        </div>
        <div>
          <label>Transcript File:</label>
          <input
            type="file"
            onChange={(e) => setTranscript(e.target.files[0])}
            required
          />
        </div>
        <div>
          <label>Chat File:</label>
          <input
            type="file"
            onChange={(e) => setChat(e.target.files[0])}
            required
          />
        </div>
        <button type="submit">Upload & Parse</button>
      </form>

      <button onClick={fetchEngagement}>Get Engagement Data</button>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <h2>Engagement Data</h2>
      {engagementData.length > 0 && (
        <table border="1" style={{ borderCollapse: 'collapse', width: '100%' }}>
          <thead>
            <tr>
              <th>Participant</th>
              <th>Chat Messages</th>
              <th>Transcript Lines</th>
            </tr>
          </thead>
          <tbody>
            {engagementData.map((participant) => (
              <tr key={participant.id}>
                <td>{participant.name}</td>
                <td>{participant.chatCount}</td>
                <td>{participant.transcriptLines}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;
