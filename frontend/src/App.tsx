import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageSquare, History, Trash2, Settings, BookOpen, Download, FileText, Eye } from 'lucide-react';
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

interface SavedScenario {
  id: string;
  title: string;
  content: string;
  createdAt: string;
  pdfData: string;
}

interface SimilarityResult {
  has_duplicates: boolean;
  similarities: Array<{
    scenario: any;
    similarity_score: number;
    is_duplicate: boolean;
    similarity_type: string;
  }>;
  high_similarities: Array<any>;
  similarity_threshold: number;
  can_auto_embed: boolean;
  message: string;
  pdf_data: string;
  pdf_filename: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioPdf[]>([]);
  const [savedScenarios, setSavedScenarios] = useState<SavedScenario[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<'chat' | 'library'>('chat');
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [pdfNotification, setPdfNotification] = useState<string | null>(null);
  const [viewingScenario, setViewingScenario] = useState<ScenarioPdf | null>(null);
  const [similarityResult, setSimilarityResult] = useState<SimilarityResult | null>(null);
  const [showSimilarityPopup, setShowSimilarityPopup] = useState(false);
  const [currentScenarioData, setCurrentScenarioData] = useState<{content: string, title: string} | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Constante API
  const API_BASE_URL = 'http://localhost:8001';

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
      const response = await fetch(`${API_BASE_URL}/chat`, {
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
      
      // Auto-sauvegarder en PDF si c'est un scénario de chasse au trésor
      const isScenario = botMessage.text.toLowerCase().includes('scénario') || 
                        botMessage.text.toLowerCase().includes('chasse au trésor') ||
                        botMessage.text.toLowerCase().includes('quête') ||
                        botMessage.text.includes('##');
      
      if (isScenario) {
        // Afficher une notification d'auto-sauvegarde
        setPdfNotification('Scénario détecté ! Téléchargement automatique en cours...');
        
        // Attendre un peu pour que le message soit affiché
        setTimeout(() => {
          generatePdf(botMessage).then(() => {
            setPdfNotification('PDF sauvegarde automatiquement dans la bibliotheque !');
            setTimeout(() => setPdfNotification(null), 4000);
          });
        }, 1000);
      }
      
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
      await fetch(`${API_BASE_URL}/chat/${sessionId}`, {
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

  const checkSimilarity = async (content: string, title: string): Promise<SimilarityResult> => {
    const response = await fetch(`${API_BASE_URL}/check-similarity`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        scenario_content: content,
        scenario_title: title
      }),
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    return await response.json();
  };

  const downloadPdfFromBase64 = (base64Data: string, filename: string) => {
    try {
      // Convertir base64 en blob
      const binaryString = window.atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/pdf' });

      // Créer le lien de téléchargement
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erreur lors du téléchargement PDF:', error);
      alert('Erreur lors du téléchargement du PDF');
    }
  };

  const generatePdf = async (messageToSave?: Message) => {
    const botMessage = messageToSave || messages.filter(m => !m.isUser).pop();
    
    if (!botMessage) {
      if (!messageToSave) {
        alert('Aucun scénario à télécharger. Générez d\'abord un scénario !');
      }
      return;
    }

    setIsGeneratingPdf(true);
    try {
      const scenarioName = extractScenarioTitle(botMessage.text) || `Scenario_${Date.now()}`;
      
      // Vérifier la similarité et générer le PDF automatiquement
      console.log('Verification de similarite en cours...');
      const result = await checkSimilarity(botMessage.text, scenarioName);
      
      // Stocker les données pour la popup
      setCurrentScenarioData({ content: botMessage.text, title: scenarioName });
      setSimilarityResult(result);
      
      if (result.can_auto_embed) {
        // Pas de doublon détecté - téléchargement automatique
        downloadPdfFromBase64(result.pdf_data, result.pdf_filename);
        
        // Sauvegarder dans la bibliothèque
        const newScenario: ScenarioPdf = {
          id: Date.now().toString(),
          name: scenarioName,
          content: botMessage.text,
          createdAt: new Date()
        };

        setScenarios(prev => [newScenario, ...prev]);
        localStorage.setItem('sifhr-scenarios', JSON.stringify([newScenario, ...scenarios]));
        
        if (!messageToSave) {
          setPdfNotification(`✅ Scénario "${scenarioName}" sauvegardé automatiquement !`);
          setTimeout(() => setPdfNotification(null), 4000);
        }
      } else {
        // Afficher la popup de validation
        setShowSimilarityPopup(true);
      }

    } catch (error) {
      console.error('Erreur lors de la vérification de similarité:', error);
      if (!messageToSave) {
        alert('Erreur lors de la vérification de similarité');
      }
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  const formatTextToHtml = (text: string): string => {
    return text
      // Gérer les emojis en les entourant d'une classe spéciale
      .replace(/([\u{1F300}-\u{1F6FF}]|[\u{1F900}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}])/gu, '<span class="emoji">$1</span>')
      // Gérer les titres
      .replace(/# (.*)/g, '<h1>$1</h1>')
      .replace(/## (.*)/g, '<h2>$1</h2>')
      .replace(/### (.*)/g, '<h3>$1</h3>')
      // Gérer le formatage
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Gérer les paragraphes
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
      .replace(/^/, '<p>')
      .replace(/$/, '</p>');
  };

  const createAndDownloadPdf = async (htmlContent: string, fileName: string): Promise<void> => {
    try {
      // Créer automatiquement un lien de téléchargement
      const styledContent = `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <title>${fileName}</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>
              @page {
                margin: 2cm;
                size: A4;
              }
              
              * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
              }
              
              body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.7;
                color: #2c3e50;
                background: linear-gradient(135deg, #f8fbff 0%, #e6f3ff 100%);
                padding: 20px;
              }
              
              .header {
                text-align: center;
                padding: 40px 20px;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #4682b4 100%);
                color: white;
                border-radius: 15px;
                margin-bottom: 40px;
                box-shadow: 0 8px 25px rgba(30, 60, 114, 0.3);
              }
              
              .header h1 {
                font-size: 2.5em;
                font-weight: 700;
                margin-bottom: 15px;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
              }
              
              .header .subtitle {
                font-size: 1.2em;
                font-weight: 500;
                opacity: 0.9;
                margin-bottom: 10px;
              }
              
              .header .date {
                font-size: 0.95em;
                opacity: 0.8;
                font-weight: 400;
              }
              
              .content {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
              }
              
              h1 {
                color: #1e3c72;
                font-size: 2.2em;
                font-weight: 700;
                margin: 30px 0 20px 0;
                border-bottom: 3px solid #4682b4;
                padding-bottom: 10px;
                text-align: center;
              }
              
              h2 {
                color: #2a5298;
                font-size: 1.6em;
                font-weight: 600;
                margin: 25px 0 15px 0;
                border-left: 4px solid #4682b4;
                padding-left: 15px;
              }
              
              h3 {
                color: #4682b4;
                font-size: 1.3em;
                font-weight: 600;
                margin: 20px 0 10px 0;
              }
              
              p {
                margin: 12px 0;
                text-align: justify;
                font-size: 1.05em;
              }
              
              strong {
                color: #1e3c72;
                font-weight: 600;
              }
              
              em {
                color: #2a5298;
                font-style: italic;
              }
              
              .emoji {
                font-size: 1.3em;
                margin: 0 5px;
              }
              
              .footer {
                margin-top: 50px;
                padding: 30px;
                background: linear-gradient(135deg, #f8fbff 0%, #e6f3ff 100%);
                border-radius: 15px;
                text-align: center;
                border: 2px solid #4682b4;
              }
              
              .footer p {
                color: #4682b4;
                font-style: italic;
                margin: 8px 0;
              }
              
              .footer strong {
                color: #1e3c72;
                font-weight: 700;
                font-size: 1.1em;
              }
              
              @media print {
                body {
                  background: white !important;
                }
                .header {
                  background: linear-gradient(135deg, #1e3c72 0%, #4682b4 100%) !important;
                  -webkit-print-color-adjust: exact;
                  print-color-adjust: exact;
                }
              }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>SCENARIO SIFHR</h1>
              <div class="subtitle">Système Immersif de Fiction Historique Riche</div>
              <div class="date">Généré le ${new Date().toLocaleDateString('fr-FR')} à ${new Date().toLocaleTimeString('fr-FR')}</div>
            </div>
            
            <div class="content">
              ${htmlContent.replace(/([\u{1F300}-\u{1F6FF}]|[\u{1F900}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}])/gu, '<span class="emoji">$1</span>')}
            </div>
            
            <div class="footer">
              <p><em>Scénario généré par l'IA Claude Sonnet 4 basé sur des documents historiques authentiques</em></p>
              <p><strong>SIFHR © ${new Date().getFullYear()}</strong></p>
            </div>
          </body>
          </html>
        `;
        
        // Créer un blob et télécharger automatiquement
        const blob = new Blob([styledContent], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${fileName}.html`;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        // Aussi ouvrir l'aperçu pour impression si souhaité
        const printWindow = window.open('', '_blank');
        if (printWindow) {
          printWindow.document.write(styledContent);
          printWindow.document.close();
          setTimeout(() => {
            printWindow.print();
          }, 1000);
        }
    } catch (error) {
      console.error('Erreur lors de la création du PDF:', error);
      alert('Erreur lors de la génération du PDF');
    }
  };

  const extractScenarioTitle = (text: string): string => {
    // Extraire le titre depuis le texte (recherche de # ou ** au début)
    const lines = text.split('\n');
    for (const line of lines) {
      const cleaned = line.replace(/[#*\s]/g, '');
      if (cleaned.length > 5 && cleaned.length < 50) {
        return cleaned.replace(/[^\w\s-]/g, '').trim();
      }
    }
    return `Scenario_${new Date().toLocaleDateString('fr-FR').replace(/\//g, '-')}`;
  };

  const downloadScenario = async (scenario: ScenarioPdf) => {
    try {
      // Créer le contenu HTML formaté avec thème bleu amélioré
      const htmlContent = formatTextToHtml(scenario.content);
      await createAndDownloadPdf(htmlContent, scenario.name);
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
      alert('Erreur lors du téléchargement du scénario');
    }
  };
  
  const viewScenario = (scenario: ScenarioPdf) => {
    setViewingScenario(scenario);
  };

  // Charger les scénarios depuis localStorage au démarrage
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
        console.error('Erreur lors du chargement des scénarios:', error);
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
          <h2>SIFHR Assistant</h2>
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
              <h1>Guide Narratif du Monde Arabo-Musulman</h1>
              <p>Créez des scénarios immersifs de chasse au trésor</p>
            </div>

        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h3>Bienvenue dans l'univers SIFHR</h3>
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
                    <h5>Sources utilisees :</h5>
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
          {pdfNotification && (
            <div className="pdf-notification">
              {pdfNotification}
            </div>
          )}
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
          </>
        )}

        {activeTab === 'library' && (
          <div className="library-page">
            <div className="library-header">
              <h1>Bibliotheque de Scenarios</h1>
              <p>Collection de vos scénarios de chasse au trésor arabo-musulmans</p>
              <button 
                className="generate-pdf-btn main-generate-btn" 
                onClick={() => generatePdf()}
                disabled={isGeneratingPdf || messages.length === 0 || !messages.some(m => !m.isUser)}
              >
                <FileText size={16} />
                {isGeneratingPdf ? 'Génération...' : 'Générer un Nouveau PDF'}
              </button>
            </div>
            
            <div className="library-main-content">
              {scenarios.length === 0 ? (
                <div className="empty-library">
                  <FileText size={64} />
                  <h3>Aucun scénario disponible</h3>
                  <p>Commencez une conversation pour générer vos premiers scénarios PDF !</p>
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

      {/* Modale de visualisation */}
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
                Télécharger PDF
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Similarity Popup */}
      {showSimilarityPopup && similarityResult && (
        <div className="modal-overlay">
          <div className="modal-content similarity-modal">
            <div className="modal-header">
              <h3>⚠️ Scénarios similaires détectés</h3>
              <button 
                className="close-modal"
                onClick={() => {
                  setShowSimilarityPopup(false);
                  setSimilarityResult(null);
                  setCurrentScenarioData(null);
                }}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="similarity-info">
                <p><strong>Seuil de similarité :</strong> {similarityResult.similarity_threshold}</p>
                <p><strong>Scénarios similaires trouvés :</strong> {similarityResult.high_similarities?.length || 0}</p>
              </div>
              
              {similarityResult.similarities && similarityResult.similarities.length > 0 && (
                <div className="similarities-list">
                  <h4>Détails des similarités :</h4>
                  {similarityResult.similarities.slice(0, 5).map((sim, index) => (
                    <div key={index} className="similarity-item">
                      <div className="similarity-score">
                        <span className={`score ${sim.similarity_score >= similarityResult.similarity_threshold ? 'high' : 'low'}`}>
                          {(sim.similarity_score * 100).toFixed(1)}%
                        </span>
                        <span className="similarity-type">
                          {sim.similarity_type === 'exact_duplicate' ? 'Doublon exact' : 'Similarite semantique'}
                        </span>
                      </div>
                      <div className="scenario-preview">
                        {sim.scenario.content.substring(0, 150)}...
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button 
                className="cancel-btn"
                onClick={() => {
                  setShowSimilarityPopup(false);
                  setSimilarityResult(null);
                  setCurrentScenarioData(null);
                }}
              >
                Annuler
              </button>
              <button 
                className="force-save-btn"
                onClick={async () => {
                  if (currentScenarioData && similarityResult?.pdf_data && similarityResult?.pdf_filename) {
                    // Télécharger le PDF malgré la similarité
                    downloadPdfFromBase64(similarityResult.pdf_data, similarityResult.pdf_filename);
                    
                    // Sauvegarder dans la bibliothèque locale
                    const newScenario: SavedScenario = {
                      id: Date.now().toString(),
                      title: currentScenarioData.title,
                      content: currentScenarioData.content,
                      createdAt: new Date().toISOString(),
                      pdfData: similarityResult.pdf_data
                    };
                    
                    const existingScenarios = JSON.parse(localStorage.getItem('sifhr-scenarios') || '[]');
                    existingScenarios.unshift(newScenario);
                    localStorage.setItem('sifhr-scenarios', JSON.stringify(existingScenarios));
                    setSavedScenarios(existingScenarios);
                    
                    // Faire l'embedding forcé
                    try {
                      await fetch(`${API_BASE_URL}/embed-scenario`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          content: currentScenarioData.content,
                          title: currentScenarioData.title,
                          force_embed: true
                        })
                      });
                    } catch (error) {
                      console.error('Erreur embedding forcé:', error);
                    }
                    
                    setShowSimilarityPopup(false);
                    setSimilarityResult(null);
                    setCurrentScenarioData(null);
                  }
                }}
              >
                Forcer la sauvegarde
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
