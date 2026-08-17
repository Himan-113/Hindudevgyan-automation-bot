# -*- coding: utf-8 -*-
"""
video_creator.py â€” HinduDevGyan Reel Engine
Full FFmpeg pipeline: scene clips â†’ intro/outro â†’ BGM mix â†’ final 1080Ã—1920 MP4.
"""

import subprocess
import shutil
import os
import sys
from pathlib import Path
from datetime import datetime

from config import (
    REEL_WIDTH, REEL_HEIGHT, REEL_FPS,
    BGM_VOLUME_DB, TEMP_DIR, OUTPUT_DIR, MUSIC_DIR,
    BRAND_NAME, BRAND_WEBSITE,
    WINDOWS_FONTS, LINUX_FONTS
)
from voice_generator import get_audio_duration


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
FFMPEG_BIN, FFPROBE_BIN = None, None

def _find_ffmpeg():
    """Locate ffmpeg/ffprobe â€” PATH first, then known winget install dir."""
    global FFMPEG_BIN, FFPROBE_BIN
    if FFMPEG_BIN:
        return  # already found
    # 1) Try PATH
    if shutil.which("ffmpeg"):
        FFMPEG_BIN  = shutil.which("ffmpeg")
        FFPROBE_BIN = shutil.which("ffprobe") or "ffprobe"
        print(f"  âœ… FFmpeg (PATH): {FFMPEG_BIN}", flush=True)
        return
    # 2) Known winget install locations
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
        Path("C:/ffmpeg/bin"),
        Path("C:/Program Files/ffmpeg/bin"),
    ]
    for base in candidates:
        for exe in base.rglob("ffmpeg.exe"):
            FFMPEG_BIN  = str(exe)
            FFPROBE_BIN = str(exe.parent / "ffprobe.exe")
            print(f"  âœ… FFmpeg (found): {FFMPEG_BIN}", flush=True)
            return
    raise FileNotFoundError(
        "FFmpeg not found! Please restart PowerShell so the new PATH takes effect, "
        "or install FFmpeg: winget install Gyan.FFmpeg"
    )

_find_ffmpeg()



# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _find_font() -> str:
    """Find an available bold font on the system."""
    for path in WINDOWS_FONTS + LINUX_FONTS:
        if os.path.exists(path):
            return path
    return ""  # FFmpeg will use default


def _find_bgm() -> Path | None:
    """Find the first .mp3 file in the music assets folder."""
    for ext in ("*.mp3", "*.wav", "*.ogg", "*.m4a"):
        files = list(MUSIC_DIR.glob(ext))
        if files:
            return files[0]
    return None


def _escape_ffmpeg_text(text: str) -> str:
    """Escape special characters for FFmpeg drawtext filter."""
    # Replace characters that break FFmpeg filter syntax
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[").replace("]", "\\]")
    text = text.replace(",", "\\,")
    text = text.replace(";", "\\;")
    return text


