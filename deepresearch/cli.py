"""
CLI Interface - Command-line interface for DeepResearch Agent.
"""

import asyncio
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from deepresearch.core.engine import ResearchEngine

app = typer.Typer(
    name="deepresearch",
    help="Autonomous multi-source research agent"
)
console = Console()


@app.command()
def research(
    topic: str = typer.Argument(..., help="Research topic or question"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Start autonomous research on a topic."""
    if verbose:
        logging.basicConfig(level=logging.INFO)
    
    console.print(Panel(
        f"[bold blue]Starting Research:[/bold blue] {topic}",
        title="🔬 DeepResearch Agent"
    ))
    
    async def run_research():
        engine = ResearchEngine({
            "db_path": "data/research.db",
            "llm_endpoint": "https://api.mimo.xiaomi.com/v1/chat/completions",
            "model": "mimo-7b"
        })
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Researching...", total=None)
            
            result = await engine.research(topic)
            
            progress.update(task, completed=True)
        
        # Display results
        console.print("\n[bold green]✅ Research Complete![/bold green]")
        console.print(f"Confidence: {result.confidence_score:.1%}")
        console.print(f"Sources: {len(result.citations)}")
        
        # Display report
        if result.report:
            console.print(Panel(
                Markdown(result.report),
                title="📄 Research Report"
            ))
        
        # Save to file if specified
        if output:
            output.write_text(result.report or "No report generated")
            console.print(f"\n[bold]Report saved to:[/bold] {output}")
        
        return result
    
    asyncio.run(run_research())


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent entries")
):
    """View recent research history."""
    async def show_history():
        engine = ResearchEngine({"db_path": "data/research.db"})
        await engine.initialize()
        
        history = await engine.get_history(limit)
        
        if not history:
            console.print("[yellow]No research history found.[/yellow]")
            return
        
        console.print(Panel(
            f"[bold]Last {len(history)} Research Tasks[/bold]",
            title="📚 History"
        ))
        
        for item in history:
            status_color = "green" if item["status"] == "completed" else "yellow"
            console.print(
                f"[{status_color}]●[/{status_color}] "
                f"{item['topic'][:50]:50} "
                f"Confidence: {item['confidence_score']:.0%}"
            )
    
    asyncio.run(show_history())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind")
):
    """Start the API server."""
    import uvicorn
    
    console.print(Panel(
        f"[bold blue]Starting API Server[/bold blue]\n"
        f"Host: {host}\n"
        f"Port: {port}\n"
        f"Docs: http://{host}:{port}/docs",
        title="🚀 DeepResearch Agent"
    ))
    
    uvicorn.run(
        "deepresearch.api.main:app",
        host=host,
        port=port,
        reload=True
    )


@app.command()
def version():
    """Show version information."""
    from deepresearch import __version__
    console.print(f"[bold]DeepResearch Agent[/bold] v{__version__}")


if __name__ == "__main__":
    app()
