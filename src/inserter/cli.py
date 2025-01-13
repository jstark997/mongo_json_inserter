import typer

from .insert import insert_files

app = typer.Typer()
app.command()(insert_files)

if __name__ == "__main__":
    app()