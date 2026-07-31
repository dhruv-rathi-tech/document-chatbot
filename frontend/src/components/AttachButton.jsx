import { useRef, useState } from "react";
import { Paperclip, Loader2 } from "lucide-react";
import "./AttachButton.css";

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.pptx,.xlsx,.txt,.md";

export default function AttachButton({ onUpload, isUploading, disabled }) {
  const inputRef = useRef(null);
  const [showTooltip, setShowTooltip] = useState(false);

  function handleFilesSelected(fileList) {
    const files = Array.from(fileList);
    if (files.length > 0) {
      onUpload(files);
    }
    // Reset so selecting the same file again still fires onChange.
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div
      className="attach-button"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_EXTENSIONS}
        hidden
        onChange={(e) => handleFilesSelected(e.target.files)}
        disabled={disabled}
      />
      <button
        type="button"
        className="attach-button__trigger"
        onClick={() => inputRef.current?.click()}
        disabled={disabled || isUploading}
        aria-label="Upload documents"
      >
        {isUploading ? (
          <Loader2 size={18} className="attach-button__spin" />
        ) : (
          <Paperclip size={18} />
        )}
      </button>

      {showTooltip && !isUploading && (
        <div className="attach-button__tooltip">
          <strong>Upload documents</strong>
          <span>PDF, DOCX, PPTX, XLSX, TXT, MD</span>
        </div>
      )}
    </div>
  );
}
