import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageSquare, History, Trash2, Settings, BookOpen, Download, FileText, Eye } from 'lucide-react';
import jsPDF from 'jspdf';
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

interface ScenarioPdf {
  id: string;
  name: string;
  content: string;
  createdAt: Date;
}

interface WebSocketMessage {
  type: string;
  message?: string;
  session_id?: string;
  response?: string;
  sources?: any[];
  length?: number;
  error?: string;
  status?: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioPdf[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<'chat' | 'library'>('chat');
  const [viewingScenario, setViewingScenario] = useState<ScenarioPdf | null>(null);
  
  // WebSocket states
  const [wsConnected, setWsConnected] = useState(false);
  const [wsStatus, setWsStatus] = useState('Disconnected');
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket URL
  const WS_URL = 'ws://127.0.0.1:8002/ws';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // WebSocket connection management
  const connectWebSocket = () => {
    try {
      setWsStatus('Connecting...');
      wsRef.current = new WebSocket(WS_URL);

      wsRef.current.onopen = () => {
        setWsConnected(true);
        setWsStatus('Connected');
        console.log('WebSocket connected');
        
        // Send ping to test connection
        sendWebSocketMessage({ type: 'ping' });
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        setWsConnected(false);
        setWsStatus('Disconnected');
        console.log('WebSocket disconnected');
        
        // Auto-reconnect after 3 seconds
        setTimeout(() => {
          if (!wsConnected) {
            connectWebSocket();
          }
        }, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsStatus('Error');
      };

    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setWsStatus('Failed');
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setWsConnected(false);
    setWsStatus('Disconnected');
  };

  const sendWebSocketMessage = (message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket not connected');
      setWsStatus('Not connected');
    }
  };

  const handleWebSocketMessage = (data: WebSocketMessage) => {
    console.log('WebSocket message received:', data);

    switch (data.type) {
      case 'pong':
        console.log('Pong received');
        break;

      case 'status':
        setWsStatus(data.message || 'Processing...');
        if (data.status === 'generating') {
          setIsStreaming(true);
          setStreamingMessage('');
        }
        break;

      case 'streaming_response':
        setStreamingMessage(data.chunk || '');
        setWsStatus(`Streaming... ${data.progress || 0}%`);
        break;

      case 'chat_response':
        if (data.response) {
          const botMessage: Message = {
            id: (Date.now() + 1).toString(),
            text: data.response,
            isUser: false,
            timestamp: new Date(),
            sources: data.sources || [],
          };

          setMessages(prev => [...prev, botMessage]);
          
          // Reset streaming state
          setIsStreaming(false);
          setStreamingMessage('');
          setWsStatus('Connected');
          
          // Auto-save scenario if it's a treasure hunt scenario
          const isScenario = botMessage.text.toLowerCase().includes('scénario') || 
                            botMessage.text.toLowerCase().includes('chasse au trésor') ||
                            botMessage.text.toLowerCase().includes('quête') ||
                            botMessage.text.includes('##');
          
          if (isScenario) {
            const scenarioName = extractScenarioTitle(botMessage.text) || `Scenario_${Date.now()}`;
            const newScenario: ScenarioPdf = {
              id: Date.now().toString(),
              name: scenarioName,
              content: botMessage.text,
              createdAt: new Date()
            };

            setScenarios(prev => [newScenario, ...prev]);
            localStorage.setItem('sifhr-scenarios', JSON.stringify([newScenario, ...scenarios]));
          }
          
          // Update session
          if (!currentSessionId && data.session_id) {
            setCurrentSessionId(data.session_id);
            const newSession: ChatSession = {
              id: data.session_id,
              name: inputText.substring(0, 30) + (inputText.length > 30 ? '...' : ''),
              lastMessage: data.response.substring(0, 50) + '...',
              timestamp: new Date(),
            };
            setSessions(prev => [newSession, ...prev]);
          }
        }
        
        setIsLoading(false);
        setWsStatus('Connected');
        break;

      case 'error':
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: `Erreur WebSocket: ${data.error}`,
          isUser: false,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
        setIsLoading(false);
        setWsStatus('Error');
        break;
    }
  };

  // Connect WebSocket on component mount
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      disconnectWebSocket();
    };
  }, []);

  const sendMessage = async () => {
    if (!inputText.trim()) return;
    if (!wsConnected) {
      alert('WebSocket not connected. Please wait for reconnection.');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    const messageToSend = inputText;
    setInputText('');

    // Send via WebSocket
    sendWebSocketMessage({
      type: 'chat',
      message: messageToSend,
      session_id: currentSessionId || undefined,
    });
  };

  const newChat = () => {
    setMessages([]);
    setCurrentSessionId(null);
  };

  const loadSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setMessages([]);
  };

  const deleteSession = async (sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      newChat();
    }
  };

  const extractScenarioTitle = (text: string): string => {
    const lines = text.split('\n');
    for (const line of lines) {
      const cleaned = line.replace(/[#*\s]/g, '');
      if (cleaned.length > 5 && cleaned.length < 50) {
        return cleaned.replace(/[^\w\s-]/g, '').trim();
      }
    }
    return `Scenario_${new Date().toLocaleDateString('fr-FR').replace(/\//g, '-')}`;
  };

  const downloadScenario = (scenario: ScenarioPdf) => {
    const element = document.createElement('a');
    const file = new Blob([scenario.content], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = `${scenario.name}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const downloadScenarioPDF = (scenario: ScenarioPdf) => {
    const pdf = new jsPDF();
    
    // Configuration du PDF
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 25;
    const maxWidth = pageWidth - (margin * 2);
    let yPosition = margin;
    
    // === EN-TÊTE AVEC THÈME BLEU ===
    // Fond bleu en en-tête
    pdf.setFillColor(41, 128, 185); // Bleu professionnel
    pdf.rect(0, 0, pageWidth, 35, 'F');
    
    // Titre principal en blanc
    pdf.setTextColor(255, 255, 255);
    pdf.setFontSize(18);
    pdf.setFont(undefined, 'bold');
    pdf.text('SIFHR - Scénarios Historiques', margin, 22);
    
    yPosition = 50;
    
    // === INFORMATIONS DU DOCUMENT ===
    pdf.setTextColor(0, 0, 0); // Noir
    pdf.setFillColor(240, 248, 255); // Bleu très clair
    pdf.rect(margin - 5, yPosition - 5, maxWidth + 10, 25, 'F');
    
    // Titre du scénario
    pdf.setFontSize(14);
    pdf.setFont(undefined, 'bold');
    pdf.setTextColor(41, 128, 185); // Bleu
    pdf.text('Titre : ' + scenario.name, margin, yPosition + 5);
    
    // Date de génération
    pdf.setFontSize(10);
    pdf.setFont(undefined, 'normal');
    pdf.setTextColor(100, 100, 100); // Gris
    pdf.text(`Généré le: ${scenario.createdAt.toLocaleDateString('fr-FR')} à ${scenario.createdAt.toLocaleTimeString('fr-FR')}`, margin, yPosition + 15);
    
    yPosition += 40;
    
    // === LIGNE SÉPARATRICE ===
    pdf.setDrawColor(41, 128, 185);
    pdf.setLineWidth(0.5);
    pdf.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 15;
    
    // === CONTENU PRINCIPAL ===
    pdf.setTextColor(0, 0, 0);
    pdf.setFontSize(11);
    pdf.setFont(undefined, 'normal');
    
    // Traitement du contenu avec formatage amélioré
    const content = scenario.content;
    const sections = content.split('\n');
    
    for (let i = 0; i < sections.length; i++) {
      const line = sections[i].trim();
      
      if (!line) {
        yPosition += 4; // Espace pour ligne vide
        continue;
      }
      
      // Vérifier si nouvelle page nécessaire
      if (yPosition > pageHeight - 40) {
        pdf.addPage();
        
        // Mini en-tête sur nouvelles pages
        pdf.setFillColor(41, 128, 185);
        pdf.rect(0, 0, pageWidth, 20, 'F');
        pdf.setTextColor(255, 255, 255);
        pdf.setFontSize(10);
        pdf.setFont(undefined, 'bold');
        pdf.text(scenario.name, margin, 12);
        
        yPosition = 35;
      }
      
      // Formatage des titres (lignes commençant par #)
      if (line.startsWith('# ') || line.startsWith('## ') || line.startsWith('### ')) {
        yPosition += 8;
        
        // Style titre principal
        if (line.startsWith('# ')) {
          pdf.setFontSize(14);
          pdf.setFont(undefined, 'bold');
          pdf.setTextColor(41, 128, 185);
          const titleText = line.replace('# ', '');
          pdf.text(titleText, margin, yPosition);
          yPosition += 8;
          
          // Ligne sous le titre
          pdf.setDrawColor(200, 200, 200);
          pdf.setLineWidth(0.3);
          pdf.line(margin, yPosition, margin + 80, yPosition);
          yPosition += 6;
        }
        // Style sous-titre
        else if (line.startsWith('## ')) {
          pdf.setFontSize(12);
          pdf.setFont(undefined, 'bold');
          pdf.setTextColor(70, 130, 180);
          const titleText = line.replace('## ', '');
          pdf.text(titleText, margin, yPosition);
          yPosition += 6;
        }
        // Style sous-sous-titre
        else if (line.startsWith('### ')) {
          pdf.setFontSize(11);
          pdf.setFont(undefined, 'bold');
          pdf.setTextColor(100, 100, 100);
          const titleText = line.replace('### ', '');
          pdf.text(titleText, margin, yPosition);
          yPosition += 5;
        }
      }
      // Formatage du texte normal
      else {
        pdf.setFontSize(10);
        pdf.setFont(undefined, 'normal');
        pdf.setTextColor(0, 0, 0);
        
        // Découpage du texte pour les longues lignes
        const wrappedLines = pdf.splitTextToSize(line, maxWidth);
        
        for (let j = 0; j < wrappedLines.length; j++) {
          if (yPosition > pageHeight - 40) {
            pdf.addPage();
            
            // Mini en-tête sur nouvelles pages
            pdf.setFillColor(41, 128, 185);
            pdf.rect(0, 0, pageWidth, 20, 'F');
            pdf.setTextColor(255, 255, 255);
            pdf.setFontSize(10);
            pdf.setFont(undefined, 'bold');
            pdf.text(scenario.name, margin, 12);
            
            yPosition = 35;
          }
          
          pdf.setTextColor(0, 0, 0);
          pdf.text(wrappedLines[j], margin, yPosition);
          yPosition += 5;
        }
      }
    }
    
    // === PIED DE PAGE ===
    const totalPages = pdf.internal.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      pdf.setPage(i);
      
      // Ligne de séparation
      pdf.setDrawColor(200, 200, 200);
      pdf.setLineWidth(0.3);
      pdf.line(margin, pageHeight - 20, pageWidth - margin, pageHeight - 20);
      
      // Numéro de page
      pdf.setFontSize(8);
      pdf.setFont(undefined, 'normal');
      pdf.setTextColor(150, 150, 150);
      pdf.text(`Page ${i} sur ${totalPages}`, pageWidth - margin - 20, pageHeight - 10);
      
      // Signature SIFHR
      pdf.text('SIFHR - Système Intelligent de Formation Historique RAG', margin, pageHeight - 10);
    }
    
    // Télécharger le PDF
    pdf.save(`${scenario.name}.pdf`);
  };
  
  const viewScenario = (scenario: ScenarioPdf) => {
    setViewingScenario(scenario);
  };

  // Load scenarios from localStorage on startup
  useEffect(() => {
    const savedScenarios = localStorage.getItem('sifhr-scenarios');
    if (savedScenarios) {
      try {
        const parsed = JSON.parse(savedScenarios);
        const scenariosWithDates = parsed.map((s: any) => ({
          ...s,
          createdAt: new Date(s.createdAt)
        }));
        setScenarios(scenariosWithDates);
      } catch (error) {
        console.error('Error loading scenarios:', error);
      }
    }
  }, []);

  return (
    <div className="app">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <button className="toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <MessageSquare size={24} />
          </button>
          <h2>SIFHR WebSocket</h2>
        </div>

        {/* WebSocket Status */}
        <div style={{
          padding: '10px 15px',
          margin: '10px',
          borderRadius: '8px',
          fontSize: '0.9em',
          textAlign: 'center',
          backgroundColor: wsConnected ? '#d1fae5' : '#fee2e2',
          color: wsConnected ? '#065f46' : '#991b1b',
          border: `1px solid ${wsConnected ? '#a7f3d0' : '#fca5a5'}`
        }}>
          Status: {wsStatus}
          <br />
          <button 
            onClick={wsConnected ? disconnectWebSocket : connectWebSocket}
            style={{
              marginTop: '5px',
              padding: '4px 8px',
              fontSize: '0.8em',
              borderRadius: '4px',
              border: 'none',
              backgroundColor: wsConnected ? '#ef4444' : '#10b981',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            {wsConnected ? 'Disconnect' : 'Connect'}
          </button>
        </div>

        <div className="sidebar-tabs">
          <button 
            className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={16} />
            Chat
          </button>
          <button 
            className={`tab-button ${activeTab === 'library' ? 'active' : ''}`}
            onClick={() => setActiveTab('library')}
          >
            <BookOpen size={16} />
            Bibliothèque
          </button>
        </div>

        <div className="sidebar-content">
          {activeTab === 'chat' && (
            <>
              <button className="new-chat-btn" onClick={newChat}>
                <MessageSquare size={16} />
                Nouveau
              </button>

              <div className="sessions-section">
                <div className="sessions-list">
                  {sessions.map(session => (
                    <div 
                      key={session.id}
                      className={`session-item ${currentSessionId === session.id ? 'active' : ''}`}
                      onClick={() => loadSession(session.id)}
                    >
                      <div className="session-name">{session.name}</div>
                      <button 
                        className="delete-session"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.id);
                        }}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {activeTab === 'library' && (
            <div className="library-section">
              <div className="library-info">
                <p>{scenarios.length} scenario(s)</p>
                <p>Consultez la zone principale →</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        {activeTab === 'chat' && (
          <>
            <div className="chat-header">
              <h1>Guide Narratif WebSocket</h1>
              <p>Communication temps réel avec le système RAG agentique</p>
            </div>

            <div className="messages-container">
              {messages.length === 0 && (
                <div className="welcome-message">
                  <h3>Bienvenue dans l'univers SIFHR WebSocket</h3>
                  <p>Communication en temps réel avec le système RAG agentique</p>
                  <div className="example-questions">
                    <h4>Exemples de questions :</h4>
                    <ul>
                      <li>"Crée un scénario de chasse au trésor dans Bagdad"</li>
                      <li>"Parle-moi des trésors de Haroun al-Rachid"</li>
                      <li>"Décris l'architecture de Cordoue au Xe siècle"</li>
                      <li>"Test WebSocket rapide"</li>
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
                        <h5>Sources utilisées :</h5>
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

              {isStreaming && streamingMessage && (
                <div className="message bot streaming">
                  <div className="message-content">
                    <div className="message-text">
                      {streamingMessage.split('\n').map((line, index) => (
                        <React.Fragment key={index}>
                          {line}
                          {index < streamingMessage.split('\n').length - 1 && <br />}
                        </React.Fragment>
                      ))}
                    </div>
                    <div className="streaming-indicator">
                      <span>En cours de génération...</span>
                      <div className="streaming-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {isLoading && (
                <div className="message bot loading">
                  <div className="message-content">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <p>L'agent traite votre demande via WebSocket...</p>
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
                  disabled={isLoading || !wsConnected}
                  rows={1}
                />
                <button 
                  onClick={sendMessage} 
                  disabled={isLoading || !inputText.trim() || !wsConnected}
                  className="send-btn"
                >
                  <Send size={20} />
                </button>
              </div>
            </div>
          </>
        )}

        {activeTab === 'library' && (
          <div className="library-page">
            <div className="library-header">
              <h1>Bibliothèque de Scénarios WebSocket</h1>
              <p>Collection de vos scénarios générés via WebSocket</p>
            </div>
            
            <div className="library-main-content">
              {scenarios.length === 0 ? (
                <div className="empty-library">
                  <FileText size={64} />
                  <h3>Aucun scénario disponible</h3>
                  <p>Commencez une conversation WebSocket pour générer vos premiers scénarios !</p>
                </div>
              ) : (
                <div className="scenarios-grid">
                  {scenarios.map(scenario => (
                    <div key={scenario.id} className="scenario-card">
                      <div className="scenario-card-header">
                        <FileText size={24} />
                        <h3>{scenario.name}</h3>
                      </div>
                      <div className="scenario-preview">
                        <p>{scenario.content.substring(0, 200)}...</p>
                      </div>
                      <div className="scenario-card-footer">
                        <span className="scenario-date">
                          {scenario.createdAt.toLocaleDateString('fr-FR')}
                        </span>
                        <div className="scenario-actions">
                          <button 
                            className="view-btn"
                            onClick={() => viewScenario(scenario)}
                            title="Voir le scénario complet"
                          >
                            <Eye size={16} />
                            Voir
                          </button>
                          <button 
                            className="download-btn"
                            onClick={() => downloadScenario(scenario)}
                            title="Télécharger TXT"
                          >
                            <Download size={16} />
                            TXT
                          </button>
                          <button 
                            className="download-btn pdf"
                            onClick={() => downloadScenarioPDF(scenario)}
                            title="Télécharger PDF"
                          >
                            <Download size={16} />
                            PDF
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modal for viewing scenarios */}
      {viewingScenario && (
        <div className="scenario-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h2>{viewingScenario.name}</h2>
              <button 
                className="close-modal"
                onClick={() => setViewingScenario(null)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="scenario-text">
                {viewingScenario.content.split('\n').map((line, index) => (
                  <React.Fragment key={index}>
                    {line}
                    {index < viewingScenario.content.split('\n').length - 1 && <br />}
                  </React.Fragment>
                ))}
              </div>
            </div>
            <div className="modal-footer">
              <button 
                className="download-from-modal-btn"
                onClick={() => {
                  downloadScenario(viewingScenario);
                  setViewingScenario(null);
                }}
              >
                <Download size={16} />
                Télécharger TXT
              </button>
              <button 
                className="download-from-modal-btn pdf"
                onClick={() => {
                  downloadScenarioPDF(viewingScenario);
                  setViewingScenario(null);
                }}
              >
                <Download size={16} />
                Télécharger PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;