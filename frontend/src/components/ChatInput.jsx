import { useRef, useState } from "react";
import { ArrowUp } from "lucide-react";
import AttachButton from "./AttachButton";
import "./ChatInput.css";

export default function ChatInput({ onSend, onUpload, isUploading, disabled, placeholder }) {
  const [value, setValue] = useState("");
  const textareaRef = useRef(null);

  function handleChange(e) {
    setValue(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 200) + "px";
    }
  }

  function handleSubmit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="chat-input">
      <AttachButton onUpload={onUpload} isUploading={isUploading} disabled={false} />

      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        disabled={disabled}
      />
      <button
        className="chat-input__send"
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
      >
        <ArrowUp size={18} />
      </button>
    </div>
  );
}