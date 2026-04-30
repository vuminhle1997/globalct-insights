"""Service layer for SQL dump ingestion and database management.

Handles loading MySQL/PostgreSQL dump files, migrating MySQL → PostgreSQL,
listing tables, and dropping databases on the managed PostgreSQL instance.
"""

import os
import re

import mysql.connector
import psycopg2

from backend.core.config import (
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    PG_HOST,
    PG_PASSWORD,
    PG_PORT,
    PG_USER,
)
from backend.dependencies import logger

# MySQL credentials — used only for migration flows
_MYSQL_HOST: str = MYSQL_HOST
_MYSQL_PORT: int = MYSQL_PORT
_MYSQL_USER: str = MYSQL_USER
_MYSQL_PASSWORD: str = MYSQL_PASSWORD


class PostgresMigration:
    """
    A utility class for migrating data from a MySQL database to a PostgreSQL database
    and optionally deleting the old MySQL database.

    Methods:
        __init__(host: str, port: int, user: str, password: str, db: str):
            Initializes the PostgresMigration instance with MySQL connection details.

        migrate_mysql_to_pg(pg_host: str, pg_port: int, pg_user: str, pg_password: str, pg_db: str, **kwargs):
            Migrates data from the MySQL database to a PostgreSQL database using pgloader.
            Creates the PostgreSQL database if it does not exist.

        delete_old_db_from_mysql(**kwargs):
            Deletes the old MySQL database after migration.

    Attributes:
        mysql_host (str): The hostname or IP address of the MySQL server.
        mysql_user (str): The username for the MySQL server.
        mysql_password (str): The password for the MySQL server.
        mysql_database (str): The name of the MySQL database.
        mysql_port (int): The port number for the MySQL server.
        mysql_db (str): Alias for the MySQL database name.
    """

    def __init__(self, host: str, port: int, user: str, password: str, db: str):
        self.mysql_host = host
        self.mysql_user = user
        self.mysql_password = password
        self.mysql_database = db
        self.mysql_port = port
        self.mysql_db = db

    def migrate_mysql_to_pg(
        self,
        pg_host: str,
        pg_port: int,
        pg_user: str,
        pg_password: str,
        pg_db: str,
        **kwargs,
    ):
        """
        Migrates a MySQL database to a PostgreSQL database using pgloader.

        This method connects to a PostgreSQL server, checks if the target database exists,
        and creates it if it does not. Then, it uses the `pgloader` tool to migrate data
        from the MySQL database to the PostgreSQL database.

        Args:
            pg_host (str): The hostname or IP address of the PostgreSQL server.
            pg_port (int): The port number of the PostgreSQL server.
            pg_user (str): The username for the PostgreSQL server.
            pg_password (str): The password for the PostgreSQL server.
            pg_db (str): The name of the target PostgreSQL database.
            **kwargs: Additional keyword arguments to pass to the PostgreSQL connection.

        Raises:
            psycopg2.Error: If there is an error connecting to or interacting with the PostgreSQL server.
            Exception: If there is a general error during the database migration process.

        Notes:
            - The method assumes that the `pgloader` tool is installed and available in the system's PATH.
            - MySQL connection details (host, port, user, password, and database) are expected to be
              attributes of the class instance (`self.mysql_host`, `self.mysql_port`, `self.mysql_user`,
              `self.mysql_password`, `self.mysql_db`).
        """
        try:
            conn = psycopg2.connect(
                host=pg_host,
                port=pg_port,
                user=pg_user,
                password=pg_password,
                dbname="postgres",
                **kwargs,
            )
            conn.autocommit = True
            cursor = conn.cursor()

            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{pg_db}';")
            if not cursor.fetchone():
                cursor.execute(f"CREATE DATABASE {pg_db};")
                logger.debug(f"Database '{pg_db}' created successfully.")
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL Error: {e}")
        except Exception as e:
            logger.error(f"General Error: {e}")

        try:
            mysql_url = (
                f"mysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
            )
            pg_url = f"pgsql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
            os.system(f"pgloader {mysql_url} {pg_url}")
        except Exception as e:
            logger.error(f"General Error: {e}")

    def delete_old_db_from_mysql(self, **kwargs):
        """
        Deletes an existing database from a MySQL server.

        This method connects to a MySQL server using the provided connection
        parameters and attempts to drop the specified database.

        Args:
            **kwargs: Additional keyword arguments to pass to the MySQL connection.

        Raises:
            mysql.connector.Error: If an error occurs while connecting to the MySQL
            server or executing the DROP DATABASE command.

        Notes:
            - Ensure that the user has sufficient privileges to drop the database.
            - Use this method with caution as it will permanently delete the database.
        """
        try:
            conn = mysql.connector.connect(
                host=self.mysql_host,
                user=self.mysql_user,
                password=self.mysql_password,
                port=self.mysql_port,
                **kwargs,
            )
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE {self.mysql_db}")
            logger.debug(f"Database '{self.mysql_db}' dropped successfully.")
            conn.commit()
            conn.close()
        except mysql.connector.Error as e:
            logger.error(f"MySQL Error: {e}")


