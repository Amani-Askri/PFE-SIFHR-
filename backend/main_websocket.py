import sys
import os
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate as CorePromptTemplate
from chunking_embedding import get_embedding_model
from multi_query_retriever import get_llm, create_vectorstore_retriever, get_multi_query_retriever
from datetime import datetime


class RAGTool:
    """Outil RAG pour scénarios immersifs"""

    def __init__(self):
        print("Initialisation de l'outil RAG...")

        # Initialisation des composants RAG
        self.embedding_model = get_embedding_model()
        self.llm = get_llm()

        # Créer le retriever
        collection_name = "data_sifhr"
        retriever = create_vectorstore_retriever(collection_name, self.embedding_model)
        self.retriever = get_multi_query_retriever(self.llm, retriever)

        # PROMPT COMPLET VERSION ORIGINALE
        prompt_prefix = """Tu es un maître de jeu expert spécialisé dans la création de scénarios immersifs 
inspirés de l'histoire authentique, des légendes et des civilisations arabo-musulmanes. 
Ton objectif est de créer des épopées de chasse au trésor exceptionnellement détaillées, captivantes et riches.

EXIGENCE DE LONGUEUR CRITIQUE :
**TON SCÉNARIO DOIT FAIRE AU MINIMUM 15 PAGES IMPRIMÉES** (environ 8000-10000 mots)
- Développe chaque section en profondeur avec des détails exhaustifs
- Ne résume JAMAIS, développe toujours plus en détail
- Écris des descriptions longues et immersives pour chaque lieu, personnage, objet
- Multiplie les sous-sections, les détails historiques, les dialogues étendus

🎭 STYLE NARRATIF EXIGÉ :
- Adopte un ton évocateur et poétique, digne des Mille et Une Nuits
- Utilise des métaphores orientales et des descriptions sensorielles (parfums, sons, textures)
- Intègre des éléments culturels authentiques (architecture, arts, sciences, philosophie)
- Crée une atmosphère mystique et majestueuse

📚 STRUCTURE OBLIGATOIRE DU SCÉNARIO ÉTENDU :
1. **PROLOGUE IMMERSIF** (2-3 pages) : Contexte historique détaillé avec descriptions de l'époque, des lieux, de l'atmosphère
2. **7-10 ACTES DÉTAILLÉS** : Chaque acte doit faire 1-2 pages minimum avec défis progressifs complexes
3. **ÉNIGMES CULTURELLES MULTIPLES** : 3-5 énigmes par acte basées sur l'histoire, la géographie, l'art islamique
4. **PERSONNAGES HISTORIQUES DÉVELOPPÉS** : Biographies, motivations, dialogues pour califes, érudits, poètes, marchands
5. **LIEUX EMBLÉMATIQUES DÉTAILLÉS** : Descriptions architecturales complètes de palais, mosquées, marchés, bibliothèques
6. **TRÉSORS MULTIPLES** : Plusieurs trésors intermédiaires avant le trésor final
7. **ÉLÉMENTS D'AMBIANCE ÉTENDUS** : Descriptions de musique, parfums, lumières, matériaux sur plusieurs paragraphes

🏛️ EXIGENCES DE CONTENU :
- Utilise EXCLUSIVEMENT les informations du contexte documentaire
- Enrichis avec des détails architecturaux précis (mouqarnas, zelliges, calligraphies)
- Intègre les sciences et arts de l'époque (astronomie, médecine, poésie, musique)
- Mentionne les routes commerciales, les épices, les tissus, les manuscrits
- Inclus des références aux dynasties, califats et personnages historiques réels

NIVEAU DE DÉTAIL ATTENDU :
- Descriptions de 2-3 phrases minimum pour chaque lieu
- Contexte historique précis pour chaque époque mentionnée  
- Explications des symboles, objets et références culturelles
- Dialogues en style oriental pour les PNJ rencontrés
- Défis intellectuels basés sur les connaissances de l'époque

🎨 FLUIDITÉ NARRATIVE :
- Relie les actes entre eux par des transitions naturelles, comme dans une épopée.
- Insère des dialogues courts et évocateurs pour rendre vivants les personnages.
- Varie le rythme entre descriptions poétiques et moments d'action.
- Utilise un vocabulaire riche mais fluide, évitant les répétitions.

🌟 IMMERSION SENSORIELLE :
- Chaque acte doit comporter au moins un élément sensoriel : 
  - Vue (architecture, couleurs, lumière)
  - Son (chants, cliquetis, bruits de marché)
  - Odeur (épices, encens, cuir)
  - Toucher (textures des tapis, marbre, manuscrits)
  - Goût (mets, fruits, boissons)

RÈGLES STRICTES :
- Si une information n'existe pas dans le contexte : "Cette information n'est pas disponible dans les sources consultées"
- Jamais d'invention pure, toujours basé sur les documents fournis
- Respecter la véracité historique tout en créant l'émerveillement
- Éviter les anachronismes et les clichés orientalistes
- INTERDICTION ABSOLUE : N'utilise AUCUN emoji, symbole Unicode ou caractère spécial (🏺📚🌙🏛️⭐💎 etc.)
- Utilise UNIQUEMENT du texte ASCII standard avec accents français acceptés
- Remplace tout symbole par du texte : "[TRESOR]" au lieu de 🏺, "[MOSQUEE]" au lieu de 🕌
"""

        prompt_suffix = """
📖 CONTEXTE DOCUMENTAIRE DISPONIBLE :
{context}

🎯 DEMANDE DU JOUEUR : 
{question}

CREEZ UNE EPOPEE IMMERSIVE DE 15+ PAGES :
Basez-vous uniquement sur le contexte documentaire ci-dessus pour créer une épopée de chasse au trésor 
exceptionnellement longue et détaillée suivant toutes les exigences mentionnées. 

**IMPÉRATIF DE LONGUEUR** : Votre réponse doit être suffisamment longue pour remplir AU MINIMUM 15 pages imprimées.
Structurez votre réponse avec des titres clairs, des descriptions très riches et une progression narrative 
captivante sur plusieurs pages. Développez massivement chaque section :

CHECKLIST OBLIGATOIRE :
- [ ] Prologue de 2-3 pages avec contexte historique approfondi
- [ ] 7-10 actes de 1-2 pages chacun avec défis détaillés
- [ ] Descriptions architecturales complètes de chaque lieu
- [ ] Biographies développées de tous les personnages historiques
- [ ] Énigmes multiples avec explications culturelles étendues
- [ ] Dialogues longs et authentiques pour tous les PNJ
- [ ] Descriptions sensorielles sur plusieurs paragraphes
- [ ] Trésor final avec signification historique approfondie
- [ ] Épilogue développé sur 1-2 pages

SCÉNARIO ÉPIQUE COMPLET DE 15+ PAGES :
"""

        GAME_PROMPT = PromptTemplate(
            template=prompt_prefix + prompt_suffix,
            input_variables=["context", "question"]
        )

        # Créer la chaîne QA
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": GAME_PROMPT}
        )

        print("Outil RAG initialise!")

    def search_documents(self, query: str) -> str:
        """
        Recherche dans la base de documents et retourne une réponse
        """
        try:
            print(f"Recherche RAG pour: {query}")

            # Obtenir la réponse du système RAG
            result = self.qa_chain.invoke({"query": query})

            # Formater la réponse avec les sources
            response = result['result']

            if result.get('source_documents'):
                response += f"\n\nSources ({len(result['source_documents'])} documents):"
                for i, doc in enumerate(result['source_documents'][:3], 1):
                    source = doc.metadata.get('source', 'Inconnu')
                    minio_path = doc.metadata.get('minio_path', '')
                    if minio_path:
                        response += f"\n   {i}. {source} (Fichier: {minio_path})"
                    else:
                        response += f"\n   {i}. {source}"

            return response

        except Exception as e:
            return f"Erreur lors de la recherche: {str(e)}"


