import { useEffect, useRef, useState } from "react";
import { FileQuestion, FileText, X } from "lucide-react";
import FileUpload from "./components/FileUpload";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import TypingIndicator from "./components/TypingIndicator";
import { uploadDocuments, sendChatMessage, clearSession } from "./api";
import "./App.css";

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const [messages, setMessages] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);

  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isGenerating]);

  // Best-effort cleanup of the session's temp files when the tab closes.
  useEffect(() => {
    function handleUnload() {
      if (sessionId) clearSession(sessionId);
    }
    window.addEventListener("beforeunload", handleUnload);
    return () => window.removeEventListener("beforeunload", handleUnload);
  }, [sessionId]);

  async function handleUpload(files) {
    setIsUploading(true);
    setUploadError(null);
    try {
      const result = await uploadDocuments(files, sessionId);
      setSessionId(result.session_id);
      setUploadedFiles((prev) => [...new Set([...prev, ...result.files_processed])]);
    } catch (err) {
      setUploadError(err.message || "Something went wrong while uploading your documents.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleClearSession() {
    await clearSession(sessionId);
    setSessionId(null);
    setUploadedFiles([]);
    setMessages([]);
    setUploadError(null);
  }

  async function handleSend(query) {
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setIsGenerating(true);

    try {
      const result = await sendChatMessage(sessionId, query);
      setMessages((prev) => [...prev, { role: "assistant", content: result.answer }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: err.message || "Something went wrong while generating a response.",
          isError: true,
        },
      ]);
    } finally {
      setIsGenerating(false);
    }
  }

  const hasDocuments = uploadedFiles.length > 0;

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__header-inner">
          <h1>Document Chat</h1>
          <p>Upload your documents and ask questions about them.</p>
        </div>
      </header>

      <main className="app__main" ref={scrollRef}>
        <div className="app__main-inner">
          {!hasDocuments && (
            <section className="app__upload-section">
              <FileUpload
                uploadedFiles={uploadedFiles}
                isUploading={isUploading}
                onUpload={handleUpload}
                onRemoveAll={handleClearSession}
              />
              {uploadError && <div className="app__upload-error">{uploadError}</div>}
            </section>
          )}

          <section className="app__chat-section">
            {messages.length === 0 ? (
              <div className="app__empty-state">
                <FileQuestion size={36} strokeWidth={1.5} />
                <p>
                  {hasDocuments
                    ? "Ask a question about your uploaded documents."
                    : "Upload a document above to get started."}
                </p>
              </div>
            ) : (
              <div className="app__messages">
                {messages.map((msg, i) => (
                  <ChatMessage key={i} role={msg.role} content={msg.content} isError={msg.isError} />
                ))}
                {isGenerating && <TypingIndicator />}
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="app__footer">
        <div className="app__footer-inner">
          {hasDocuments && (
            <div className="app__uploaded-chips">
              <div className="app__uploaded-chips-header">
                <span>
                  {uploadedFiles.length} document{uploadedFiles.length > 1 ? "s" : ""} loaded
                </span>
                <button
                  className="app__clear-btn"
                  onClick={handleClearSession}
                  title="Remove all documents and start a new session"
                >
                  <X size={14} />
                  Clear
                </button>
              </div>
              <div className="app__uploaded-chips-list">
                {uploadedFiles.map((name) => (
                  <div className="app__uploaded-chip" key={name}>
                    <FileText size={14} />
                    <span>{name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {uploadError && hasDocuments && (
            <div className="app__upload-error app__upload-error--footer">{uploadError}</div>
          )}

          <ChatInput
            onSend={handleSend}
            onUpload={handleUpload}
            isUploading={isUploading}
            disabled={isGenerating || !hasDocuments}
            placeholder={
              hasDocuments ? "Ask a question about your documents…" : "Upload a document first…"
            }
          />
        </div>
      </footer>
    </div>
  );
}