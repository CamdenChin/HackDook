import React, { useState } from "react";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import { Link } from "react-router-dom";

function Home() {
    const [files, setFiles] = useState([]);
    const [program, setProgram] = useState("");
    const [instructor, setInstructor] = useState("");
    const [date, setDate] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const { getRootProps, getInputProps } = useDropzone({
        accept: ".txt, .csv, .json, .xlsx",
        onDrop: (acceptedFiles) => {
            setFiles((prevFiles) => [...prevFiles, ...acceptedFiles]);
        },
    });

    const handleUpload = async () => {
        if (!program || !instructor || !date || files.length === 0) {
            setError("Please provide all required fields and upload files.");
            return;
        }

        setLoading(true);
        const formData = new FormData();
        files.forEach((file) => formData.append("files", file));
        formData.append("program", program);
        formData.append("instructor", instructor);
        formData.append("date", date);

        try {
            await axios.post("http://localhost:5001/api/upload", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            alert("Files uploaded successfully!");
        } catch (err) {
            console.error(err);
            setError("Error uploading files.");
        }
        setLoading(false);
    };

    return (
        <div className="p-6 max-w-3xl mx-auto">
            {/* Header Section */}
            <header className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">🔥 Ignite Engagement Tracker</h1>
                <nav>
                    <Link to="/dashboard" className="mr-4">Dashboard</Link>
                    <Link to="/upload" className="mr-4">Upload</Link>
                    <Link to="/reports" className="mr-4">Reports</Link>
                    <Link to="/settings">Settings</Link>
                </nav>
            </header>

            {/* File Upload Section */}
            <div {...getRootProps()} className="border-dashed border-2 p-6 text-center cursor-pointer bg-gray-100">
                <input {...getInputProps()} />
                <p>Drag & drop files here, or click to select files</p>
                <p className="text-sm text-gray-500">(Supported: .txt, .csv, .json, .xlsx)</p>
            </div>
            <ul className="mt-3">
                {files.map((file, index) => (
                    <li key={index} className="text-sm">📄 {file.name}</li>
                ))}
            </ul>

            {/* Metadata Entry */}
            <div className="mt-4 space-y-2">
                <input type="text" placeholder="Program Name" value={program} onChange={(e) => setProgram(e.target.value)} className="border p-2 w-full" />
                <input type="text" placeholder="Instructor Name" value={instructor} onChange={(e) => setInstructor(e.target.value)} className="border p-2 w-full" />
                <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="border p-2 w-full" />
            </div>

            {/* Process Button */}
            <button onClick={handleUpload} className="mt-4 bg-blue-600 text-white px-4 py-2 rounded w-full">
                {loading ? "Uploading..." : "Process & Analyze"}
            </button>

            {/* Error Message */}
            {error && <p className="text-red-500 mt-2">{error}</p>}
        </div>
    );
}

export default Home;
