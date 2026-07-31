import { User, Bot, AlertCircle } from "lucide-react";
import "./ChatMessage.css";

export default function ChatMessage({ role, content, isError }) {
  const isUser = role === "user";

  return (
    <div className={`chat-message ${isUser ? "chat-message--user" : "chat-message--assistant"}`}>
      <div className={`chat-message__avatar ${isError ? "chat-message__avatar--error" : ""}`}>
        {isUser ? <User size={16} /> : isError ? <AlertCircle size={16} /> : <Bot size={16} />}
      </div>
      <div className="chat-message__body">
        <div className="chat-message__role">{isUser ? "You" : "Assistant"}</div>
        <div className={`chat-message__content ${isError ? "chat-message__content--error" : ""}`}>
          {formatContent(content)}
        </div>
      </div>
    </div>
  );
}


function formatContent(content) {
  if (!content) return null;

  const sourcesIndex = content.indexOf("Sources");
  const mainText = sourcesIndex !== -1 ? content.slice(0, sourcesIndex).trim() : content;
  const sourcesText = sourcesIndex !== -1 ? content.slice(sourcesIndex).trim() : null;

  const paragraphs = mainText.split(/\n{2,}/).filter(Boolean);

  return (
    <>
      {paragraphs.map((para, i) => (
        <p key={i}>{para}</p>
      ))}
      {sourcesText && <div className="chat-message__sources">{sourcesText}</div>}
    </>
  );
}
