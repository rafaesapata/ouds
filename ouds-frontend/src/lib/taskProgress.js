import { useState, useEffect, useRef, useCallback } from 'react';

// OUDS - WebSocket para Task Progress em tempo real
// ================================================

export class TaskProgressWebSocket {
  constructor(sessionId, onTaskUpdate) {
    this.sessionId = sessionId;
    this.onTaskUpdate = onTaskUpdate;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect() {
    try {
      // Use WebSocket endpoint - detect if running locally or in production
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = isLocal ? 'localhost:8000' : window.location.host;
      const wsUrl = `${protocol}//${host}/service/ws/progress/${this.sessionId}`;
      
      console.log('🔌 Connecting to WebSocket:', wsUrl);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.reconnectAttempts = 0;
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };
      
      this.ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        this.attemptReconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('❌ Error creating WebSocket:', error);
    }
  }

  handleMessage(data) {
    console.log('📨 WebSocket message:', data);
    
    // Parse different types of messages
    switch (data.type) {
      case 'step_start':
        this.onTaskUpdate({
          type: 'step_start',
          step: data.step,
          totalSteps: data.total_steps,
          title: data.title || `Step ${data.step}`
        });
        break;
        
      case 'thinking':
        this.onTaskUpdate({
          type: 'thinking',
          thoughts: data.thoughts,
          tools: data.tools || []
        });
        break;
        
      case 'token_usage':
        this.onTaskUpdate({
          type: 'token_usage',
          tokenUsage: {
            input: data.input,
            completion: data.completion,
            total: data.total,
            cumulative: data.cumulative
          }
        });
        break;
        
      case 'tool_execution':
        this.onTaskUpdate({
          type: 'tool_execution',
          tool: data.tool,
          status: data.status,
          output: data.output,
          error: data.error
        });
        break;
        
      case 'step_complete':
        this.onTaskUpdate({
          type: 'step_complete',
          step: data.step,
          output: data.output
        });
        break;
        
      case 'error':
        this.onTaskUpdate({
          type: 'error',
          error: data.error
        });
        break;
        
      default:
        console.log('📝 Unknown message type:', data.type);
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('❌ Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('❌ WebSocket not connected');
    }
  }
}

// Hook para usar TaskProgress WebSocket
export function useTaskProgressWebSocket(sessionId) {
  const [tasks, setTasks] = useState([]);
  const [currentStep, setCurrentStep] = useState(null);
  const [totalSteps, setTotalSteps] = useState(null);
  const wsRef = useRef(null);

  const handleTaskUpdate = useCallback((update) => {
    console.log('🔄 Task update:', update);
    
    switch (update.type) {
      case 'step_start':
        setCurrentStep(update.step);
        setTotalSteps(update.totalSteps);
        
        const newTask = {
          id: `step_${update.step}`,
          title: update.title,
          subtitle: `Step ${update.step} of ${update.totalSteps}`,
          status: 'running',
          timestamp: new Date().toISOString()
        };
        
        setTasks(prev => [...prev, newTask]);
        break;
        
      case 'thinking':
        setTasks(prev => prev.map(task => 
          task.status === 'running' 
            ? { ...task, thoughts: update.thoughts, tools: update.tools }
            : task
        ));
        break;
        
      case 'token_usage':
        setTasks(prev => prev.map(task => 
          task.status === 'running' 
            ? { ...task, tokenUsage: update.tokenUsage }
            : task
        ));
        break;
        
      case 'tool_execution':
        setTasks(prev => prev.map(task => 
          task.status === 'running' 
            ? { 
                ...task, 
                tools: [...(task.tools || []), update.tool],
                output: update.output,
                error: update.error
              }
            : task
        ));
        break;
        
      case 'step_complete':
        setTasks(prev => prev.map(task => 
          task.id === `step_${update.step}` 
            ? { ...task, status: 'completed', output: update.output }
            : task
        ));
        break;
        
      case 'error':
        setTasks(prev => prev.map(task => 
          task.status === 'running' 
            ? { ...task, status: 'error', error: update.error }
            : task
        ));
        break;
    }
  }, []);

  useEffect(() => {
    if (sessionId) {
      wsRef.current = new TaskProgressWebSocket(sessionId, handleTaskUpdate);
      wsRef.current.connect();
      
      return () => {
        if (wsRef.current) {
          wsRef.current.disconnect();
        }
      };
    }
  }, [sessionId, handleTaskUpdate]);

  const resetTasks = useCallback(() => {
    setTasks([]);
    setCurrentStep(null);
    setTotalSteps(null);
  }, []);

  return {
    tasks,
    currentStep,
    totalSteps,
    resetTasks,
    sendMessage: (message) => wsRef.current?.sendMessage(message)
  };
}

