import React from 'react';

interface HeaderProps {
  sessionRemainingMinutes: number;
  onNewChat: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  sessionRemainingMinutes,
  onNewChat,
}) => {
  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white text-xl shadow-md">
          🗺️
        </div>
        <div>
          <h1 className="font-semibold text-gray-800 text-lg">智能旅行助手</h1>
          <p className="text-xs text-gray-500">基于 AI 的个性化旅行规划</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Session 信息 */}
        <div className="hidden sm:flex items-center gap-2 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${sessionRemainingMinutes > 10 ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
            <span>会话有效: {sessionRemainingMinutes} 分钟</span>
          </div>
        </div>

        {/* 新建对话按钮 */}
        <button
          onClick={onNewChat}
          className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          <span className="hidden sm:inline">新对话</span>
        </button>
      </div>
    </header>
  );
};
