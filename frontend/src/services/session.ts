import { v4 as uuidv4 } from 'uuid';
import type { SessionInfo } from '../types';

const SESSION_STORAGE_KEY = 'travel_assistant_session';
const SESSION_EXPIRY_HOURS = 1; // 1小时过期

/**
 * 获取 Session 信息
 * 如果不存在或已过期，创建新的 Session
 */
export const getSession = (): SessionInfo => {
  const storedSession = localStorage.getItem(SESSION_STORAGE_KEY);
  
  if (storedSession) {
    try {
      const session: SessionInfo = JSON.parse(storedSession);
      const now = Date.now();
      
      // 检查是否过期
      if (session.expiresAt > now) {
        return session;
      }
      // Session 已过期，清除旧数据
      console.log('[Session] Session expired, creating new one');
    } catch (e) {
      console.error('[Session] Error parsing session:', e);
    }
  }
  
  // 创建新的 Session
  return createNewSession();
};

/**
 * 创建新的 Session
 */
export const createNewSession = (): SessionInfo => {
  const now = Date.now();
  const session: SessionInfo = {
    id: uuidv4(),
    createdAt: now,
    expiresAt: now + SESSION_EXPIRY_HOURS * 60 * 60 * 1000, // 1小时后过期
  };
  
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
  console.log('[Session] Created new session:', session.id);
  
  return session;
};

/**
 * 清除 Session（用于新建对话）
 */
export const clearSession = (): SessionInfo => {
  localStorage.removeItem(SESSION_STORAGE_KEY);
  return createNewSession();
};

/**
 * 检查 Session 是否有效
 */
export const isSessionValid = (session: SessionInfo): boolean => {
  return session.expiresAt > Date.now();
};

/**
 * 获取 Session 剩余时间（分钟）
 */
export const getSessionRemainingMinutes = (session: SessionInfo): number => {
  const remaining = session.expiresAt - Date.now();
  return Math.max(0, Math.floor(remaining / (60 * 1000)));
};
