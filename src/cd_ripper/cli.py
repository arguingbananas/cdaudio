import os
import subprocess
import sys
from pathlib import Path

import click

from cd_ripper.organizer import organize_rips
from cd_ripper.ripper import rip_cd


@click.group()
def main():
    """CD Ripper CLI."""


@main.command()
@click.option("--drive", default="/dev/cdrom", help="CD-ROM device path.")
@click.option("--output-dir", default="./rips", type=click.Path(file_okay=False, writable=True), help="Directory to save ripped tracks.")
@click.option("--format", default="wav", type=click.Choice(["wav", "flac", "mp3"]), help="Output audio format.")
@click.option("--artist", default="", help="Artist name for metadata organization.")
@click.option("--album", default="", help="Album name for metadata organization.")
@click.option("--year", default="", help="Release year for metadata tags.")
@click.option("--genre", default="", help="Genre for metadata tags.")
def rip(drive, output_dir, format, artist, album, year, genre):
    """Rip an audio CD and save tracks."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metadata = {
        "artist": artist.strip(),
        "album": album.strip(),
        "year": year.strip(),
        "genre": genre.strip(),
    }

    click.echo(f"Ripping CD from {drive} into {output_path} as {format.upper()}")
    rip_cd(drive, output_path, format, metadata)
    click.echo("Rip completed.")


@main.command()
@click.argument("source-dir", type=click.Path(exists=True, file_okay=False, readable=True))
@click.option("--auto-release", is_flag=True, default=False, help="Automatically match a MusicBrainz release via AcoustID and apply album metadata.")
@click.option("--acoustid-key", default="", help="AcoustID API key to use for fingerprint lookups (required with --auto-release).")
def organize(source_dir, auto_release, acoustid_key):
    """Organize ripped audio files into artist/album folders.

    Use `--auto-release` with `--acoustid-key` to automatically match a
    MusicBrainz release and apply album-level metadata before organizing.
    """
    key = acoustid_key.strip() or None
    organize_rips(Path(source_dir), auto_release=auto_release, acoustid_key=key)


if __name__ == "__main__":
    main()
