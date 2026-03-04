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

// ========== 旅行计划数据结构 ==========

// 酒店信息
export interface Hotel {
  name: string;
  address: string;
  price_range?: string;
  rating?: string;
  distance?: string;
  type?: string;
  estimated_cost?: number;
}

// 景点信息
export interface Attraction {
  name: string;
  address: string;
  visit_duration?: number;
  description?: string;
  category?: string;
  rating?: number;
  ticket_price?: number;
}

// 餐饮信息
export interface Meal {
  type: string;
  name: string;
  address?: string;
  description?: string;
  estimated_cost?: number;
}

// 天气信息
export interface WeatherInfo {
  date: string;
  day_weather: string;
  night_weather: string;
  day_temp: number;
  night_temp: number;
  wind_direction: string;
  wind_power: string;
}

// 每日行程
export interface DayPlan {
  date: string;
  day_index: number;
  description: string;
  transportation?: string;
  accommodation?: string;
  hotel?: Hotel;
  attractions: Attraction[];
  meals?: Meal[];
}

// 预算信息
export interface Budget {
  total_attractions?: number;
  total_hotels?: number;
  total_meals?: number;
  total_transportation?: number;
  total?: number;
}

// 完整旅行计划
export interface TripPlan {
  city: string;
  start_date: string;
  end_date: string;
  days: DayPlan[];
  weather_info?: WeatherInfo[];
  overall_suggestions: string;
  budget?: Budget;
}
