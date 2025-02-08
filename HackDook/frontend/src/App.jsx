import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/dashboard" element={<h1>Dashboard Page (Coming Soon)</h1>} />
                <Route path="/upload" element={<h1>Upload Page (Coming Soon)</h1>} />
                <Route path="/reports" element={<h1>Reports Page (Coming Soon)</h1>} />
                <Route path="/settings" element={<h1>Settings Page (Coming Soon)</h1>} />
            </Routes>
        </Router>
    );
}

export default App;
