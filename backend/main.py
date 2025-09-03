from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate as CorePromptTemplate
from chunking_embedding import get_embedding_model
from multi_query_retriever import get_llm, create_vectorstore_retriever, get_multi_query_retriever


class RAGTool:
    """Outil RAG pour scénarios immersifs"""

    def __init__(self):
        print(" Initialisation de l'outil RAG...")

        # Initialisation des composants RAG
        self.embedding_model = get_embedding_model()
        self.llm = get_llm()

        # Créer le retriever
        collection_name = "data_sifhr"
        retriever = create_vectorstore_retriever(collection_name, self.embedding_model)
        self.retriever = get_multi_query_retriever(self.llm, retriever)
#PROMPT *****
        # Prompt dynamique enrichi pour scénarios immersifs
        prompt_prefix = """Tu es un maître de jeu expert spécialisé dans la création de scénarios immersifs 
inspirés de l'histoire authentique, des légendes et des civilisations arabo-musulmanes. 
Ton objectif est de créer des quêtes de chasse au trésor exceptionnellement captivantes et riches en détails.

🎭 STYLE NARRATIF EXIGÉ :
- Adopte un ton évocateur et poétique, digne des Mille et Une Nuits
- Utilise des métaphores orientales et des descriptions sensorielles (parfums, sons, textures)
- Intègre des éléments culturels authentiques (architecture, arts, sciences, philosophie)
- Crée une atmosphère mystique et majestueuse

📜 STRUCTURE OBLIGATOIRE DU SCÉNARIO :
1. **PROLOGUE IMMERSIF** : Contexte historique précis avec date et lieu
2. **ACTES MULTIPLES** : Minimum 4 actes avec défis progressifs
3. **ÉNIGMES CULTURELLES** : Basées sur l'histoire, la géographie, l'art islamique
4. **PERSONNAGES HISTORIQUES** : Califes, érudits, poètes, marchands authentiques  
5. **LIEUX EMBLÉMATIQUES** : Palais, mosquées, marchés, bibliothèques détaillés
6. **TRÉSOR FINAL** : Significatif culturellement et historiquement
7. **ÉLÉMENTS D'AMBIANCE** : Musique, parfums, lumières, matériaux

🏛️ EXIGENCES DE CONTENU :
- Utilise EXCLUSIVEMENT les informations du contexte documentaire
- Enrichis avec des détails architecturaux précis (mouqarnas, zelliges, calligraphies)
- Intègre les sciences et arts de l'époque (astronomie, médecine, poésie, musique)
- Mentionne les routes commerciales, les épices, les tissus, les manuscrits
- Inclus des références aux dynasties, califats et personnages historiques réels

💎 NIVEAU DE DÉTAIL ATTENDU :
- Descriptions de 2-3 phrases minimum pour chaque lieu
- Contexte historique précis pour chaque époque mentionnée  
- Explications des symboles, objets et références culturelles
- Dialogues en style oriental pour les PNJ rencontrés
- Défis intellectuels basés sur les connaissances de l'époque

🎨 FLUIDITÉ NARRATIVE :
- Relie les actes entre eux par des transitions naturelles, comme dans une épopée.
- Insère des dialogues courts et évocateurs pour rendre vivants les personnages.
- Varie le rythme entre descriptions poétiques et moments d’action.
- Utilise un vocabulaire riche mais fluide, évitant les répétitions.

🗺️ IMMERSION SENSORIELLE :
- Chaque acte doit comporter au moins un élément sensoriel : 
  - Vue (architecture, couleurs, lumière)
  - Son (chants, cliquetis, bruits de marché)
  - Odeur (épices, encens, cuir)
  - Toucher (textures des tapis, marbre, manuscrits)
  - Goût (mets, fruits, boissons)

⚠️ RÈGLES STRICTES :
- Si une information n'existe pas dans le contexte : "Cette information n'est pas disponible dans les sources consultées"
- Jamais d'invention pure, toujours basé sur les documents fournis
- Respecter la véracité historique tout en créant l'émerveillement
- Éviter les anachronismes et les clichés orientalistes
"""

        prompt_suffix = """
📚 CONTEXTE DOCUMENTAIRE DISPONIBLE :
{context}

🎲 DEMANDE DU JOUEUR : 
{question}

🏺 CRÉEZ UN SCÉNARIO IMMERSIF COMPLET :
Basez-vous uniquement sur le contexte documentaire ci-dessus pour créer un scénario de chasse au trésor 
exceptionnel suivant toutes les exigences mentionnées. Structurez votre réponse avec des titres clairs,
des descriptions riches et une progression narrative captivante. N'oubliez pas d'inclure tous les éléments 
demandés : prologue, actes multiples, énigmes, personnages, lieux, trésor et ambiance.

SCÉNARIO IMMERSIF ENRICHI :
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

        print(" Outil RAG initialisé!")

    def search_documents(self, query: str) -> str:
        """
        Recherche dans la base de documents et retourne une réponse
        """
        try:
            print(f" Recherche RAG pour: {query}")

            # Obtenir la réponse du système RAG
            result = self.qa_chain.invoke({"query": query})

            # Formater la réponse avec les sources
            response = result['result']

            if result.get('source_documents'):
                response += f"\n\n Sources ({len(result['source_documents'])} documents):"
                for i, doc in enumerate(result['source_documents'][:3], 1):
                    source = doc.metadata.get('source', 'Inconnu')
                    minio_path = doc.metadata.get('minio_path', '')
                    if minio_path:
                        response += f"\n   {i}. {source} ( {minio_path})"
                    else:
                        response += f"\n   {i}. {source}"

            return response

        except Exception as e:
            return f" Erreur lors de la recherche: {str(e)}"


def create_agentic_rag_system():
    """Créer le système RAG agentique"""

    print("\n" + "=" * 80)
    print("SYSTEME RAG AGENTIQUE - INITIALISATION")
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

    # Template de prompt ReAct personnalisé
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
Thought: Je vais maintenant enrichir la réponse avec ces informations
Final Answer: [réponse immersive basée sur les documents trouvés]

IMPORTANT:
- NE JAMAIS répondre directement sans consulter la base
- TOUJOURS faire plusieurs recherches si nécessaire pour enrichir le scénario
- Utiliser un style narratif immersif dans la réponse finale

Commence!

Question: {input}
Thought:{agent_scratchpad}'''

    prompt = CorePromptTemplate.from_template(template)

    # Obtenir le modèle LLM
    llm = get_llm()

    # Créer l'agent ReAct
    agent = create_react_agent(llm, tools, prompt)

    # Créer l'exécuteur d'agent
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,  # Plus d'itérations pour recherches multiples
        return_intermediate_steps=True  # Pour voir toutes les étapes
    )

    return agent_executor


def main():
    """Système interactif pour jeu immersif arabo-musulman"""

    # Créer le système agentique
    agent_executor = create_agentic_rag_system()

    print("\nGuide Narratif du Monde Arabo-Musulman pret!")
    print("Explorez l'histoire et les legendes de l'Orient")
    print("L'agent recherchera automatiquement dans la base quand necessaire")
    print("Parfait pour enrichir votre chasse au tresor immersive")
    print("\nExemples de questions:")
    print("   • 'Parle-moi des palais abbassides de Bagdad'")
    print("   • 'Quels trésors pouvait-on trouver sur la Route de la Soie?'")
    print("   • 'Décris l'architecture de Cordoue au Xe siècle'")
    print("   • 'Qui était Haroun al-Rachid et quel était son trésor?'")
    print("\n Tapez 'exit' pour quitter\n")
    print("=" * 80)

    # Historique de conversation pour le contexte
    chat_history = []

    # Boucle interactive
    while True:
        print("\n Posez votre question:")
        question = input(">>> ").strip()

        if question.lower() in ['exit', 'quit', 'q']:
            print("\n Au revoir!")
            break

        if not question:
            continue

        print("\n L'agent réfléchit...")
        print("-" * 50)

        try:
            # Préparer l'historique de chat sous forme de string
            chat_history_str = ""
            for i in range(0, len(chat_history), 2):
                if i + 1 < len(chat_history):
                    chat_history_str += f"Human: {chat_history[i]}\nAI: {chat_history[i+1]}\n"

            # Invoquer l'agent avec l'historique
            if chat_history_str:
                result = agent_executor.invoke({
                    "input": question,
                    "chat_history": chat_history_str
                })
            else:
                result = agent_executor.invoke({"input": question})

            # Afficher la réponse finale
            print("\n" + "=" * 80)
            print(" RÉPONSE FINALE:")
            print("-" * 80)
            print(result['output'])

            # Ajouter à l'historique
            chat_history.append(question)
            chat_history.append(result['output'])

            # Garder seulement les 6 derniers échanges
            if len(chat_history) > 12:
                chat_history = chat_history[-12:]

        except Exception as e:
            print(f"\n Erreur: {e}")

        print("=" * 80)


# API FastAPI pour connecter avec le frontend
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import uvicorn
from typing import List, Optional

app = FastAPI(title="SIFHR RAG API", version="1.0.0")

# Configuration CORS pour le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèles Pydantic pour l'API
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str
    sources: List[dict] = []

# Instance globale de l'agent RAG
global_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialiser l'agent RAG au démarrage"""
    global global_agent
    try:
        print("Initialisation de l'agent RAG...")
        global_agent = create_agentic_rag_system()
        print("Agent RAG initialisé avec succès!")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de l'agent RAG: {e}")
        global_agent = None

