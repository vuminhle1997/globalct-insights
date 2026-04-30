from chromadb import Collection
from sqlmodel import Session

from backend.core.config import PG_HOST as pg_host, PG_PASSWORD as pg_password, PG_PORT as pg_port, PG_USER as pg_user
from backend.dependencies import SessionDep, engine, logger
from backend.models.chat import Chat
from backend.models.chat_file import ChatFile
from backend.services.migration.db_migration_manager import list_all_tables_from_db, load_dump_to_database
from backend.services.rag.indexer.files_indexer import index_sql_dump


def process_dump_to_persist(
    db_client: SessionDep,
    chat_id: str,
    chat_file_id: str,
    sql_dump_path: str,
    database_type: str,
    db_name: str,
    chroma_collection: Collection,
):
    """
    Processes a SQL dump file, loads it into a database, indexes its contents, and updates the database records.

    Args:
        db_client (Session): The database session client used to interact with the database.
        chat_id (str): The ID of the chat associated with the operation.
        chat_file_id (str): The ID of the chat file to be processed.
        sql_dump_path (str): The file path to the SQL dump file.
        database_type (str): The type of the database (e.g., PostgreSQL, MySQL).
        db_name (str): The name of the database where the dump will be loaded.
        chroma_collection (Collection): The Chroma collection used for indexing the SQL dump.

    Returns:
        None

    Raises:
        None

    Notes:
        - Ensures the chat and chat file exist in the database before proceeding.
        - Loads the SQL dump into the specified database.
        - Extracts and updates the list of tables from the database.
        - Indexes the SQL dump contents using the provided Chroma collection.
        - Commits the changes to the database session.
    """
    with Session(engine) as db_session:
        try:
            db_chat = db_session.get(Chat, chat_id)
            if not db_chat:
                logger.error(f"Chat: '{chat_id}' not found in background task.")
                return

            db_file = db_session.get(ChatFile, chat_file_id)
            if not db_file:
                logger.error(f"ChatFile: '{chat_file_id}' not found in background task.")
                return

            # 1. Load the dump (creates the target DB & populates it)
            load_dump_to_database(sql_dump_path, db_name)

            # 2. Discover tables & persist immediately (so we don't lose them if indexing fails)
            tables = list_all_tables_from_db(
                host=pg_host,
                port=pg_port,
                user=pg_user,
                password=pg_password,
                db_type=database_type,
                db=db_name,
            )
            db_file.tables = tables
            db_session.add(db_file)  # no-op if already in session, safe call
            db_session.commit()
            db_session.refresh(db_file)
            logger.debug(f"Persisted tables for ChatFile {db_file.id}: {tables}")

            if not tables:
                logger.warning(f"No tables discovered for DB '{db_name}' (type={database_type}). Skipping indexing.")
                return

            # 3. Index the SQL dump (vectorize table schemas)
            index_sql_dump(file=db_file, chroma_collection=chroma_collection)

            # 4. Mark as indexed & commit
            db_file.indexed = True
            db_session.commit()
            db_session.refresh(db_file)
            logger.info(f"Indexed SQL dump for ChatFile {db_file.id} (DB: {db_file.database_name})")
        except Exception as e:
            db_session.rollback()
            logger.error(
                f"Failed processing SQL dump for Chat: {chat_id}, File: {chat_file_id}. Error: {e}",
                exc_info=True,
            )
            return
