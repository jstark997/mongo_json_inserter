import json
import typer
from pymongo import errors, MongoClient

def check_connection(client: MongoClient):
    try:
        # Send a ping command to the admin database
        client.admin.command("ping")
        typer.secho("MongoDB connection is valid.", fg=typer.colors.GREEN)
        return True
    except Exception as e:
        typer.secho(f"Failed to connect to MongoDB: {e}", fg=typer.colors.RED)
        return False

def create_indexes(collection, index_specs):
    """
    Creates indexes on the specified MongoDB collection based on the provided index specifications.

    :param collection: The MongoDB collection.
    :param index_specs: A list of dictionaries specifying the indexes. Each dictionary should have:
        - `field`: The field to index.
        - `unique`: Whether the index should be unique (default: False).
        - `background`: Whether the index should be created in the background (default: True).
    """
    if not index_specs:
        typer.secho("No index specifications provided. Skipping index creation.", fg=typer.colors.YELLOW)
        return

    try:
        # Check existing indexes
        existing_indexes = collection.index_information()

        for spec in index_specs:
            field = spec.get("field")
            unique = spec.get("unique", False)
            background = spec.get("background", True)
            index_name = f"{field}_1"

            if index_name not in existing_indexes:
                collection.create_index(
                    [(field, 1)], unique=unique, background=background
                )
                typer.secho(f"Index on '{field}' created successfully. Unique: {unique}, Background: {background}", fg=typer.colors.GREEN)
            else:
                typer.secho(f"Index on '{field}' already exists.", fg=typer.colors.BLUE)

    except errors.OperationFailure as e:
        typer.secho(f"Operation failed while creating indexes: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"An error occurred while creating indexes: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

def insert_batch(collection, batch, results, file_path, log_file_path):
    """
    Inserts a batch of documents into the MongoDB collection.
    Updates the results dictionary with the counts for inserted documents,
    duplicate documents, and other errors.
    """
    try:
        # Attempt to insert the entire batch
        collection.insert_many(batch, ordered=False)  # `ordered=False` skips duplicates
        results["inserted"] += len(batch)
    except errors.BulkWriteError as e:
        # Get the number of failed writes from the error details
        failed_writes = e.details["writeErrors"]
        total_failed = len(failed_writes)

        # Count duplicate errors and other errors
        duplicates = sum(1 for error in failed_writes if error["code"] == 11000)
        other_errors = total_failed - duplicates

        # If there are other errors, log them
        if other_errors:
            with open(log_file_path, "a") as log_file:
                log_file.write(f"Bulk write error occurred in processing file - {file_path}\n")
                for error in e.details["writeErrors"]:
                    if error["code"] != 11000:  # Not a duplicate key error
                        log_file.write(f"Error: {error['errmsg']} (Document: {error['op']})\n")
            
        # Calculate successful insertions
        successful_insertions = len(batch) - total_failed
        results["inserted"] += successful_insertions
        results["duplicates"] += duplicates
        results["otherError"] += other_errors
    except Exception as e:
        typer.secho(f"Exception thrown in processing file - {file_path} : {e}", fg=typer.colors.RED)
        # If a general exception occurs, assume the entire batch failed for other reasons
        results["otherError"] += len(batch)
        with open(log_file_path, "a") as log_file:
            log_file.write(f"Exception thrown in processing file - {file_path} : {e}\n")

def batch_insert(file_path, collection, log_file_path, batch_size=1000):
    """
    Reads JSON lines from a file and inserts them into a MongoDB collection in batches.
    Logs summary results in a JSON format.
    """
    results = {
        "fileName": file_path,
        "totalLines": 0,
        "inserted": 0,
        "duplicates": 0,
        "otherError": 0,
    }

    try:
        with open(file_path, "r") as file:
            batch = []
            for line in file:
                results["totalLines"] += 1
                try:
                    # Parse the JSON line
                    document = json.loads(line.strip())
                    batch.append(document)

                    # Insert documents in batches
                    if len(batch) >= batch_size:
                        insert_batch(collection, batch, results, file_path, log_file_path)
                        batch = []  # Clear the batch
                except json.JSONDecodeError:
                    results["otherError"] += 1  # Count as an error for invalid JSON

            # Insert any remaining documents in the batch
            if batch:
                insert_batch(collection, batch, results, file_path, log_file_path)

        # Write summary results to log file as a JSON line
        with open(log_file_path, "a") as log_file:
            log_file.write(json.dumps({"results": results}) + "\n")

    except FileNotFoundError as e:
        typer.secho(f"File not found: {e}", fg=typer.colors.RED)
    except Exception as e:
        typer.secho(f"An error occurred while processing file: {file_path}: {e}", fg=typer.colors.RED)
