import { useState, useCallback, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import type { ChatMessage, SessionInfo, TripPlanResponse } from '../types';
import { tripApi } from '../services/api';
import { getSession, clearSession, getSessionRemainingMinutes } from '../services/session';

// 消息存储的 localStorage key
const MESSAGES_STORAGE_KEY = 'travel_assistant_messages';

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  session: SessionInfo;
  sessionRemainingMinutes: number;
  sendMessage: (content: string) => Promise<void>;
  clearChat: () => void;
}

export const useChat = (): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<SessionInfo>(() => getSession());
  const [sessionRemainingMinutes, setSessionRemainingMinutes] = useState<number>(
    () => getSessionRemainingMinutes(getSession())
  );

  // 从 localStorage 加载消息历史
  useEffect(() => {
    const storedMessages = localStorage.getItem(`${MESSAGES_STORAGE_KEY}_${session.id}`);
    if (storedMessages) {
      try {
        const parsed = JSON.parse(storedMessages);
        // 恢复 Date 对象
        const restored = parsed.map((msg: ChatMessage) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
        setMessages(restored);
      } catch (e) {
        console.error('Error loading messages:', e);
      }
    }
  }, [session.id]);

  // 保存消息到 localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(`${MESSAGES_STORAGE_KEY}_${session.id}`, JSON.stringify(messages));
    }
  }, [messages, session.id]);

  // 更新 session 剩余时间
  useEffect(() => {
    const interval = setInterval(() => {
      const remaining = getSessionRemainingMinutes(session);
      setSessionRemainingMinutes(remaining);
      
      // 如果 session 过期，自动清理
      if (remaining <= 0) {
        const newSession = getSession();
        if (newSession.id !== session.id) {
          setSession(newSession);
          setMessages([]);
        }
      }
    }, 60000); // 每分钟更新一次

    return () => clearInterval(interval);
  }, [session]);

  // 发送消息
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    setError(null);

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // 调用 API
      const response: TripPlanResponse = await tripApi.planTrip({
        input: content.trim(),
        session_id: session.id,
      });

      // 添加助手回复
      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        type: response.type,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Error sending message:', err);
      const errorMessage = err instanceof Error ? err.message : '发送消息失败，请稍后重试';
      setError(errorMessage);
      
      // 添加错误消息
      const errorMsg: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: `抱歉，发生了错误：${errorMessage}`,
        timestamp: new Date(),
        type: 'stop',
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [session.id, isLoading]);

  // 清除聊天记录并创建新 session
  const clearChat = useCallback(() => {
    // 清除当前 session 的消息
    localStorage.removeItem(`${MESSAGES_STORAGE_KEY}_${session.id}`);
    
    // 创建新的 session
    const newSession = clearSession();
    setSession(newSession);
    setMessages([]);
    setError(null);
    setSessionRemainingMinutes(getSessionRemainingMinutes(newSession));
  }, [session.id]);

  return {
    messages,
    isLoading,
    error,
    session,
    sessionRemainingMinutes,
    sendMessage,
    clearChat,
  };
};
