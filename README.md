# Mongo JSON Inserter

`mongo_json_inserter` is a CLI application designed to process JSON lines from files and insert them into a MongoDB database collection. The application handles batch processing, creates indexes if specified, and logs the processing results for each file. Successfully processed files are moved to a destination directory.

---

## Features

- Connects to a MongoDB database and validates the connection.
- Processes all JSON files in a specified directory.
- Inserts JSON lines into a MongoDB collection in batches.
- Supports creating MongoDB indexes via specifications.
- Logs processing results to a timestamped log file.
- Moves successfully processed files to a destination directory.

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/jstark997/mongo_json_inserter.git
   cd mongo_json_inserter
   ```

2. Install the application using `pipx`:

   ```bash
   pipx install .
   ```

   If you don't have `pipx` installed, you can install it using:

   ```bash
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath
   ```

   Then restart your terminal or reload your shell configuration.

---

## Usage

The application is invoked using the `monjin` command.

### Syntax

```bash
monjin <db_connection_url> <database_name> <collection_name> <source_dir> <dest_dir> <log_file_path> [index_specs]
```

### Arguments

- `db_connection_url`: MongoDB connection URL (e.g., `mongodb://localhost:27017`).
- `database_name`: Name of the MongoDB database.
- `collection_name`: Name of the MongoDB collection.
- `source_dir`: Directory containing the JSON files to process.
- `dest_dir`: Directory where successfully processed files will be moved.
- `log_file_path`: Path to the log file where results will be written.
- `index_specs` (optional): JSON string specifying index configurations (e.g., `'[{"field": "name", "unique": true}]'`).

### Example

1. Create a source directory and add JSON files:

   ```bash
   mkdir source_dir
   echo '{"name": "John", "age": 30}' > source_dir/file1.json
   echo '{"name": "Jane", "age": 25}' > source_dir/file2.json
   ```

2. Create a destination directory:

   ```bash
   mkdir dest_dir
   ```

3. Create a logs directory:

   ```bash
   mkdir logs
   ```

4. Run the application:

   ```bash
   monjin mongodb://localhost:27017 test_db test_collection source_dir dest_dir logs/db_insert '[{"field": "name", "unique": true}]'
   ```

5. Check the destination directory for moved files:

   ```bash
   ls dest_dir
   ```

6. Review the log file for processing results:

   ```bash
   cat logs/db_insert-<timestamp>.log
   ```

---

## Index Specification Format

When providing index specifications, use a JSON string containing an array of index configuration objects. Each object should have the following fields:

- `field` (string, required): The name of the field to index.
- `unique` (boolean, optional): Whether the index should enforce uniqueness. Default is `false`.
- `background` (boolean, optional): Whether the index should be created in the background. Default is `true`.

### Example

```json
[
  { "field": "name", "unique": true },
  { "field": "age", "unique": false, "background": false }
]
```

In the above example:

- The `name` field will have a unique index.
- The `age` field will have a non-unique index created in the foreground.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Author

Jeff Stark (<jstark997@gmail.com>)
