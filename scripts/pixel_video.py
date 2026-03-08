#!/usr/bin/env python3
"""
将 videos 目录下的视频处理为像素风格并输出到 videos/pixel/。

像素效果：先缩小再最近邻放大，得到块状像素画风格。
输出使用 ffmpeg 编码为 H.264 (yuv420p)，保证 Electron/Chromium 可播放。

依赖：pip install opencv-python
      pip install imageio-ffmpeg  （可选，用于 H.264 编码；否则需系统安装 ffmpeg 并加入 PATH）
运行：python scripts/pixel_video.py
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import cv2
except ImportError:
    print("请先安装: pip install opencv-python", file=sys.stderr)
    sys.exit(1)


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_ffmpeg_path() -> str | None:
    """优先使用 imageio-ffmpeg 提供的 ffmpeg，否则查系统 PATH。"""
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return exe
    except Exception:
        pass
    return shutil.which("ffmpeg")


def _ffmpeg_available() -> bool:
    return _get_ffmpeg_path() is not None


def _encode_h264_for_web(input_mp4: Path, output_mp4: Path, fps: float, w: int, h: int) -> None:
    """用 ffmpeg 将 MP4 转为 H.264 yuv420p，兼容 Electron/浏览器。"""
    ffmpeg_exe = _get_ffmpeg_path()
    if not ffmpeg_exe:
        raise RuntimeError("未找到 ffmpeg，请安装 imageio-ffmpeg 或系统 ffmpeg")
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(input_mp4),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-an",
        "-r", str(round(fps, 2)),
        str(output_mp4),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 编码失败: {result.stderr or result.stdout}")


def process_frame_pixel(frame, pixel_scale: int):
    """将一帧转为像素风格：缩小再最近邻放大。"""
    h, w = frame.shape[:2]
    pw = max(1, w // pixel_scale)
    ph = max(1, h // pixel_scale)
    small = cv2.resize(frame, (pw, ph), interpolation=cv2.INTER_NEAREST)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def process_video(
    input_path: Path,
    output_path: Path,
    pixel_scale: int = 8,
    use_ffmpeg: bool = True,
) -> None:
    """处理单个视频为像素风格，输出分辨率与输入一致，默认用 ffmpeg 转为 H.264。"""
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 若元数据无宽高，从第一帧取
    if w <= 0 or h <= 0:
        ret, frame = cap.read()
        if not ret or frame is None:
            raise RuntimeError(f"无法读取首帧: {input_path}")
        h, w = frame.shape[:2]
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    if use_ffmpeg and _ffmpeg_available():
        tmp = output_path.with_suffix(output_path.suffix + ".tmp.mp4")
    else:
        tmp = output_path

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(tmp), fourcc, fps, (w, h))
    if not out.isOpened():
        cap.release()
        raise RuntimeError(f"无法创建输出: {tmp}")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(process_frame_pixel(frame, pixel_scale))
    finally:
        cap.release()
        out.release()

    if use_ffmpeg and _ffmpeg_available():
        try:
            _encode_h264_for_web(tmp, output_path, fps, w, h)
        finally:
            tmp.unlink(missing_ok=True)
        print(f"已输出 (H.264): {output_path} ({w}x{h})")
    else:
        if use_ffmpeg:
            print("未检测到 ffmpeg，已输出为 mp4v（Electron 可能无法播放）:", output_path, file=sys.stderr)
        print(f"已输出: {output_path} ({w}x{h})")


def main() -> None:
    root = get_project_root()
    videos_dir = root / "videos"
    pixel_dir = videos_dir / "pixel"

    parser = argparse.ArgumentParser(description="将 videos 转为像素风格视频")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=videos_dir,
        help="输入视频目录",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=pixel_dir,
        help="输出目录 (默认 videos/pixel)",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=8,
        help="像素块大小，越大越糊 (默认 8)",
    )
    parser.add_argument(
        "--no-ffmpeg",
        action="store_true",
        help="不使用 ffmpeg，仅用 OpenCV 输出（Electron 可能无法播放）",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="指定文件则只处理这些，否则处理 input-dir 下所有 .mp4",
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        print(f"输入目录不存在: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.files:
        paths = [Path(p) for p in args.files]
    else:
        paths = list(args.input_dir.glob("*.mp4"))

    if not paths:
        print("未找到 .mp4 文件", file=sys.stderr)
        sys.exit(1)

    for p in paths:
        if not p.is_absolute():
            p = args.input_dir / p
        if not p.exists():
            print(f"跳过不存在的文件: {p}", file=sys.stderr)
            continue
        out = args.output_dir / p.name
        try:
            process_video(p, out, pixel_scale=args.scale, use_ffmpeg=not args.no_ffmpeg)
        except Exception as e:
            print(f"处理失败 {p}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
