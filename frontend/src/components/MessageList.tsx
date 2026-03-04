import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage as ChatMessageType } from '../types';

interface ChatMessageProps {
  message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`flex items-start gap-3 max-w-[85%] ${
          isUser ? 'flex-row-reverse' : 'flex-row'
        }`}
      >
        {/* 头像 */}
        <div
          className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-white font-medium text-sm ${
            isUser ? 'bg-primary-500' : 'bg-gradient-to-br from-emerald-500 to-teal-500'
          }`}
        >
          {isUser ? '我' : '🧭'}
        </div>

        {/* 消息内容 */}
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-primary-500 text-white'
              : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          ) : (
            <div className="markdown-content">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
          
          {/* 时间戳 */}
          <div
            className={`text-xs mt-2 ${
              isUser ? 'text-primary-100' : 'text-gray-400'
            }`}
          >
            {message.timestamp.toLocaleTimeString('zh-CN', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

interface MessageListProps {
  messages: ChatMessageType[];
  isLoading: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-gray-500">
          <div className="text-6xl mb-4">🗺️</div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">智能旅行助手</h2>
          <p className="text-center text-gray-500 max-w-md">
            你好！我是你的智能旅行规划助手。
            <br />
            告诉我你想去哪里旅行，我会帮你规划行程、推荐景点和酒店。
          </p>
          <div className="mt-6 flex flex-wrap gap-2 justify-center">
            <span className="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600">
              🏖️ 海滨度假
            </span>
            <span className="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600">
              🏔️ 山地探险
            </span>
            <span className="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600">
              🏛️ 文化古迹
            </span>
            <span className="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-600">
              🎢 主题乐园
            </span>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          
          {/* 加载指示器 */}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-9 h-9 rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white">
                  🧭
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3 shadow-sm">
                  <div className="typing-indicator flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                  </div>
                  <p className="text-sm text-gray-500 mt-2">正在为您规划行程...</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};
