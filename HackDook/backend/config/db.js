// config/db.js
const { Sequelize } = require('sequelize');
const path = require('path');

// Using SQLite for simplicity; you can replace with MySQL/Postgres
const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: path.join(__dirname, 'database.sqlite'), // or ':memory:' for in-memory
  logging: false
});

module.exports = sequelize;
