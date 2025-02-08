// server.js
const express = require('express');
const cors = require('cors');
const path = require('path');
const multer = require('multer');
const parseRoutes = require('./routes/parseRoutes');
const db = require('./config/db');

const app = express();
const PORT = process.env.PORT || 5001;

// Middleware
app.use(cors());
app.use(express.json());

// Database sync (Sequelize)
db.sync({ alter: true })
  .then(() => console.log('Database synced successfully'))
  .catch((err) => console.error('Error syncing database:', err));

// Routes
app.use('/api', parseRoutes);

// Start Server
app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