def _get_effect_filter(effect: str, duration: float) -> str:
    """
    Return a zoompan FFmpeg filter string for the given effect.
    Each produces smooth movement over the scene duration.
    """
    fps = REEL_FPS
    frames = int(duration * fps)
    w, h = REEL_WIDTH, REEL_HEIGHT

    zoom_speed = 0.0008  # subtle zoom per frame

    effects = {
        "zoom_in": (
            f"zoompan=z='min(zoom+{zoom_speed},1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        ),
        "zoom_out": (
            f"zoompan=z='if(lte(zoom,1.0),1.3,max(1.0,zoom-{zoom_speed}))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        ),
        "pan_left": (
            f"zoompan=z=1.15:x='min(x+2,iw/4)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        ),
        "pan_right": (
            f"zoompan=z=1.15:x='max(x-2,0)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        ),
        "ken_burns": (
            f"zoompan=z='min(zoom+{zoom_speed/2},1.25)':x='iw/2-(iw/zoom/2)+sin(on/30)*20':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        ),
    }
    return effects.get(effect, effects["zoom_in"])


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SUBTITLE CARD GENERATOR (via FFmpeg drawtext)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _burn_subtitle_on_image(image_path: Path, subtitle: str, output_path: Path, font_path: str) -> Path:
    """
    Burn subtitle text onto image using PIL — supports Hindi/Devanagari perfectly.
    Draws a semi-transparent box + white text at bottom-third of image.
    Returns path to the composited image.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.open(image_path).convert("RGBA")
        img = img.resize((REEL_WIDTH, REEL_HEIGHT), Image.Resampling.LANCZOS)

        # Find best font
        font = None
        size = 48
        for fp in WINDOWS_FONTS + LINUX_FONTS:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, size)
                    break
                except Exception:
                    pass
        if font is None:
            try:
                font = ImageFont.load_default(size=size)
            except Exception:
                font = ImageFont.load_default()

        draw = ImageDraw.Draw(img)

        # Word-wrap subtitle to fit width
        words = subtitle.split()
        lines, current = [], ""
        for word in words:
            test = (current + " " + word).strip()
            # Estimate width (rough: each char ~28px at size 48)
            if len(test) * 28 < REEL_WIDTH - 80:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        lines = lines[:3]  # max 3 lines

        # Calculate text block height
        line_h = size + 12
        block_h = len(lines) * line_h + 40
        box_y1 = REEL_HEIGHT - block_h - 100
        box_y2 = REEL_HEIGHT - 60

        # Draw semi-transparent box
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        ov_draw.rectangle([(40, box_y1), (REEL_WIDTH - 40, box_y2)],
                          fill=(0, 0, 0, 160))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        # Draw each line centered
        y_text = box_y1 + 20
        for line in lines:
            # Estimate text width for centering
            try:
                bbox = font.getbbox(line)
                tw = bbox[2] - bbox[0]
            except Exception:
                tw = len(line) * 28
            x = max(50, (REEL_WIDTH - tw) // 2)
            draw.text((x, y_text), line, font=font, fill=(255, 255, 255),
                      stroke_width=2, stroke_fill=(0, 0, 0))
            y_text += line_h

        # Save as JPEG for FFmpeg
        img.convert("RGB").save(str(output_path), "JPEG", quality=90)
        return output_path
    except Exception as e:
        print(f"  ⚠️  Subtitle burn failed ({e}), using original image", flush=True)
        return image_path



# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SCENE CLIP GENERATOR
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_scene_clip(
    scene: dict,
    image_path: Path,
    voice_path: Path | None,
    reel_id: str,
    font_path: str
) -> Path | None:
    """
    Build one scene clip: image + effect + subtitle.
    Audio is attached if voice_path is provided.
    Returns path to scene MP4 or None.
    """
    scene_id = scene["id"]
    subtitle = scene.get("subtitle", scene.get("narration", ""))
    effect = scene.get("effect", "zoom_in")

    # Get actual voice duration if available, else use scene default
    if voice_path and voice_path.exists():
        duration = get_audio_duration(voice_path)
        duration = max(duration + 0.5, 3.0)  # add small buffer
    else:
        duration = float(scene.get("duration_sec", 5))

    output_path = TEMP_DIR / f"{reel_id}_clip_{scene_id:02d}.mp4"
    if output_path.exists():
        output_path.unlink()

    # Build zoompan filter
    zoompan = _get_effect_filter(effect, duration)

    # Burn subtitle onto image frame using PIL (supports Hindi reliably)
    subtitle_img_path = TEMP_DIR / f"{reel_id}_subimg_{scene_id:02d}.jpg"
    composited_image = _burn_subtitle_on_image(image_path, subtitle, subtitle_img_path, font_path)

    # Build FFmpeg command (simple scale+crop — no drawtext filter needed)
    cmd = [
        FFMPEG_BIN, "-y",
        "-loop", "1",
        "-i", str(composited_image),
    ]

    if voice_path and voice_path.exists():
        cmd += ["-i", str(voice_path)]

    # Video filters: scale → zoompan → format (no drawtext)
    vf = (
        f"scale={REEL_WIDTH}:{REEL_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={REEL_WIDTH}:{REEL_HEIGHT},"
        f"{zoompan},"
        f"format=yuv420p"
    )

    cmd += [
        "-vf", vf,
        "-t", str(duration),
        "-r", str(REEL_FPS),
    ]

    if voice_path and voice_path.exists():
        cmd += [
            "-map", "0:v",
            "-map", "1:a",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
        ]
    else:
        cmd += ["-an"]  # no audio for this clip

    cmd += [
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and output_path.exists():
        print(f"  âœ… Scene {scene_id} clip built ({duration:.1f}s)")
        return output_path
    else:
        print(f"  âŒ Scene {scene_id} clip failed:")
        print(f"     {result.stderr[-400:]}")
        return None


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# INTRO / OUTRO CARDS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_text_card(
    line1: str,
    line2: str,
    duration: float,
    output_path: Path,
    font_path: str,
    bg_color: str = "0x1A0A00",
    text_color: str = "0xD4A017"
) -> Path | None:
    """Build a simple branded text card using FFmpeg lavfi."""

    l1 = _escape_ffmpeg_text(line1)
    l2 = _escape_ffmpeg_text(line2)

    if font_path and os.path.exists(font_path):
        font_arg = f"fontfile='{font_path}'"
    else:
        font_arg = "font=Arial"

    vf = (
        f"color={bg_color}:size={REEL_WIDTH}x{REEL_HEIGHT}:rate={REEL_FPS},"
        f"drawtext={font_arg}:text='{l1}':fontsize=80:fontcolor={text_color}:"
        f"x=(w-text_w)/2:y=(h/2-100):borderw=3:bordercolor=black@0.5,"
        f"drawtext={font_arg}:text='{l2}':fontsize=50:fontcolor=white:"
        f"x=(w-text_w)/2:y=(h/2+20):borderw=2:bordercolor=black@0.5,"
        f"format=yuv420p"
    )

    cmd = [
        FFMPEG_BIN, "-y",
        "-f", "lavfi",
        "-i", f"color={bg_color}:size={REEL_WIDTH}x{REEL_HEIGHT}:rate={REEL_FPS}",
        "-vf", vf,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-an",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and output_path.exists():
        return output_path
    else:
        print(f"  âš ï¸  Text card failed: {result.stderr[-200:]}")
        return None


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FADE TRANSITION HELPER
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def add_fade(clip_path: Path, fade_in: bool = True, fade_out: bool = True,
             duration: float = 0.4) -> Path:
    """Apply fade-in/fade-out to a clip."""
    output = clip_path.parent / (clip_path.stem + "_faded.mp4")

    # Get clip duration
    clip_dur = get_audio_duration(clip_path)

    vf_parts = []
    af_parts = []
    if fade_in:
        vf_parts.append(f"fade=t=in:st=0:d={duration}")
        af_parts.append(f"afade=t=in:st=0:d={duration}")
    if fade_out and clip_dur > duration:
        vf_parts.append(f"fade=t=out:st={clip_dur - duration}:d={duration}")
        af_parts.append(f"afade=t=out:st={clip_dur - duration}:d={duration}")

    vf = ",".join(vf_parts) if vf_parts else "null"
    af = ",".join(af_parts) if af_parts else "anull"

    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(clip_path),
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        str(output)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 and output.exists():
        return output
    return clip_path  # return original if fade fails


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# FINAL ASSEMBLY
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def assemble_reel(
    scene_clips: list[Path | None],
    reel_id: str,
    script: dict,
    font_path: str
) -> Path | None:
    """
    Assemble all scene clips + intro + outro + BGM into final reel.
    Returns path to final MP4.
    """
    print(f"\nðŸŽžï¸  Assembling final reel...")

    valid_clips = [c for c in scene_clips if c and c.exists()]
    if not valid_clips:
        print("  âŒ No valid scene clips to assemble")
        return None

    # â”€â”€ Build intro card â”€â”€
    intro_path = TEMP_DIR / f"{reel_id}_intro.mp4"
    intro = build_text_card(
        line1=f"ðŸ•‰ï¸  {BRAND_NAME}",
        line2=script.get("title", ""),
        duration=2.5,
        output_path=intro_path,
        font_path=font_path
    )

    # â”€â”€ Build outro card â”€â”€
    outro_path = TEMP_DIR / f"{reel_id}_outro.mp4"
    outro = build_text_card(
        line1="Follow for More",
        line2=f"ðŸŒ {BRAND_WEBSITE}",
        duration=3.0,
        output_path=outro_path,
        font_path=font_path
    )

    # â”€â”€ Concat list â”€â”€
    all_clips = []
    if intro and intro.exists():
        all_clips.append(intro)
    all_clips.extend(valid_clips)
    if outro and outro.exists():
        all_clips.append(outro)

    # Write concat file
    concat_file = TEMP_DIR / f"{reel_id}_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in all_clips:
            # Forward slashes required even on Windows for FFmpeg
            f.write(f"file '{clip.as_posix()}'\n")

    # â”€â”€ Concat all clips â”€â”€
    raw_output = TEMP_DIR / f"{reel_id}_raw.mp4"
    concat_cmd = [
        FFMPEG_BIN, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "128k",
        "-r", str(REEL_FPS),
        str(raw_output)
    ]
    result = subprocess.run(concat_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  âŒ Concat failed: {result.stderr[-400:]}")
        return None
    print(f"  âœ… Concatenated {len(all_clips)} clips")

    # â”€â”€ Mix BGM â”€â”€
    bgm_path = _find_bgm()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_output = OUTPUT_DIR / f"reel_{timestamp}_{reel_id[:8]}.mp4"

    if bgm_path and bgm_path.exists():
        print(f"  ðŸŽµ Mixing BGM: {bgm_path.name}")
        # Get total reel duration
        total_dur = get_audio_duration(raw_output)

        mix_cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(raw_output),
            "-stream_loop", "-1",  # loop BGM
            "-i", str(bgm_path),
            "-t", str(total_dur),
            "-filter_complex",
            f"[0:a]volume=1.0[va];[1:a]volume={_db_to_linear(BGM_VOLUME_DB):.4f},atrim=0:{total_dur}[bgm];[va][bgm]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(final_output)
        ]
        result = subprocess.run(mix_cmd, capture_output=True, text=True)
        if result.returncode == 0 and final_output.exists():
            print(f"  âœ… BGM mixed successfully")
        else:
            print(f"  âš ï¸  BGM mix failed, using raw audio")
            shutil.copy(raw_output, final_output)
    else:
        print("  â„¹ï¸  No BGM found. Place .mp3 files in reel_engine/assets/music/")
        shutil.copy(raw_output, final_output)

    if final_output.exists():
        size_mb = final_output.stat().st_size / 1024 / 1024
        print(f"\nâœ… FINAL REEL: {final_output.name} ({size_mb:.1f} MB)")
        return final_output

    return None


def _db_to_linear(db: float) -> float:
    """Convert dB to linear scale for FFmpeg volume filter."""
    return 10 ** (db / 20)


def cleanup_temp(reel_id: str):
    """Remove all temp files for a specific reel_id."""
    for f in TEMP_DIR.glob(f"{reel_id}*"):
        try:
            f.unlink()
        except Exception:
            pass
    print(f"  ðŸ§¹ Cleaned temp files for {reel_id}")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MAIN ENTRY POINT
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def create_reel(
    script: dict,
    image_paths: list[Path | None],
    voice_paths: list[Path | None],
    reel_id: str
) -> Path | None:
    """
    Full reel creation pipeline.
    Takes script, image paths, voice paths â†’ returns final MP4 path.
    """
    font_path = _find_font()
    print(f"  ðŸ”¤ Font: {font_path or 'system default'}")

    scenes = script.get("scenes", [])
    if not scenes:
        print("  âŒ No scenes in script")
        return None

    # Build one clip per scene
    scene_clips = []
    for i, scene in enumerate(scenes):
        img = image_paths[i] if i < len(image_paths) else None
        voice = voice_paths[i] if i < len(voice_paths) else None

        if img is None or not img.exists():
            print(f"  âš ï¸  Skipping scene {scene['id']} â€” no image")
            scene_clips.append(None)
            continue

        clip = build_scene_clip(scene, img, voice, reel_id, font_path)
        scene_clips.append(clip)

    # Assemble final reel
    return assemble_reel(scene_clips, reel_id, script, font_path)
