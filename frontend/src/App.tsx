import { Header } from './components/Header';
import { MessageList } from './components/MessageList';
import { ChatInput } from './components/ChatInput';
import { useChat } from './hooks/useChat';

function App() {
  const {
    messages,
    isLoading,
    error,
    sessionRemainingMinutes,
    sendMessage,
    clearChat,
  } = useChat();

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 顶部导航 */}
      <Header
        sessionRemainingMinutes={sessionRemainingMinutes}
        onNewChat={clearChat}
      />

      {/* 消息列表 */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full max-w-4xl mx-auto flex flex-col">
          <MessageList messages={messages} isLoading={isLoading} />
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200">
          <div className="max-w-4xl mx-auto flex items-center gap-2 text-red-600 text-sm">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* 输入框 */}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}

export default App;
