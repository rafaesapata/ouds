import React, { useState, useEffect } from 'react';

const TaskProgress = ({ isVisible, tasks = [], currentStep, totalSteps }) => {
  const [expandedTasks, setExpandedTasks] = useState(new Set());

  const toggleTask = (taskId) => {
    const newExpanded = new Set(expandedTasks);
    if (newExpanded.has(taskId)) {
      newExpanded.delete(taskId);
    } else {
      newExpanded.add(taskId);
    }
    setExpandedTasks(newExpanded);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <span className="animate-spin">⚙️</span>;
      case 'completed':
        return '✅';
      case 'error':
        return '❌';
      case 'pending':
        return '⏳';
      default:
        return '📋';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'text-blue-600 bg-blue-50';
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      case 'pending':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  if (!isVisible || tasks.length === 0) {
    return null;
  }

  return (
    <div className="mb-4 border border-gray-200 rounded-lg bg-white shadow-sm">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900 flex items-center">
            🎯 Task Progress
            {currentStep && totalSteps && (
              <span className="ml-2 text-xs text-gray-500">
                Step {currentStep}/{totalSteps}
              </span>
            )}
          </h3>
          <div className="flex items-center space-x-2">
            {currentStep && totalSteps && (
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(currentStep / totalSteps) * 100}%` }}
                ></div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tasks List */}
      <div className="max-h-64 overflow-y-auto">
        {tasks.map((task, index) => (
          <div key={task.id || index} className="border-b border-gray-100 last:border-b-0">
            {/* Task Header */}
            <div 
              className={`px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors ${getStatusColor(task.status)}`}
              onClick={() => toggleTask(task.id || index)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-lg">{getStatusIcon(task.status)}</span>
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {task.title || `Step ${index + 1}`}
                    </div>
                    {task.subtitle && (
                      <div className="text-xs text-gray-500">{task.subtitle}</div>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {task.timestamp && (
                    <span className="text-xs text-gray-400">
                      {new Date(task.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                  <span className="text-gray-400">
                    {expandedTasks.has(task.id || index) ? '▼' : '▶'}
                  </span>
                </div>
              </div>
            </div>

            {/* Task Details (Expandable) */}
            {expandedTasks.has(task.id || index) && (
              <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
                {/* Thoughts */}
                {task.thoughts && (
                  <div className="mb-3">
                    <div className="text-xs font-medium text-gray-700 mb-1">
                      ✨ Manus's thoughts:
                    </div>
                    <div className="text-sm text-gray-600 bg-white p-2 rounded border">
                      {task.thoughts}
                    </div>
                  </div>
                )}

                {/* Tools */}
                {task.tools && task.tools.length > 0 && (
                  <div className="mb-3">
                    <div className="text-xs font-medium text-gray-700 mb-1">
                      🛠️ Tools selected: {task.tools.length}
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {task.tools.map((tool, toolIndex) => (
                        <span 
                          key={toolIndex}
                          className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Token Usage */}
                {task.tokenUsage && (
                  <div className="mb-3">
                    <div className="text-xs font-medium text-gray-700 mb-1">
                      📊 Token usage:
                    </div>
                    <div className="text-xs text-gray-600 bg-white p-2 rounded border font-mono">
                      Input: {task.tokenUsage.input} | 
                      Completion: {task.tokenUsage.completion} | 
                      Total: {task.tokenUsage.total}
                      {task.tokenUsage.cumulative && (
                        <div className="mt-1 text-gray-500">
                          Cumulative: {task.tokenUsage.cumulative.total}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Output/Logs */}
                {task.output && (
                  <div className="mb-3">
                    <div className="text-xs font-medium text-gray-700 mb-1">
                      📝 Output:
                    </div>
                    <div className="text-sm text-gray-600 bg-white p-2 rounded border font-mono text-xs max-h-32 overflow-y-auto">
                      {task.output}
                    </div>
                  </div>
                )}

                {/* Error */}
                {task.error && (
                  <div className="mb-3">
                    <div className="text-xs font-medium text-red-700 mb-1">
                      ❌ Error:
                    </div>
                    <div className="text-sm text-red-600 bg-red-50 p-2 rounded border">
                      {task.error}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      {tasks.length > 0 && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>
              {tasks.filter(t => t.status === 'completed').length} completed, 
              {tasks.filter(t => t.status === 'running').length} running, 
              {tasks.filter(t => t.status === 'pending').length} pending
            </span>
            <span>
              Last update: {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskProgress;