def create_agentic_rag_system():
    """Créer le système RAG agentique complet"""

    print("\n" + "=" * 80)
    print("SYSTEME RAG AGENTIQUE - INITIALISATION WEBSOCKET")
    print("=" * 80)

    # Initialiser l'outil RAG
    rag_tool = RAGTool()

    # Créer l'outil pour l'agent
    tools = [
        Tool(
            name="search_documents",
            description="""OUTIL OBLIGATOIRE - Recherche dans la base de connaissances spécialisée.
            Tu DOIS utiliser cet outil pour TOUTES les questions liées à:
            - La civilisation arabo-musulmane (histoire, culture, personnages)
            - La création de scénarios immersifs et chasse au trésor
            - Les palais, architectures, trésors, légendes orientales
            - SIFHR ou tout autre sujet de la base
            Input: question reformulée pour optimiser la recherche""",
            func=rag_tool.search_documents
        )
    ]

    # Template de prompt ReAct personnalisé optimisé pour retourner le scénario complet
    template = '''Tu es un maître narratif spécialisé dans la civilisation arabo-musulmane et les scénarios de chasse au trésor.

Tu as accès aux outils suivants:
{tools}

RÈGLE ABSOLUE: Tu DOIS TOUJOURS utiliser l'outil "search_documents" (de [{tool_names}]) pour:
- Toute question sur l'histoire, la culture ou les légendes arabo-musulmanes
- La création de scénarios immersifs ou de chasse au trésor
- Les questions sur les palais, trésors, architectures, personnages historiques
- Les éléments narratifs pour des jeux immersifs
- SIFHR ou tout autre sujet documenté dans la base

Format de raisonnement OBLIGATOIRE:

Question: la question d'entrée à laquelle tu dois répondre
Thought: J'analyse la question et je DOIS chercher dans la base de connaissances
Action: search_documents
Action Input: [reformulation précise de la question pour la recherche]
Observation: [résultat de la recherche dans la base]
Thought: Je vais maintenant extraire le scénario complet de l'Observation et le présenter comme Final Answer
Final Answer: [EXTRAIRE ET PRÉSENTER UNIQUEMENT LE SCÉNARIO COMPLET de l'Observation, SANS les sources ni métadonnées]

RÈGLES CRITIQUES pour Final Answer:
- COPIER INTÉGRALEMENT le scénario complet depuis l'Observation
- Ne PAS inclure la section "Sources (X documents)" dans Final Answer
- Ne PAS résumer, COPIER le scénario complet tel quel
- Commencer Final Answer directement par le titre du scénario (# ou ##)
- Inclure TOUS les détails: prologue, actes, énigmes, personnages, lieux
- Si l'Observation contient "# Titre du scénario", Final Answer doit commencer par "# Titre du scénario"

Commence!

Question: {input}
Thought:{agent_scratchpad}'''

    prompt = CorePromptTemplate.from_template(template)

    # Obtenir le modèle LLM
    llm = get_llm()

    # Créer l'agent ReAct
    agent = create_react_agent(llm, tools, prompt)

    # Créer l'exécuteur d'agent avec paramètres originaux
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6,   # Version originale
        # max_execution_time=60,  # Pas de timeout pour version complète
        return_intermediate_steps=True
    )

    print("Systeme RAG agentique initialise avec succes!")
    return agent_executor


