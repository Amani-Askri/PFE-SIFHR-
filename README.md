# SIFHR - Guide Narratif du Monde Arabo-Musulman

## Description
SIFHR est un système RAG (Retrieval-Augmented Generation) intelligent utilisant des agents ReAct pour créer des scénarios immersifs de chasse au trésor basés sur la civilisation arabo-musulmane. Le système combine une interface web moderne avec un backend API puissant alimenté par l'IA.

## Architecture
- **Backend**: FastAPI avec système d'agents RAG utilisant LangChain et Google Gemini
- **Frontend**: React TypeScript avec Vite
- **Base de données**: Milvus pour les embeddings vectoriels
- **Modèle LLM**: Google Gemini (gemini-2.0-flash-exp)

## Structure du Projet
```
PFE-SIFHR-/
├── backend/
│   ├── main.py              # API FastAPI principale
│   ├── requirements.txt     # Dépendances Python
│   └── config.py           # Configuration API
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # Interface React principale
│   │   └── App.css         # Styles avec thème arabo-musulman
│   ├── package.json        # Dépendances Node.js
│   └── vite.config.ts      # Configuration Vite
├── SIFHR/
│   └── agentic_ReAct.py    # Système d'agent ReAct original
├── start_backend.bat       # Script de démarrage backend
├── start_frontend.bat      # Script de démarrage frontend
└── README.md
```

## Installation

### Prérequis
- Python 3.8+
- Node.js 18+
- Milvus (base de données vectorielle)

### Backend
1. Créer et activer l'environnement virtuel :
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer les variables d'environnement dans `config.py` :
```python
GOOGLE_API_KEY = "AIzaSyAqp2tKpS-hN_aNgg4I5IMM6FRM4B5vL5o"
MODEL_NAME = "gemini-2.0-flash-exp"
```

### Frontend
1. Installer les dépendances :
```bash
cd frontend
npm install
```

## Démarrage

### Option 1: Scripts automatisés
- Double-cliquer sur `start_backend.bat` pour démarrer l'API
- Double-cliquer sur `start_frontend.bat` pour démarrer l'interface web

### Option 2: Manuel
1. Démarrer le backend :
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Démarrer le frontend :
```bash
cd frontend
npm run dev
```

## Utilisation

1. Ouvrir le navigateur à `http://localhost:5173`
2. Interagir avec l'agent via l'interface de chat
3. Explorer les fonctionnalités :
   - Création de scénarios immersifs
   - Consultation de sources historiques
   - Gestion des sessions de conversation

## Fonctionnalités

### Système d'Agent ReAct
- **Raisonnement**: L'agent analyse les questions et planifie ses actions
- **Récupération**: Recherche dans la base de connaissances Milvus
- **Génération**: Création de réponses contextuelles avec Google Gemini

### Interface Web
- Sidebar avec gestion des sessions
- Affichage des sources consultées
- Interface responsive avec thème culturel
- Support des conversations multi-tours

### API Endpoints
- `POST /chat`: Envoi de messages à l'agent
- `GET /sessions`: Récupération des sessions
- `DELETE /chat/{session_id}`: Suppression de session
- `GET /health`: Vérification de l'état du système

## Exemples de Questions
- "Crée un scénario de chasse au trésor dans Bagdad"
- "Parle-moi des trésors de Haroun al-Rachid"
- "Décris l'architecture de Cordoue au Xe siècle"
- "Qu'est-ce que SIFHR ?"

## Dépannage

### Erreur 429 (Rate Limiting)
Le système est configuré pour utiliser Google Gemini. Si vous rencontrez des limitations, vérifiez votre quota API.

### Problèmes de connexion Milvus
Assurez-vous que Milvus est démarré et accessible sur le port par défaut (19530).

### Problèmes d'encodage
Le système gère automatiquement l'encodage UTF-8 pour les caractères arabes et les emojis.

## Développement

### Ajout de nouvelles fonctionnalités
1. Backend : Modifier `main.py` pour ajouter de nouveaux endpoints
2. Frontend : Étendre `App.tsx` avec de nouveaux composants
3. Agent : Personnaliser `agentic_ReAct.py` pour de nouveaux comportements

### Tests
```bash
# Backend
cd backend
python -m pytest

# Frontend  
cd frontend
npm test
```

## Support
Pour toute question ou problème, consultez la documentation du système d'agent ReAct original dans le dossier `SIFHR/`.