def initialize_pg_url(pg_db: str) -> str:
    """
    Constructs a PostgreSQL connection URL.

    Args:
        pg_db (str): The name of the PostgreSQL database.

    Returns:
        str: A formatted PostgreSQL connection URL in the form:
             "postgresql://<PG_USER>:<PG_PASSWORD>@<PG_HOST>:<PG_PORT>/<pg_db>".
    """
    return f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{pg_db}"


def load_mysql_dump(host: str, port: int, user: str, password: str, db: str, dump_path: str, **kwargs):
    """
    Loads a MySQL dump file into a specified database.

    This function connects to a MySQL server, creates the specified database
    if it does not exist, and executes the SQL statements from the provided
    dump file to populate the database.

    Args:
        host (str): The hostname or IP address of the MySQL server.
        port (int): The port number of the MySQL server.
        user (str): The username to authenticate with the MySQL server.
        password (str): The password to authenticate with the MySQL server.
        db (str): The name of the database to load the dump into.
        dump_path (str): The file path to the SQL dump file.
        **kwargs: Additional keyword arguments to pass to the MySQL connection.

    Raises:
        mysql.connector.Error: If there is an error related to MySQL operations.
        Exception: For any other general errors.

    Notes:
        - The function removes any `CREATE DATABASE` and `USE` statements from
          the SQL dump file to ensure compatibility with the specified database.
        - The connection is automatically committed after each statement.
    """
    try:
        conn = mysql.connector.connect(host=host, user=user, password=password, port=port, **kwargs)
        cursor = conn.cursor()

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db};")
        logger.debug(f"Database '{db}' checked/created successfully.")

        conn.database = db
        conn.autocommit = True

        with open(dump_path, encoding="utf-8") as file:
            sql_script = file.read()

        sql_script = re.sub(r"(?i)CREATE DATABASE.*?;", "", sql_script)
        sql_script = re.sub(r"(?i)USE\s+\S+;", "", sql_script)

        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        logger.debug(f"SQL dump {dump_path}, DB:{db} loaded successfully.")
    except mysql.connector.Error as e:
        logger.error(f"MySQL Error: {e}")
    except Exception as e:
        logger.error(f"General Error: {e}")
    finally:
        cursor.close()
        conn.close()


