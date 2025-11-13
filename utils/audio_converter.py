import os
import subprocess
import tempfile
import uuid


def convert_to_wav(input_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """
    Convert browser audio (WebM/Opus fragments) to 16 kHz mono WAV.
    
    MediaRecorder sends WebM fragments that need special handling.
    Uses FFmpeg with format hints and error tolerance for streaming WebM.
    """
    if not input_bytes or len(input_bytes) < 4000:
        raise Exception("insufficient data")

    tmp_dir = tempfile.gettempdir()
    in_path = os.path.join(tmp_dir, f"nika_in_{uuid.uuid4().hex}.webm")
    out_path = os.path.join(tmp_dir, f"nika_out_{uuid.uuid4().hex}.wav")

    try:
        # Write input bytes to file
        with open(in_path, "wb") as f:
            f.write(input_bytes)
            f.flush()

        # FFmpeg command with WebM format handling
        # Key flags for handling WebM fragments:
        # -f webm: Force WebM format (helps with fragments)
        # -fflags +genpts: Generate PTS for streams without timestamps
        # -err_detect ignore_err: Ignore errors in stream
        # -analyzeduration and -probesize: Quick analysis for streaming
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-nostdin",
            "-y",
            "-f", "webm",           # Force WebM format
            "-fflags", "+genpts+discardcorrupt",  # Generate PTS, discard corrupt
            "-err_detect", "ignore_err",
            "-analyzeduration", "1000000",  # 1 second analysis
            "-probesize", "1000000",        # 1 MB probe size
            "-i", in_path,
            "-ac", "1",              # mono
            "-ar", "16000",          # 16kHz
            "-vn",                   # No video
            "-f", "wav",             # Output WAV format
            out_path,
        ]

        success = False
        stderr_output = None
        for attempt in range(2):
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )
            
            stderr_output = result.stderr.decode('utf-8', errors='ignore') if result.stderr else ""

            if result.returncode == 0 and os.path.exists(out_path):
                size = os.path.getsize(out_path)
                if size > 2000:
                    success = True
                    break
            elif attempt == 0:
                # On first failure, check if it's a format issue
                # Sometimes FFmpeg needs the data to be treated as a stream
                # Try with pipe input approach on second attempt
                pass

        if not success:
            # Check stderr for specific errors
            if stderr_output:
                if "Invalid data found" in stderr_output or "moov atom not found" in stderr_output:
                    raise Exception("invalid fragment - incomplete WebM data")
                elif "End of file" in stderr_output:
                    raise Exception("invalid fragment - incomplete WebM data")
            raise Exception("invalid fragment")

        return out_path

    except subprocess.TimeoutExpired:
        print("⚠️ FFmpeg timeout while converting fragment")
        raise Exception("ffmpeg timeout")
    except Exception as e:
        # Re-raise our custom exceptions
        if "invalid fragment" in str(e) or "insufficient data" in str(e):
            raise
        # Log unexpected errors
        error_msg = str(e).lower()
        expected_errors = ["ffmpeg skipped", "timeout"]
        if not any(err in error_msg for err in expected_errors):
            print(f"⚠️ FFmpeg conversion error: {e}")
        raise
    finally:
        # Clean input file only; keep output for next stage
        if os.path.exists(in_path):
            try:
                os.remove(in_path)
            except Exception:
                pass
