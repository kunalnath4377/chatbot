import React, { useState, useRef, useEffect } from "react";
import axios from "axios";

const App = () => {
    const [file, setFile] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [messages, setMessages] = useState([]);
    const chatContainerRef = useRef(null);

    // Automatically scroll to the bottom when new messages are added
    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const handleFileUpload = async () => {
        if (!file) return; // Ignore if no file is selected

        setIsProcessing(true);
        setMessages((prev) => [...prev, { type: "user", content: `Uploaded file: ${file.name}` }]);

        try {
            const formData = new FormData();
            formData.append("file", file);
            const res = await axios.post(
                "http://localhost:8000/upload-file",
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );
            setMessages((prev) => [...prev, { type: "assistant", content: res.data.summary }]);
        } catch (error) {
            console.error("Error uploading file:", error);
            setMessages((prev) => [...prev, { type: "error", content: "An error occurred while processing the file." }]);
        } finally {
            setIsProcessing(false);
            setFile(null); // Clear the file input
        }
    };

    // Function to render numbered list with styling
    const renderNumberedList = (text) => {
        return text.split("\n\n").map((point, index) => (
            <div key={index} style={{ marginBottom: "8px" }}>
                <span style={{ fontWeight: "bold", fontSize: "1.2em" }}>
                    {point.split(".")[0]}.
                </span>
                <span>{point.split(".").slice(1).join(".")}</span>
            </div>
        ));
    };

    return (
        <div style={{ padding: "20px", fontFamily: "Arial, sans-serif", maxWidth: "800px", margin: "0 auto" }}>
            
            {/* Chat Container */}
            <div
                ref={chatContainerRef}
                style={{
                    height: "400px",
                    overflowY: "auto",
                    border: "1px solid #ccc",
                    borderRadius: "5px",
                    padding: "10px",
                    marginBottom: "20px",
                    backgroundColor: "#f9f9f9",
                }}
            >
                {messages.map((message, index) => (
                    <div
                        key={index}
                        style={{
                            marginBottom: "10px",
                            textAlign: message.type === "user" ? "right" : "left",
                        }}
                    >
                        <div
                            style={{
                                display: "inline-block",
                                padding: "10px",
                                borderRadius: "10px",
                                backgroundColor: message.type === "user" ? "#007bff" : "#e9ecef",
                                color: message.type === "user" ? "#fff" : "#000",
                            }}
                        >
                            {message.type === "assistant" && typeof message.content === "string"
                                ? renderNumberedList(message.content)
                                : message.content}
                        </div>
                    </div>
                ))}
                {isProcessing && (
                    <div style={{ textAlign: "center", color: "#666", fontStyle: "italic" }}>
                        Processing...
                    </div>
                )}
            </div>

            {/* File Upload Section */}
            <div style={{ marginBottom: "20px" }}>
                <input
                    type="file"
                    onChange={(e) => setFile(e.target.files[0])}
                    style={{ marginRight: "10px" }}
                />
                <button
                    onClick={handleFileUpload}
                    disabled={isProcessing}
                    style={{ padding: "10px 20px", cursor: "pointer", borderRadius: "5px", border: "none", backgroundColor: "#28a745", color: "#fff" }}
                >
                    Upload File
                </button>
            </div>
        </div>
    );
};

export default App;