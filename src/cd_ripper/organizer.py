import re
import shutil
from pathlib import Path
from typing import Optional

from mutagen import File

try:
    import acoustid
    import musicbrainzngs
except Exception:
    acoustid = None
    musicbrainzngs = None


def _normalize_track_number(track_number: Optional[str]) -> Optional[str]:
    if not track_number:
        return None

    track = str(track_number).split("/")[0].strip()
    match = re.match(r"^(\d+)", track)
    if not match:
        return None

    return match.group(1).zfill(2)


def _sanitize_title(title: str) -> str:
    title = title.strip()
    title = re.sub(r"[\\/*:?\"<>|]+", "", title)
    title = re.sub(r"\s+", " ", title)
    return title


def _build_target_filename(title: Optional[str], track_number: Optional[str], original_name: str) -> str:
    ext = Path(original_name).suffix
    if title:
        title = _sanitize_title(title)
        if track_number:
            return f"{track_number} - {title}{ext}"
        return f"{title}{ext}"
    if track_number:
        return f"{track_number} - {Path(original_name).stem}{ext}"
    return original_name


def organize_rips(source_dir: Path, auto_release: bool = False, acoustid_key: Optional[str] = None):
    """Organize audio files under `source_dir` into `organized/Artist/Album`.

    If `auto_release` is True and `acoustid_key` is provided, attempt to
    fingerprint tracks with AcoustID, find the best matching MusicBrainz
    release, apply album-level metadata, and then move files accordingly.
    """

    audio_extensions = {".wav", ".flac", ".mp3"}
    destination_root = source_dir / "organized"
    destination_root.mkdir(exist_ok=True)

    files = [p for p in sorted(source_dir.iterdir()) if p.is_file() and p.suffix.lower() in audio_extensions]

    if auto_release and acoustid_key and acoustid and musicbrainzngs:
        musicbrainzngs.set_useragent("cd_ripper", "0.1", "noreply@example.com")

        # Map recording MBID -> list of files
        rec_to_files = {}
        file_recs = {}
        for f in files:
            try:
                duration, fp = acoustid.fingerprint_file(str(f))
                res = acoustid.lookup(acoustid_key, fp, duration)
                results = res.get("results", [])
                recid = None
                for r in results:
                    recs = r.get("recordings") or []
                    if recs:
                        recid = recs[0].get("id")
                        break
                if not recid:
                    continue
                file_recs[f] = recid
                rec_to_files.setdefault(recid, []).append(f)
            except Exception:
                # best-effort: skip fingerprint failures
                continue

        # Tally candidate releases
        release_counts = {}
        for recid in rec_to_files:
            try:
                r = musicbrainzngs.get_recording_by_id(recid, includes=["releases"])
                releases = r.get("recording", {}).get("release-list") or []
                for rel in releases:
                    rid = rel.get("id")
                    if rid:
                        release_counts[rid] = release_counts.get(rid, 0) + 1
            except Exception:
                continue

        if release_counts:
            # choose release with most matching recordings
            best_release = max(release_counts.items(), key=lambda x: x[1])[0]
            try:
                rel = musicbrainzngs.get_release_by_id(best_release, includes=["artists", "labels", "recordings", "media"])['release']
                album_title = rel.get('title')
                release_date = rel.get('date') or ''
                artist_credit = rel.get('artist-credit') or []
                artists = []
                for a in artist_credit:
                    if isinstance(a, dict):
                        name = a.get('name') or (a.get('artist') or {}).get('name')
                        if name:
                            artists.append(name)
                    elif isinstance(a, str):
                        artists.append(a)
                album_artist = ', '.join(artists) if artists else 'Various Artists'

                # map recording id -> (title, track_no)
                track_map = {}
                media = rel.get('medium-list') or rel.get('media') or []
                for med in media:
                    tracks = med.get('track-list') or []
                    for t in tracks:
                        rec = t.get('recording') or {}
                        rid = rec.get('id')
                        title = t.get('title') or rec.get('title')
                        pos = t.get('position') or t.get('number') or ''
                        pos_str = str(pos) if pos is not None else ''
                        if rid:
                            track_map[rid] = (title or '', pos_str)

                # apply tags and move files
                from mutagen.wave import WAVE
                from mutagen.id3 import TIT2, TPE1, TALB, TRCK, TDRC

                for f, recid in file_recs.items():
                    title, track_no = track_map.get(recid, (None, None))
                    normalized_track = _normalize_track_number(track_no)
                    suffix = f.suffix.lower()
                    try:
                        if suffix == '.wav':
                            audio = WAVE(str(f))
                            if audio.tags is None:
                                audio.add_tags()
                            if title:
                                audio.tags.add(TIT2(encoding=3, text=title))
                            audio.tags.add(TPE1(encoding=3, text=album_artist))
                            audio.tags.add(TALB(encoding=3, text=album_title))
                            if release_date:
                                audio.tags.add(TDRC(encoding=3, text=release_date))
                            if track_no:
                                audio.tags.add(TRCK(encoding=3, text=track_no))
                            audio.save()
                        else:
                            audio = File(f)
                            if audio is None:
                                continue
                            tags = audio.tags or {}
                            if title:
                                tags['title'] = title
                            tags['artist'] = album_artist
                            tags['album'] = album_title
                            if release_date:
                                tags['date'] = release_date
                            if track_no:
                                tags['tracknumber'] = str(track_no)
                            audio.save()
                    except Exception:
                        # don't fail entire run on tag errors
                        pass

                    safe_artist = album_artist.replace('/','-')
                    safe_album = album_title.replace('/','-')
                    target_dir = destination_root / safe_artist / safe_album
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target_name = _build_target_filename(title, normalized_track, f.name)
                    try:
                        shutil.move(str(f), str(target_dir / target_name))
                    except Exception:
                        continue
            except Exception:
                # if release fetch fails, fall back to simple organize below
                pass

    # fallback/simple organization for remaining files (or when auto_release disabled)
    for file_path in files:
        # if file already moved into organized/Artist/Album, skip
        if destination_root in file_path.parents:
            continue
        if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
            audio = File(file_path, easy=True)
            if audio is None:
                continue

            artist = audio.get("artist", ["Unknown Artist"])[0]
            album = audio.get("album", ["Unknown Album"])[0]
            title = audio.get("title", [None])[0]
            track_no = audio.get("tracknumber", [None])[0]
            normalized_track = _normalize_track_number(track_no)

            artist_dir = destination_root / artist.strip()
            album_dir = artist_dir / album.strip()
            album_dir.mkdir(parents=True, exist_ok=True)

            target_name = _build_target_filename(title, normalized_track, file_path.name)
            try:
                shutil.move(str(file_path), str(album_dir / target_name))
            except Exception:
                continue
