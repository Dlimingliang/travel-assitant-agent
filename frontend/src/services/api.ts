import axios from 'axios';
import type { AxiosInstance } from 'axios';
import type { TripRequest, TripPlanResponse } from '../types';

// API 基础配置
// 生产环境使用空字符串（相对路径），开发环境使用 localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL !== undefined 
  ? import.meta.env.VITE_API_BASE_URL 
  : 'http://localhost:8000';

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 12000000, // 2分钟超时，因为 Agent 处理可能较慢
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('[API] Response:', response.data);
    return response;
  },
  (error) => {
    console.error('[API] Response error:', error);
    return Promise.reject(error);
  }
);

// API 服务
export const tripApi = {
  /**
   * 发送旅行规划请求
   * @param request 旅行请求参数
   * @returns 旅行计划响应
   */
  planTrip: async (request: TripRequest): Promise<TripPlanResponse> => {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', request);
    return response.data;
  },

  /**
   * 健康检查
   * @returns 健康状态
   */
  healthCheck: async (): Promise<{ status: string; service: string; version: string }> => {
    const response = await apiClient.get('/api/health');
    return response.data;
  },
};

export default apiClient;
