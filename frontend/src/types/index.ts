// 旅行计划请求
export interface TripRequest {
  input: string;
  session_id: string;
}

// 响应类型枚举
export type TripPlanType = 'clarify' | 'stop';

// 旅行计划响应
export interface TripPlanResponse {
  success: boolean;
  type: TripPlanType;
  message: string;
}

// 消息角色
export type MessageRole = 'user' | 'assistant';

// 聊天消息
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  type?: TripPlanType; // 仅用于 assistant 消息
}

// Session 信息
export interface SessionInfo {
  id: string;
  createdAt: number;
  expiresAt: number;
}
