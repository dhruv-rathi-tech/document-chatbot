import { Bot } from "lucide-react";
import "./ChatMessage.css";
import "./TypingIndicator.css";

export default function TypingIndicator() {
  return (
    <div className="chat-message chat-message--assistant">
      <div className="chat-message__avatar">
        <Bot size={16} />
      </div>
      <div className="chat-message__body">
        <div className="chat-message__role">Assistant</div>
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
}
