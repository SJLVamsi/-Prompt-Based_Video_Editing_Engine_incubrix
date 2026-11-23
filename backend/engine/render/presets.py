"""Render presets: H.264 + AAC tails."""
PRESETS = {
    "preview": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p"],
    "720p": ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"],
    "1080p": ["-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p"],
    "short": ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p"],
}
AUDIO = ["-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2"]
MUX = ["-movflags", "+faststart", "-avoid_negative_ts", "make_zero"]