@app.get("/health")
async def health_check():
    """Point de santé de l'API"""
    return {
        "status": "healthy", 
        "message": "SIFHR RAG API is running",
        "agent_status": "initialized" if global_agent else "not_initialized"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """Point d'entrée principal pour le chat avec l'agent RAG"""
    
    if not global_agent:
        raise HTTPException(
            status_code=503,
            detail="Agent RAG non initialisé. Veuillez réessayer plus tard."
        )
    
    # Générer un ID de session si non fourni
    session_id = chat_message.session_id or str(uuid.uuid4())
    
    try:
        # Invoquer l'agent RAG
        result = global_agent.invoke({"input": chat_message.message})
        
        # Extraire la réponse et les sources
        response_text = result.get('output', 'Désolé, je n\'ai pas pu générer une réponse.')
        
        # Extraire les sources depuis les étapes intermédiaires si disponibles
        sources = []
        sources_found = []
        if 'intermediate_steps' in result:
            for step in result['intermediate_steps']:
                if len(step) > 1:
                    step_result = str(step[1])
                    if ' Sources (' in step_result:
                        # Parser les sources à partir des logs
                        lines = step_result.split('\n')
                        sources_section = False
                        for line in lines:
                            if ' Sources (' in line:
                                sources_section = True
                                continue
                            if sources_section and line.strip():
                                if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                                    # Format : "   1. filename ( minio://path)"
                                    if '(' in line and ')' in line:
                                        parts = line.split(' ( ')
                                        if len(parts) == 2:
                                            doc_name = parts[0].split('. ', 1)[-1].strip()
                                            doc_path = parts[1].replace(')', '').strip()
                                            sources_found.append({
                                                'name': doc_name,
                                                'path': doc_path
                                            })
                                elif not line.strip().startswith(' '):
                                    # Fin de la section sources
                                    sources_section = False
        
        # Formater les sources trouvées
        if sources_found:
            sources_text = "\n\n---\n\n## 📚 **SOURCES DOCUMENTAIRES UTILISÉES**\n\n"
            sources_text += "*Ce scénario s'appuie sur les documents authentiques suivants :*\n\n"
            for i, source in enumerate(sources_found[:10], 1):  # Limiter à 10 sources
                sources_text += f"**{i}.** `{source['name']}`\n"
                sources_text += f"   📁 *Localisation : {source['path']}*\n\n"
            
            sources_text += f"\n✨ *Total : {len(set(s['name'] for s in sources_found))} documents consultés pour garantir l'authenticité historique.*"
            
            response_text += sources_text
        
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            sources=sources
        )
        
    except Exception as e:
        print(f"Erreur lors du traitement du message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement: {str(e)}"
        )

@app.delete("/chat/{session_id}")
async def delete_session(session_id: str):
    """Supprimer une session de chat"""
    # Pour l'instant, retourner un succès simple
    # Plus tard, implémenter la suppression réelle de la session
    return {"message": f"Session {session_id} supprimée"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