def load_pgsql_dump(host: str, port: int, user: str, password: str, db: str, dump_path: str, **kwargs):
    """
    Load a PostgreSQL database dump into a specified database. If the database does not exist, it will be created.

    Args:
        host (str): The hostname or IP address of the PostgreSQL server.
        port (int): The port number on which the PostgreSQL server is listening.
        user (str): The username to connect to the PostgreSQL server.
        password (str): The password for the specified user.
        db (str): The name of the database to load the dump into.
        dump_path (str): The file path to the SQL dump file.
        **kwargs: Additional keyword arguments to pass to the psycopg2 connection.

    Raises:
        psycopg2.Error: If there is an error connecting to the PostgreSQL server or executing SQL commands.

    Notes:
        - The function first checks if the specified database exists. If it does not, it creates the database.
        - The SQL dump is loaded using the `psql` command-line utility.
        - Ensure that the `psql` utility is installed and available in the system's PATH.
        - The `PGPASSWORD` environment variable is temporarily set to provide the password for the `psql` command.
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname="postgres",
            **kwargs,
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Create the database if it doesn't exist
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db}';")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {db};")
            logger.debug(f"Database '{db}' created successfully.")
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL Error: {e}")
    finally:
        os.system(f"PGPASSWORD={password} psql -U {user}  -h {host} -p {port} -d {db} < {dump_path}")


def detect_sql_dump_type(file_path: str) -> str:
    """
    Detect the type of an SQL dump file (MySQL or PostgreSQL).

    This function analyzes the content of a given SQL dump file to determine whether
    it originates from a MySQL or PostgreSQL database. It searches for specific
    keywords that are characteristic of each database type.

    Args:
        file_path (str): The path to the SQL dump file to be analyzed.

    Returns:
        str: A string indicating the type of the SQL dump:
            - "MySQL" if MySQL-specific keywords are detected.
            - "Postgres" if PostgreSQL-specific keywords are detected.
            - "Unknown" if no specific keywords are found.
            - An error message if the file cannot be read.
    """
    """Detect if an SQL dump is from MySQL or PostgreSQL."""
    mysql_keywords = {
        "ENGINE=",
        "AUTO_INCREMENT",
        "UNLOCK TABLES",
        "LOCK TABLES",
        "CHARSET=",
    }
    postgres_keywords = {
        "SET search_path",
        "SERIAL PRIMARY KEY",
        "RETURNING",
        "BIGSERIAL",
        "NOW()",
    }

    try:
        with open(file_path, encoding="utf-8", errors="ignore") as file:
            for line in file:
                line = line.strip().upper()
                if any(keyword in line for keyword in mysql_keywords):
                    return "MySQL"
                if any(keyword in line for keyword in postgres_keywords):
                    return "Postgres"
        return "Unknown"
    except Exception as e:
        logger.error(f"Error reading sql dump file: {e}")
        return f"Error reading file: {e}"


def load_dump_to_database(sql_dump_path: str, db_name="TWICE"):
    """
    Loads a SQL dump file into a database and optionally migrates it to PostgreSQL.

    This function detects the type of SQL dump (MySQL or PostgreSQL) and performs the
    appropriate loading operation. If the dump is for MySQL, it also migrates the data
    to a PostgreSQL database and deletes the old MySQL database.

    Args:
        sql_dump_path (str): The file path to the SQL dump file.
        db_name (str, optional): The name of the database to load the dump into. Defaults to "TWICE".

    Raises:
        ValueError: If the SQL dump type cannot be detected or is unsupported.

    Notes:
        - For MySQL dumps, the function assumes the presence of MySQL credentials and
          performs a migration to PostgreSQL after loading the dump.
        - For PostgreSQL dumps, the function directly loads the dump into the specified
          PostgreSQL database.
    """
    db = detect_sql_dump_type(sql_dump_path)
    if db == "MySQL":
        logger.debug(f"MySQL dump detected for file: {sql_dump_path}")
        load_mysql_dump(_MYSQL_HOST, _MYSQL_PORT, _MYSQL_USER, _MYSQL_PASSWORD, db_name, sql_dump_path)
        migration = PostgresMigration(
            _MYSQL_HOST,
            _MYSQL_PORT,
            _MYSQL_USER,
            _MYSQL_PASSWORD,
            db_name,
        )
        migration.migrate_mysql_to_pg(PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, db_name)
        migration.delete_old_db_from_mysql()
    elif db == "Postgres":
        logger.debug(f"PostgreSQL dump detected for file: {sql_dump_path}")
        load_pgsql_dump(PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, db_name, sql_dump_path)


def list_all_tables_from_db(host: str, port: int, user: str, password: str, db: str, db_type: str, **kwargs):
    """
    Lists all tables from a specified database.

    This function connects to a database (PostgreSQL or MySQL) and retrieves the names of all tables
    in the specified database schema. By default, it retrieves tables from the 'public' schema for PostgreSQL
    and the specified database schema for MySQL.

    Args:
        host (str): The hostname or IP address of the database server.
        port (int): The port number on which the database server is listening.
        user (str): The username to authenticate with the database.
        password (str): The password to authenticate with the database.
        db (str): The name of the database to connect to.
        db_type (str): The type of the database, either "PostgreSQL" or "MySQL".
        **kwargs: Additional keyword arguments to pass to the database connection.

    Returns:
        list: A list of table names in the specified database schema. Returns an empty list if an error occurs.

    Raises:
        psycopg2.Error: If an error occurs while connecting to or querying the PostgreSQL database.

    Notes:
        - For PostgreSQL, the function retrieves tables from the 'public' schema.
        - For MySQL, the function retrieves tables from the schema specified by the `db` parameter.
    """
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=db,
            **kwargs,
        )
        cursor = conn.cursor()
        statement = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        if db_type == "MySQL":
            statement = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{db}';"
        cursor.execute(statement)

        tables = []
        for table in cursor.fetchall():
            tables.append(table[0])

        logger.debug(f"Tables: {tables} from database: {db}")
        cursor.close()
        conn.close()
        return tables
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL Error: {e}")
        return []


def delete_database_from_postgres(database_name: str):
    """
    Deletes a PostgreSQL database with the specified name.

    This function connects to the PostgreSQL server using the provided
    connection parameters and executes a SQL statement to drop the database.
    The connection is made to the 'postgres' database, which is required
    because a database cannot drop itself.

    Args:
        database_name (str): The name of the database to be deleted.

    Raises:
        psycopg2.Error: If an error occurs while connecting to the database
                        or executing the SQL statement.

    Example:
        delete_database_from_postgres("example_db")
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname="postgres",
        )
        conn.autocommit = True
        cursor = conn.cursor()
        statement = f"DROP DATABASE {database_name};"
        cursor.execute(statement)

        logger.debug(f"Database '{database_name}' dropped successfully.")
        cursor.close()
        conn.close()
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL Error: {e}")
        raise e