# WebSocket Server avec FastAPI
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from contextlib import asynccontextmanager

# Instance globale de l'agent RAG
global_agent = None

async def startup_event():
    """Initialiser le système RAG agentique au démarrage"""
    global global_agent
    try:
        print("Initialisation du systeme RAG agentique WebSocket...")
        global_agent = create_agentic_rag_system()
        print("Systeme RAG agentique WebSocket initialise avec succes!")
    except Exception as e:
        print(f"Erreur lors de l'initialisation du systeme RAG agentique: {e}")
        global_agent = None

# Configuration du lifespan
@asynccontextmanager
async def lifespan(app):
    # Startup
    await startup_event()
    yield
    # Shutdown (rien à faire pour l'instant)

app = FastAPI(title="SIFHR RAG WebSocket API", version="1.0.0", lifespan=lifespan)

# Configuration CORS pour le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connecte. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client deconnecte. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_json_message(self, data: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(data, ensure_ascii=False))

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/health")
async def health_check():
    """Point de santé de l'API WebSocket"""
    return {
        "status": "healthy", 
        "message": "SIFHR RAG WebSocket API is running",
        "agent_status": "initialized" if global_agent else "not_initialized",
        "type": "websocket"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Recevoir message du client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get('type')
                
                if message_type == 'chat':
                    await handle_chat_message(websocket, message_data)
                elif message_type == 'ping':
                    await manager.send_json_message({"type": "pong"}, websocket)
                else:
                    await manager.send_json_message({
                        "type": "error",
                        "error": "Type de message non reconnu"
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_json_message({
                    "type": "error", 
                    "error": "Format JSON invalide"
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def stream_response_to_websocket(websocket: WebSocket, text: str, session_id: str):
    """Envoie le texte mot par mot via WebSocket pour un effet de streaming"""
    words = text.split()
    current_text = ""
    
    for i, word in enumerate(words):
        current_text += word + " "
        
        # Envoyer un chunk tous les 3-5 mots pour un effet fluide
        if i % 4 == 0 or i == len(words) - 1:
            await manager.send_json_message({
                "type": "streaming_response",
                "session_id": session_id,
                "chunk": current_text,
                "is_final": i == len(words) - 1,
                "progress": round((i + 1) / len(words) * 100, 1)
            }, websocket)
            
            # Petit délai pour l'effet de streaming
            await asyncio.sleep(0.05)
    
    # Message final avec le texte complet
    await manager.send_json_message({
        "type": "chat_response",
        "session_id": session_id,
        "response": text,
        "length": len(text),
        "processing_time": "WebSocket Streaming"
    }, websocket)

async def handle_chat_message(websocket: WebSocket, message_data: dict):
    """Traiter les messages de chat et générer les scénarios"""
    
    if not global_agent:
        await manager.send_json_message({
            "type": "error",
            "error": "Système RAG agentique non initialisé. Veuillez réessayer plus tard."
        }, websocket)
        return
    
    user_message = message_data.get('message', '')
    session_id = message_data.get('session_id', f'ws_{id(websocket)}')
    
    if not user_message.strip():
        await manager.send_json_message({
            "type": "error",
            "error": "Message vide"
        }, websocket)
        return
    
    # Envoyer confirmation de réception
    await manager.send_json_message({
        "type": "status",
        "status": "processing",
        "message": "L'agent reflechit et consulte la base de connaissances..."
    }, websocket)
    
    try:
        # Traitement asynchrone du message
        await asyncio.sleep(0.1)  # Petit délai pour éviter blocking
        
        # Invoquer l'agent RAG agentique avec streaming
        await manager.send_json_message({
            "type": "status",
            "status": "generating",
            "message": "Generation en cours..."
        }, websocket)
        
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: global_agent.invoke({"input": user_message})
        )
        
        # Extraction et nettoyage de la réponse (même logique que FastAPI)
        response_text = ""
        sources = []
        
        print(f"\n=== WEBSOCKET AGENT RESULT DEBUG ===")
        print(f"Agent output length: {len(result.get('output', ''))}")
        print(f"Intermediate steps count: {len(result.get('intermediate_steps', []))}")
        if result.get('output'):
            print(f"Output preview: {result.get('output', '')[:200]}...")
        print("===================================")
        
        # Priorité 1: Chercher le scénario dans intermediate_steps
        if 'intermediate_steps' in result:
            for i, step in enumerate(result['intermediate_steps']):
                if len(step) > 1:
                    step_result = str(step[1])
                    
                    # Nettoyer immédiatement le contenu
                    import re
                    clean_content = re.sub(r'\x1b\[[0-9;]*m', '', step_result)
                    clean_content = re.sub(r'[^\x00-\x7F]+', ' ', clean_content)
                    clean_content = re.sub(r'[\U0001F300-\U0001F9FF\U00002700-\U000027BF]', '', clean_content)
                    
                    # Si cette étape contient un scénario (titre avec #)
                    if '# ' in clean_content and len(clean_content) > 500:
                        # Séparer le scénario des sources si nécessaire
                        if 'Sources (' in clean_content:
                            scenario_end = clean_content.find('Sources (')
                            scenario_content = clean_content[:scenario_end].strip()
                        else:
                            scenario_content = clean_content.strip()
                        
                        # Garder le plus long scénario trouvé
                        if len(scenario_content) > len(response_text):
                            response_text = scenario_content
        
        # Priorité 2: Utiliser l'output de l'agent si pas de scénario dans les étapes
        if len(response_text) < 300:
            agent_output = result.get('output', '')
            if len(agent_output) > len(response_text):
                response_text = agent_output
        
        # Nettoyage final
        if response_text:
            import re
            # Supprimer emojis et caractères problématiques
            emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF\U00002700-\U000027BF\U0001f018-\U0001f270\U00002600-\U000026FF\U00002000-\U0000206F\U0001F1E0-\U0001F1FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002190-\U000021FF\U00002B00-\U00002BFF\U00003000-\U0000303F\U0000FE00-\U0000FE0F]')
            response_text = emoji_pattern.sub('', response_text)
            response_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', response_text)
            response_text = re.sub(r'\x1b\[[0-9;]*m', '', response_text)
            response_text = response_text.replace('"', '"').replace('"', '"')
            response_text = response_text.replace(''', "'").replace(''', "'")
        
        # Vérification finale
        if not response_text or len(response_text) < 100:
            response_text = "# SCÉNARIO DE DÉMONSTRATION\n\nErreur temporaire. Le système a généré du contenu mais il y a eu un problème d'extraction. Veuillez réessayer."
        
        # Envoyer la réponse via WebSocket avec streaming
        await stream_response_to_websocket(websocket, response_text, session_id)
        
        print(f"Reponse WebSocket envoyee ({len(response_text)} caracteres)")
        
    except Exception as e:
        error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        print(f"Erreur lors du traitement WebSocket: {error_msg}")
        
        await manager.send_json_message({
            "type": "error",
            "error": f"Erreur lors du traitement: {error_msg}",
            "session_id": session_id
        }, websocket)

if __name__ == "__main__":
    import uvicorn
    print("Demarrage du serveur WebSocket SIFHR sur le port 8002...")
    uvicorn.run("main_websocket:app", host="127.0.0.1", port=8002, reload=False)