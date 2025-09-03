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
#PROMPT
        # Prompt dynamique pour scénarios immersifs
        prompt_prefix = """Tu es un maître de jeu spécialisé dans la création de scénarios immersifs 
inspirés de l'histoire, des légendes et des civilisations arabo-musulmanes. 
Ton objectif est d'aider à créer des quêtes de chasse au trésor captivantes.

INSTRUCTIONS IMPORTANTES :
1. Utilise EXCLUSIVEMENT le contexte fourni pour construire le scénario
2. Si l'information n'existe pas dans le contexte, réponds clairement :
   "Cette information n'est pas disponible dans les documents consultés"
3. Crée des descriptions immersives (lieux, personnages, objets, indices)
4. Structure la réponse avec des puces ou des paragraphes narratifs selon le besoin
5. N'invente rien en dehors du contexte, mais enrichis l'ambiance avec un style narratif immersif
"""

        prompt_suffix = """
CONTEXTE DOCUMENTAIRE :
{context}

QUESTION DU JOUEUR : {question}

RÉPONSE IMMERSIVE BASÉE SUR LES DOCUMENTS :
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


if __name__ == "__main__":
    main()
