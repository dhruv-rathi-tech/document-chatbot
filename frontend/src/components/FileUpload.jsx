import { useRef, useState } from "react";
import { Paperclip, FileText, X, Loader2 } from "lucide-react";
import "./FileUpload.css";

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.pptx,.xlsx,.txt,.md";

export default function FileUpload({ uploadedFiles, isUploading, onUpload, onRemoveAll }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  function handleFilesSelected(fileList) {
    const files = Array.from(fileList);
    if (files.length > 0) {
      onUpload(files);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    handleFilesSelected(e.dataTransfer.files);
  }

  return (
    <div className="file-upload">
      <div
        className={`file-upload__dropzone ${isDragging ? "file-upload__dropzone--active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS}
          hidden
          onChange={(e) => handleFilesSelected(e.target.files)}
        />

        {isUploading ? (
          <>
            <Loader2 size={22} className="file-upload__spin" />
            <span>Processing documents…</span>
          </>
        ) : (
          <>
            <Paperclip size={22} />
            <span>
              <strong>Click to upload</strong> or drag and drop
            </span>
            <span className="file-upload__hint">PDF, DOCX, PPTX, XLSX, TXT, MD</span>
          </>
        )}
      </div>

      {uploadedFiles.length > 0 && (
        <div className="file-upload__list">
          <div className="file-upload__list-header">
            <span>{uploadedFiles.length} document{uploadedFiles.length > 1 ? "s" : ""} loaded</span>
            <button
              className="file-upload__clear-btn"
              onClick={onRemoveAll}
              title="Remove all documents and start a new session"
            >
              <X size={14} />
              Clear
            </button>
          </div>
          <div className="file-upload__chips">
            {uploadedFiles.map((name) => (
              <div className="file-upload__chip" key={name}>
                <FileText size={14} />
                <span>{name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
