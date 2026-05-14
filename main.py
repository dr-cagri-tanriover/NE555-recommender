from __future__ import annotations

import sys

import click

from config import settings
from pdf_generator import generate_pdf
from recommender import RecommenderError, get_recommendations


@click.command()
@click.argument("prompt", nargs=-1, required=False)
@click.option(
    "--prompt-file", "-f",
    default=None,
    type=click.Path(exists=True, readable=True, dir_okay=False),
    help="Path to a text file containing the circuit description.",
)
@click.option(
    "--count", "-n",
    default=3,
    show_default=True,
    type=click.IntRange(1, 10),
    help="Number of circuits to recommend (1-10).",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output PDF path (default: from OUTPUT_PDF_PATH env var or 'ne555_report.pdf').",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Print progress to stderr.",
)
def main(prompt: tuple[str, ...], prompt_file: str | None, count: int, output: str | None, verbose: bool) -> None:
    """NE555 Circuit Recommender.

    PROMPT describes the desired circuit features, e.g.:

    \b
        python main.py "astable oscillator at 1kHz for audio tone generation" --count 3
        python main.py monostable pulse timer 5 second delay --count 2
        python main.py --prompt-file my_requirements.txt --count 3
    """
    if prompt_file and prompt:
        raise click.UsageError("Provide either PROMPT text or --prompt-file, not both.")
    if prompt_file:
        with open(prompt_file, encoding="utf-8") as fh:
            user_prompt = fh.read().strip()
        if not user_prompt:
            raise click.UsageError(f"Prompt file '{prompt_file}' is empty.")
    elif prompt:
        user_prompt = " ".join(prompt)
    else:
        raise click.UsageError("Provide a PROMPT argument or --prompt-file.")

    output_path = output or settings.output_pdf_path

    if verbose:
        click.echo(f"Finding {count} NE555 circuit(s) for: {user_prompt}", err=True)
        click.echo(f"Output: {output_path}", err=True)
    else:
        # Always show a minimal progress indicator even without --verbose
        click.echo(f"Searching for {count} NE555 circuit(s)…", err=True)

    try:
        circuits = get_recommendations(user_prompt, count)
    except RecommenderError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Generating PDF with {len(circuits)} circuit(s)…", err=True)
    generate_pdf(circuits, user_prompt, output_path, count)
    click.echo(f"Report written to: {output_path}")


if __name__ == "__main__":
    main()
