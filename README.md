# CD Ripper

A Python command-line tool to rip audio CDs and organize tracks into a clean folder layout.

## Features

- Rip an audio CD into WAV, FLAC, or MP3 files.
- Organize ripped tracks into artist/album folders using metadata.
- Simple CLI interface with `rip` and `organize` commands.

## Requirements

- Python 3.10+
- `cdparanoia` installed on Linux for ripping audio CDs
- Optional: `ffmpeg` for MP3/FLAC encoding

## System dependencies

On Debian/Ubuntu you can install common system packages with:

```bash
sudo apt update
sudo apt install -y cdparanoia ffmpeg libchromaprint-tools
```

`libchromaprint-tools` provides `fpcalc`, which is required for AcoustID fingerprinting. For macOS, install the tools via Homebrew:

```bash
brew install cdparanoia ffmpeg chromaprint
```

Python extras (for optional features):

```bash
python -m pip install musicbrainzngs pyacoustid discid
```

`--auto-release` uses AcoustID and MusicBrainz; you must supply an AcoustID API key via `--acoustid-key` to enable automatic release matching.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

## Usage

Rip a CD to WAV files:

```bash
cdripper rip --output-dir ./rips --format wav
```

Rip a CD and organize with metadata:

```bash
cdripper rip --output-dir ./rips --format flac --artist "Artist Name" --album "Album Name"
```

Organize an existing folder of ripped tracks:

```bash
cdripper organize ./rips
```

Auto-match a MusicBrainz release using AcoustID and apply album metadata:

```bash
# uses the installed `cdripper` script (from pyproject.toml entry points)
cdripper organize ./rips --auto-release --acoustid-key YOUR_ACOUSTID_KEY

# or with the module directly:
python -m cd_ripper.cli organize ./rips --auto-release --acoustid-key YOUR_ACOUSTID_KEY
```

Note: `--auto-release` requires network access and an AcoustID API key. The project's `pyproject.toml` already defines the console script entry point:

```toml
[project.scripts]
cdripper = "cd_ripper.cli:main"
```

## Development

Run the CLI help:

```bash
python -m cd_ripper.cli --help
```

Run tests:

```bash
pytest
```
