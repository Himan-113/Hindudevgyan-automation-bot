"""
voice_generator.py â€” HinduDevGyan Reel Engine
Generates Hindi narration audio using Edge-TTS (Microsoft, free).
Combines all scene narrations into one continuous MP3.
"""

import asyncio
import subprocess
from pathlib import Path
import edge_tts
from config import VOICE_DEFAULT, TEMP_DIR

# ── FFmpeg path (reuse from video_creator if available, else find it) ──
import shutil as _shutil, os as _os
from pathlib import Path as _Path
def _get_ffmpeg_bins():
    if _shutil.which('ffmpeg'):
        return _shutil.which('ffmpeg'), _shutil.which('ffprobe') or 'ffprobe'
    base = _Path(_os.environ.get('LOCALAPPDATA','')) / 'Microsoft' / 'WinGet' / 'Packages'
    for exe in base.rglob('ffmpeg.exe'):
        return str(exe), str(exe.parent / 'ffprobe.exe')
    return 'ffmpeg', 'ffprobe'
_FFMPEG_BIN, _FFPROBE_BIN = _get_ffmpeg_bins()


async def _generate_audio_async(text: str, output_path: Path, voice: str):
    """Async Edge-TTS generation."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


def generate_voice(text: str, output_path: Path, voice: str = VOICE_DEFAULT) -> bool:
    """
    Generate a single audio file from text using Edge-TTS.
    Returns True on success.
    """
    try:
        asyncio.run(_generate_audio_async(text, output_path, voice))
        if output_path.exists() and output_path.stat().st_size > 1000:
            return True
        return False
    except Exception as e:
        print(f"  âŒ Voice generation failed: {e}")
        return False


def generate_scene_voices(scenes: list[dict], reel_id: str, voice: str = VOICE_DEFAULT) -> list[Path | None]:
    """
    Generate one audio file per scene narration.
    Returns list of Paths (None for failed scenes).
    """
    print(f"\nðŸŽ™ï¸  Generating Hindi narration ({voice})...")
    audio_paths = []

    for scene in scenes:
        narration = scene.get("narration", "").strip()
        if not narration:
            audio_paths.append(None)
            continue

        filename = f"{reel_id}_scene_{scene['id']:02d}_voice.mp3"
        output_path = TEMP_DIR / filename

        if output_path.exists() and output_path.stat().st_size > 500:
            print(f"  â™»ï¸  Reusing: {filename}")
            audio_paths.append(output_path)
            continue

        print(f"  ðŸ—£ï¸  Scene {scene['id']}: {narration[:50]}...")
        success = generate_voice(narration, output_path, voice)
        audio_paths.append(output_path if success else None)

    success = sum(1 for p in audio_paths if p is not None)
    print(f"  ðŸ“Š Voice: {success}/{len(scenes)} scenes have audio")
    return audio_paths


def combine_voices_with_gaps(audio_paths: list[Path | None], reel_id: str, gap_ms: int = 300) -> Path | None:
    """
    Concatenate all scene audio files into one track using FFmpeg.
    Adds a small gap between scenes for natural pacing.
    Returns path to combined MP3 or None.
    """
    valid = [(i, p) for i, p in enumerate(audio_paths) if p and p.exists()]
    if not valid:
        print("  âŒ No valid audio files to combine")
        return None

    if len(valid) == 1:
        return valid[0][1]

    # Write FFmpeg concat list
    concat_file = TEMP_DIR / f"{reel_id}_voice_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for i, (_, path) in enumerate(valid):
            f.write(f"file '{path.as_posix()}'\n")
            if i < len(valid) - 1 and gap_ms > 0:
                # We'll handle gaps via scene timing in video_creator instead
                pass

    output_path = TEMP_DIR / f"{reel_id}_voice_combined.mp3"

    cmd = [
        _FFMPEG_BIN, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-acodec", "libmp3lame",
        "-q:a", "2",
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and output_path.exists():
            print(f"  âœ… Combined voice: {output_path.name}")
            return output_path
        else:
            print(f"  âŒ FFmpeg combine error: {result.stderr[-300:]}")
            return None
    except FileNotFoundError:
        print("  âŒ FFmpeg not found. Please install FFmpeg and restart your shell.")
        return None


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using FFprobe."""
    try:
        result = subprocess.run(
            [_FFPROBE_BIN, "-v", "error", "-show_entries",
             "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
             str(audio_path)],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 5.0  # Default fallback
