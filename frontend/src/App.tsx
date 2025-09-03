import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageSquare, History, Trash2, Settings } from 'lucide-react';
import './App.css';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  sources?: Source[];
}

interface Source {
  id: number;
  source: string;
  path: string;
  content_preview: string;
}

interface ChatSession {
  id: string;
  name: string;
  lastMessage: string;
  timestamp: Date;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputText,
          session_id: currentSessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response,
        isUser: false,
        timestamp: new Date(),
        sources: data.sources || [],
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Mettre à jour ou créer la session
      if (!currentSessionId) {
        setCurrentSessionId(data.session_id);
        const newSession: ChatSession = {
          id: data.session_id,
          name: inputText.substring(0, 30) + (inputText.length > 30 ? '...' : ''),
          lastMessage: data.response.substring(0, 50) + '...',
          timestamp: new Date(),
        };
        setSessions(prev => [newSession, ...prev]);
      } else {
        setSessions(prev => prev.map(session => 
          session.id === currentSessionId 
            ? { ...session, lastMessage: data.response.substring(0, 50) + '...', timestamp: new Date() }
            : session
        ));
      }

    } catch (error) {
      console.error('Erreur:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Erreur de connexion: ${error instanceof Error ? error.message : 'Erreur inconnue'}`,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const newChat = () => {
    setMessages([]);
    setCurrentSessionId(null);
  };

  const loadSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    // Ici vous pourriez charger l'historique de la session depuis l'API
    setMessages([]); // Pour l'instant, on repart à zéro
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await fetch(`http://localhost:8000/chat/${sessionId}`, {
        method: 'DELETE',
      });
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSessionId === sessionId) {
        newChat();
      }
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
    }
  };

  return (
    <div className="app">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <button className="toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <MessageSquare size={24} />
          </button>
          <h2>SIFHR Assistant</h2>
        </div>

        <div className="sidebar-content">
          <button className="new-chat-btn" onClick={newChat}>
            <MessageSquare size={20} />
            Nouvelle conversation
          </button>

          <div className="sessions-section">
            <h3><History size={16} /> Historique</h3>
            <div className="sessions-list">
              {sessions.map(session => (
                <div 
                  key={session.id}
                  className={`session-item ${currentSessionId === session.id ? 'active' : ''}`}
                  onClick={() => loadSession(session.id)}
                >
                  <div className="session-info">
                    <div className="session-name">{session.name}</div>
                    <div className="session-preview">{session.lastMessage}</div>
                    <div className="session-time">
                      {session.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                  <button 
                    className="delete-session"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(session.id);
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="sidebar-footer">
          <button className="settings-btn">
            <Settings size={20} />
            Paramètres
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="main-content">
        <div className="chat-header">
          <h1>Guide Narratif du Monde Arabo-Musulman</h1>
          <p>Créez des scénarios immersifs de chasse au trésor</p>
        </div>

        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h3>🏛️ Bienvenue dans l'univers SIFHR</h3>
              <p>Explorez les mystères et légendes de la civilisation arabo-musulmane</p>
              <div className="example-questions">
                <h4>Exemples de questions :</h4>
                <ul>
                  <li>"Crée un scénario de chasse au trésor dans Bagdad"</li>
                  <li>"Parle-moi des trésors de Haroun al-Rachid"</li>
                  <li>"Décris l'architecture de Cordoue au Xe siècle"</li>
                  <li>"Qu'est-ce que SIFHR ?"</li>
                </ul>
              </div>
            </div>
          )}

          {messages.map(message => (
            <div key={message.id} className={`message ${message.isUser ? 'user' : 'bot'}`}>
              <div className="message-content">
                <div className="message-text">
                  {message.text.split('\n').map((line, index) => (
                    <React.Fragment key={index}>
                      {line}
                      {index < message.text.split('\n').length - 1 && <br />}
                    </React.Fragment>
                  ))}
                </div>
                
                {message.sources && message.sources.length > 0 && (
                  <div className="sources">
                    <h5>📚 Sources utilisées :</h5>
                    {message.sources.map(source => (
                      <div key={source.id} className="source-item">
                        <strong>{source.source}</strong>
                        <p>{source.content_preview}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="message-time">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message bot loading">
              <div className="message-content">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <p>L'agent réfléchit et consulte la base de connaissances...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Posez votre question sur la civilisation arabo-musulmane..."
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              disabled={isLoading}
              rows={1}
            />
            <button 
              onClick={sendMessage} 
              disabled={isLoading || !inputText.trim()}
              className="send-btn"
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
