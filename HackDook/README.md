# Zoom Engagement Tracker

Zoom Engagement Tracker is a web application designed to help you analyze and track participant engagement during Zoom meetings. The app parses Zoom transcripts and chat logs to provide insights into engagement levels by counting spoken lines and chat messages. It even supports multi-week analysis, making it easier to track trends over time.

## Features

- **File Upload**: Easily upload Zoom transcript and chat log files.
- **Engagement Analysis**: Automatically analyze and display participant engagement based on spoken lines and chat messages.
- **Dynamic Data Table**: View the parsed engagement data in a dynamic and interactive table.
- **Multi-Week Analysis**: Track engagement trends across multiple weeks.

## Prerequisites

Before you begin, make sure you have the following installed on your machine:

- **Node.js** (version 16 or newer)
- **npm** (Node Package Manager, which comes with Node.js)

## Setup Instructions

Follow these steps to get the project up and running on your local machine.

### 1. Clone the Repository

Clone the repository and navigate to the frontend directory:

```
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>/frontend
```

### 2. Install Frontend Dependencies
Install the required dependencies for the frontend:

```
npm install
```

###  3. Start the Backend (Express Server)
Open a new terminal window, navigate to the backend directory, and install its dependencies:

```
cd ../backend
npm install
```

Start the backend server:

```
npm start
The backend will run on http://localhost:5001.
```

### 4. Start the Frontend (React App)
Navigate back to the frontend directory and start the React application:

```
cd ../frontend
npm start
The frontend will run on http://localhost:3000.
```

### Customization
Feel free to modify the application to meet your specific needs. Both the frontend and backend are modular and easy to extend.

### Contributing
If you would like to contribute to this project, fork the repository, make your changes, and submit a pull request for review.

### License
This project is licensed under the MIT License.

