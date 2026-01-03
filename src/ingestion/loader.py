import logging
from pathlib import Path
import shutil
from langchain_community.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_chroma import Chroma
from src import config # Import config from src

logger = logging.getLogger(__name__)

def load_documents_from_corpus(corpus_path: Path):
    """Loads all text documents from the specified corpus path."""
    logger.info(f"Loading documents from {corpus_path}...")
    
    if not corpus_path.exists():
        logger.error(f"Corpus path does not exist: {corpus_path}")
        return []

    # Using UnstructuredFileLoader for broader compatibility with various text-based files
    loader = DirectoryLoader(
        str(corpus_path),
        glob="**/*",
        loader_cls=UnstructuredFileLoader,
        show_progress=True,
        use_multithreading=True
    )
    documents = loader.load()
    if not documents:
        logger.warning(f"No documents found in {corpus_path}. Please check the path and file types.")
    logger.info(f"Loaded {len(documents)} documents from corpus.")
    return documents

def split_documents(documents, chunk_size: int, chunk_overlap: int):
    """Splits documents into smaller, manageable chunks."""
    logger.info(f"Splitting {len(documents)} documents into chunks (size={chunk_size}, overlap={chunk_overlap})...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True
    )
    splits = text_splitter.split_documents(documents)
    logger.info(f"Created {len(splits)} document splits.")
    return splits

def get_azure_openai_embeddings_model():
    """Initializes and returns the Azure OpenAI Embeddings model."""
    logger.info("Initializing Azure OpenAI Embeddings model...")
    try:
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
            openai_api_version=config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
        )
        return embeddings
    except Exception as e:
        logger.error(f"Error initializing Azure OpenAI Embeddings: {e}. Check AZURE_OPENAI_ environment variables.")
        raise

def setup_chroma_db(documents, embeddings, db_path: Path):
    """
    Sets up or updates the ChromaDB vector store.
    If the DB exists, it tries to load it; otherwise, it creates a new one.
    """
    logger.info(f"Checking Chroma DB at {db_path}...")
    
    # Ensure parent directory exists for the Chroma DB
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Check if a Chroma DB already exists
    if db_path.exists() and any(db_path.iterdir()):
        logger.info(f"Loading existing Chroma DB from {db_path}...")
        try:
            vectorstore = Chroma(persist_directory=str(db_path), embedding_function=embeddings)
            logger.info("Chroma DB loaded successfully.")
            return vectorstore
        except Exception as e:
            logger.warning(f"Error loading existing Chroma DB: {e}. Attempting to recreate DB.")
            # If loading fails, remove existing (potentially corrupted) DB and recreate
            if db_path.exists():
                shutil.rmtree(db_path)
            
    logger.info(f"Creating new Chroma DB at {db_path}...")
    if not documents:
        logger.warning("No documents available to create the vector database.")
        return None
        
    splits = split_documents(documents, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    if not splits:
        logger.warning("No document splits generated. Cannot create vector database.")
        return None

    try:
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=str(db_path)
        )
        # Chroma's .persist() method ensures data is written to disk
        vectorstore.persist() 
        logger.info("Chroma DB created and persisted successfully.")
        return vectorstore
    except Exception as e:
        logger.error(f"Error creating Chroma DB: {e}. Check your embeddings model and data.")
        raise

def ingest_pipeline():
    """
    Orchestrates the full ingestion pipeline: loads documents, splits them,
    generates embeddings, and stores them in ChromaDB.
    """
    logger.info("Starting document ingestion pipeline for ChromaDB...")
    try:
        # 1. Load documents
        documents = load_documents_from_corpus(config.CORPUS_PATH)
        if not documents:
            logger.error("No documents loaded. Aborting ingestion.")
            return

        # 2. Get embeddings model
        embeddings = get_azure_openai_embeddings_model()

        # 3. Setup ChromaDB
        vectorstore = setup_chroma_db(documents, embeddings, config.CHROMA_DB_PATH)
        if vectorstore:
            logger.info("ChromaDB ingestion pipeline completed.")
        else:
            logger.error("ChromaDB vector store could not be set up. Aborting ingestion.")
    except Exception as e:
        logger.critical(f"Critical error during ingestion pipeline: {e}", exc_info=True)
