import React, { useState } from 'react';
import type { TripPlan, DayPlan, WeatherInfo } from '../types';

interface TripPlanCardProps {
  plan: TripPlan;
}

// 天气图标映射
const getWeatherIcon = (weather: string): string => {
  if (weather.includes('晴')) return '☀️';
  if (weather.includes('多云')) return '⛅';
  if (weather.includes('阴')) return '☁️';
  if (weather.includes('雨')) return '🌧️';
  if (weather.includes('雪')) return '🌨️';
  if (weather.includes('雷')) return '⛈️';
  if (weather.includes('雾')) return '🌫️';
  return '🌤️';
};

// 格式化日期
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
  return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]}`;
};

// 天气卡片组件
const WeatherCard: React.FC<{ weather: WeatherInfo }> = ({ weather }) => (
  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-3 text-center min-w-[100px]">
    <div className="text-xs text-gray-500 mb-1">{formatDate(weather.date)}</div>
    <div className="text-2xl mb-1">{getWeatherIcon(weather.day_weather)}</div>
    <div className="text-sm font-medium text-gray-700">{weather.day_weather}</div>
    <div className="text-xs text-gray-500 mt-1">
      <span className="text-red-500">{weather.day_temp}°</span>
      <span className="mx-1">/</span>
      <span className="text-blue-500">{weather.night_temp}°</span>
    </div>
    <div className="text-xs text-gray-400 mt-1">{weather.wind_direction} {weather.wind_power}</div>
  </div>
);

// 每日行程卡片组件
const DayPlanCard: React.FC<{ day: DayPlan; weather?: WeatherInfo }> = ({ day, weather }) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm mb-4">
      {/* 日期头部 */}
      <div 
        className="bg-gradient-to-r from-primary-500 to-primary-600 px-4 py-3 cursor-pointer flex items-center justify-between"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="bg-white/20 rounded-lg px-3 py-1">
            <span className="text-white font-bold">Day {day.day_index + 1}</span>
          </div>
          <div className="text-white">
            <div className="font-medium">{formatDate(day.date)}</div>
          </div>
          {weather && (
            <div className="flex items-center gap-1 bg-white/20 rounded-full px-2 py-1 text-sm text-white">
              <span>{getWeatherIcon(weather.day_weather)}</span>
              <span>{weather.day_temp}°/{weather.night_temp}°</span>
            </div>
          )}
        </div>
        <svg 
          className={`w-5 h-5 text-white transition-transform ${expanded ? 'rotate-180' : ''}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* 展开内容 */}
      {expanded && (
        <div className="p-4">
          {/* 行程描述 */}
          <p className="text-gray-600 mb-4 bg-gray-50 rounded-lg p-3 text-sm">
            📝 {day.description}
          </p>

          {/* 景点列表 */}
          {day.attractions && day.attractions.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <span className="text-lg">🎯</span> 今日景点
              </h4>
              <div className="space-y-2">
                {day.attractions.map((attraction, idx) => (
                  <div 
                    key={idx} 
                    className="flex items-start gap-3 bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg p-3"
                  >
                    <div className="w-8 h-8 rounded-full bg-orange-500 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {idx + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-800">{attraction.name}</div>
                      <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span className="truncate">{attraction.address}</span>
                      </div>
                      {attraction.ticket_price !== undefined && attraction.ticket_price > 0 && (
                        <div className="text-sm text-orange-600 mt-1">
                          🎫 门票: ¥{attraction.ticket_price}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 酒店信息 */}
          {day.hotel && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <span className="text-lg">🏨</span> 住宿推荐
              </h4>
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-3">
                <div className="font-medium text-gray-800">{day.hotel.name}</div>
                <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>{day.hotel.address}</span>
                </div>
                {day.hotel.price_range && (
                  <div className="text-sm text-purple-600 mt-1">
                    💰 价格: {day.hotel.price_range}
                  </div>
                )}
                {day.hotel.rating && (
                  <div className="text-sm text-yellow-600 mt-1">
                    ⭐ 评分: {day.hotel.rating}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 餐饮信息 */}
          {day.meals && day.meals.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                <span className="text-lg">🍽️</span> 餐饮推荐
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {day.meals.map((meal, idx) => (
                  <div key={idx} className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-3">
                    <div className="text-xs text-green-600 font-medium">{meal.type}</div>
                    <div className="font-medium text-gray-800">{meal.name}</div>
                    {meal.estimated_cost && (
                      <div className="text-sm text-gray-500">约 ¥{meal.estimated_cost}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// 主组件
export const TripPlanCard: React.FC<TripPlanCardProps> = ({ plan }) => {
  return (
    <div className="w-full">
      {/* 头部概览 */}
      <div className="bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 rounded-xl p-5 mb-4 text-white">
        <div className="flex items-center gap-3 mb-3">
          <div className="text-4xl">🗺️</div>
          <div>
            <h2 className="text-2xl font-bold">{plan.city}之旅</h2>
            <p className="text-white/80 text-sm">
              {formatDate(plan.start_date)} - {formatDate(plan.end_date)} · 共{plan.days.length}天
            </p>
          </div>
        </div>
      </div>

      {/* 天气预报 */}
      {plan.weather_info && plan.weather_info.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span className="text-lg">🌤️</span> 天气预报
          </h3>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {plan.weather_info.map((weather, idx) => (
              <WeatherCard key={idx} weather={weather} />
            ))}
          </div>
        </div>
      )}

      {/* 每日行程 */}
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <span className="text-lg">📅</span> 详细行程
        </h3>
        {plan.days.map((day, idx) => (
          <DayPlanCard 
            key={idx} 
            day={day} 
            weather={plan.weather_info?.find(w => w.date === day.date)}
          />
        ))}
      </div>

      {/* 预算信息 */}
      {plan.budget && plan.budget.total && plan.budget.total > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span className="text-lg">💰</span> 预算概览
          </h3>
          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 rounded-xl p-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-3">
              {plan.budget.total_attractions !== undefined && (
                <div className="text-center">
                  <div className="text-xs text-gray-500">门票</div>
                  <div className="font-semibold text-gray-800">¥{plan.budget.total_attractions}</div>
                </div>
              )}
              {plan.budget.total_hotels !== undefined && (
                <div className="text-center">
                  <div className="text-xs text-gray-500">住宿</div>
                  <div className="font-semibold text-gray-800">¥{plan.budget.total_hotels}</div>
                </div>
              )}
              {plan.budget.total_meals !== undefined && (
                <div className="text-center">
                  <div className="text-xs text-gray-500">餐饮</div>
                  <div className="font-semibold text-gray-800">¥{plan.budget.total_meals}</div>
                </div>
              )}
              {plan.budget.total_transportation !== undefined && (
                <div className="text-center">
                  <div className="text-xs text-gray-500">交通</div>
                  <div className="font-semibold text-gray-800">¥{plan.budget.total_transportation}</div>
                </div>
              )}
            </div>
            <div className="border-t border-orange-200 pt-3 text-center">
              <div className="text-sm text-gray-500">预估总费用</div>
              <div className="text-2xl font-bold text-orange-600">¥{plan.budget.total}</div>
            </div>
          </div>
        </div>
      )}

      {/* 总体建议 */}
      {plan.overall_suggestions && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <span className="text-lg">💡</span> 温馨提示
          </h3>
          <p className="text-gray-600 text-sm leading-relaxed">{plan.overall_suggestions}</p>
        </div>
      )}
    </div>
  );
};
