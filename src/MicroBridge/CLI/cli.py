import sys

import click

from pathlib import Path
from xml.parsers.expat import ExpatError

from MicroBridge.Core.core import convert_ndpa_to_lmd_core, derive_output_filename
from MicroBridge.launcher import install_launcher as _install_launcher

BANNER = r"""
  ___  ____               ______      _     _
  |  \/  (_)              | ___ \    (_)   | |
  | .  . |_  ___ _ __ ___ | |_/ /_ __ _  __| | __ _  ___
  | |\/| | |/ __| '__/ _ \| ___ \ '__| |/ _` |/ _` |/ _ \
  | |  | | | (__| | | (_) | |_/ / |  | | (_| | (_| |  __/
  \_|  |_/_|\___|_|  \___/\____/|_|  |_|\__,_|\__, |\___|
                                               __/ |
                                              |___/
"""

def convert_files(files, output):
    successful = 0
    failures = []
    for file in files:
        if Path(file).suffix != ".ndpa":
            message = f"\nExpected a '.ndpa' file, got a '{Path(file).suffix}' file Instead"
            failures.append((file, message))
            continue
        output_name = derive_output_filename(file)
        if output:
            output_name = str(Path(output) / Path(output_name).name)
        try:
            convert_ndpa_to_lmd_core(file, output_name)
        except (ValueError, FileNotFoundError, IsADirectoryError, ExpatError) as e:
            failures.append((file, e))
            click.echo(f"Converting the ndpa to an LMD xml failed: {e}", err=True)
        else:
            click.echo("Successfully converted ndpa into LMD xml")
            successful += 1
    return successful, failures

def find_ndpa_files(directory):
    files = []
    for entry in Path(directory).iterdir():
        if entry.suffix == ".ndpa":
            files.append(str(entry))
    return files

@click.command()
@click.pass_context
@click.option('-b', '--batch',type=click.Path(), nargs=1, required=False, help="Process a Directory of '.ndpa' files in one go.")
@click.option('-o', '--output',type=click.Path(), nargs=1, required=False, help="Select an output directory for the converted '.ndpa' files to end up in.")
@click.option('--install-launcher', is_flag=True, default=False,
              help="Add MicroBridge to your applications menu (no admin needed).")
@click.argument("files", nargs=-1, required=False)
def run(ctx, files, batch, output, install_launcher):
    click.echo(BANNER)
    if install_launcher:
        try:
            created = _install_launcher()
        except NotImplementedError as e:
            click.secho(str(e), fg="red", err=True)
            sys.exit(1)
        except OSError as e:
            click.secho(f"Could not install the launcher: {e}", fg="red", err=True)
            sys.exit(1)
        click.secho(f"Launcher installed at {created}", fg="green")
        sys.exit(0)
    if not files and not batch:
        click.echo(ctx.get_help())
        sys.exit(1)
    elif files and batch:
        click.echo(f"You cannot have files and -b dir in one command \n\n{ctx.get_help()}")
        sys.exit(1)
    elif batch:
        files = find_ndpa_files(batch)
    successful, failures = convert_files(files, output)


    click.echo("\n\n\n===============================================")
    if successful == len(files):
        click.secho(f"{successful}/{len(files)} files converted. \nAll files converted fine", fg="green",err=False)
        sys.exit(0)
    else:
        click.secho(f"{len(failures)}/{len(files)} failed to convert \nThe files that failed to convert were:\n", fg="red", err=True)
        for filename, err in failures:
            click.secho(f"{filename} errored with: {err}", fg="red", bold=True, err=True)
        sys.exit(1)
