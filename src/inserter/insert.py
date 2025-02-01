import json
import os
import shutil
from typing import Optional
import typer
from typing_extensions import Annotated
from pymongo import MongoClient
from datetime import datetime
from inserter.utils import check_connection, create_indexes, batch_insert

def insert_files(
    db_connection_url: Annotated[str, typer.Argument(help="MongoDB connection URL")],
    database_name: Annotated[str, typer.Argument(help="Database name")],
    collection_name: Annotated[str, typer.Argument(help="Collection name")],
    source_dir: Annotated[str, typer.Argument(help="Source directory containing JSON files")],
    dest_dir: Annotated[str, typer.Argument(help="Destination directory for processed files")],
    log_file_path: Annotated[str, typer.Argument(help="Path to the log file")],
    add_fields: Annotated[Optional[str], typer.Argument(help="Optional JSON array specifying fields to add to each document with null values")] = None
        ):
    """
    Processes all files in the specified directory:
    - Inserts JSON lines from each file into the MongoDB collection.
    - Moves successfully processed files to the destination directory.
    - Writes log entries to a timestamped log file.
    """

    # Check if directories exist
    if not os.path.isdir(source_dir):
        typer.secho(f"Source directory does not exist: {source_dir}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if not os.path.isdir(dest_dir):
        typer.secho(f"Destination directory does not exist: {dest_dir}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    
    # Append the current date and time to the log file name
    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file_name, log_file_ext = os.path.splitext(log_file_path)
    timestamped_log_file_path = f"{log_file_name}-{current_time}.log"

    try:
        # Connect to MongoDB
        typer.secho("Connecting to MongoDB...", fg=typer.colors.BLUE)
        client = MongoClient(db_connection_url)

        # Validate the connection
        if not check_connection(client):
            typer.secho("Exiting due to invalid MongoDB connection.", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        db = client[database_name]
        collection = db[collection_name]
        typer.secho(f"Connected to database: {db}", fg=typer.colors.GREEN)
        typer.secho(f"Connected to collection: {collection}", fg=typer.colors.GREEN)

        # Check if there are additional empty fields to add
        additional_fields = {}
        if add_fields:
            try:
                field_list = json.loads(add_fields)
                if isinstance(field_list, list):
                    additional_fields = {field: None for field in field_list}
                else:
                    raise ValueError("Expected a JSON array of field names.")
            except (json.JSONDecodeError, ValueError) as e:
                typer.secho(f"Invalid additional fields JSON: {e}", fg=typer.colors.RED)
                raise typer.Exit(code=1)

        # List all files in the source directory
        files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
        if not files:
            typer.secho("No files to process.", fg=typer.colors.YELLOW)
            return

        for file_name in files:
            file_path = os.path.join(source_dir, file_name)
            typer.secho(f"Processing file: {file_path}", fg=typer.colors.BLUE)

            # Perform batch insert
            batch_insert(file_path, collection, timestamped_log_file_path, additional_fields)

            # Move the file to the destination directory
            dest_path = os.path.join(dest_dir, file_name)
            shutil.move(file_path, dest_path)
            typer.secho(f"Moved file to: {dest_path}", fg=typer.colors.GREEN)

    except Exception as e:
        typer.secho(f"An error occurred during processing: {e}", fg=typer.colors.RED)
    finally:
        client.close()
