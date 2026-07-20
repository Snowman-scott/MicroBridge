import sys

import click

from MicroBridge.utils import clear_terminal
from MicroBridge.Core.core import convert_ndpa_to_lmd_core, derive_output_filename


@click.command()
@click.argument("files", nargs=-1, required=True)
def run(files):
    successful = 0
    failures = []
    for file in files:
        output_name = derive_output_filename(file)
        try:
            convert_ndpa_to_lmd_core(file, output_name)
        except ValueError as e:
            failures.append((file, e))
            click.echo(f"Converting the ndpa to an LMD xml failed: {e}", err=True)
        else:
            click.echo("Successfully converted ndpa into LMD xml :3")
            successful += 1


    click.echo("\n\n\n===============================================")
    if successful == len(files):
        click.echo(f"{successful}/{len(files)} files converted. \nAll files converted fine :3")
        sys.exit(0)
    else:
        click.echo(f"{len(failures)}/{len(files)} failed to convert 3:\nThe files that failed to convert were:\n")
        for filename, err in failures:
            click.echo(f"{filename} errored with: {err}", err=True)
        sys.exit(1)
