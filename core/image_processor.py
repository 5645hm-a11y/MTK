"""Image processing utilities for MTK partition images.

This module implements sparse image detection and sparse-to-raw conversion
using simg2img so EXT4 images can be mounted/read by downstream tooling.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

SPARSE_HEADER_MAGIC = 0xED26FF3A


class ImageProcessor:
    """Process Android/MTK partition image files."""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.simg2img_path = self._find_simg2img()

    def _find_simg2img(self) -> Optional[Path]:
        """Resolve simg2img executable path."""
        configured = self.config.get("tools.simg2img_path")
        if configured:
            p = Path(configured)
            if p.exists():
                return p

        tools_dir = Path(self.config.get("tools_dir", "./tools"))
        candidates = [
            tools_dir / "simg2img.exe",
            tools_dir / "simg2img" / "simg2img.exe",
            tools_dir / "android-utils" / "simg2img.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate

        from_path = shutil.which("simg2img")
        if from_path:
            return Path(from_path)

        self.logger.warning("simg2img was not found. Sparse conversion will be unavailable.")
        return None

    def can_convert_sparse(self) -> bool:
        return self.simg2img_path is not None and self.simg2img_path.exists()

    def is_sparse_image(self, image_path: Path) -> bool:
        """Return True if image has Android sparse magic header."""
        try:
            with image_path.open("rb") as f:
                header = f.read(4)
            if len(header) != 4:
                return False
            magic = int.from_bytes(header, byteorder="little", signed=False)
            return magic == SPARSE_HEADER_MAGIC
        except Exception as e:
            self.logger.debug(f"Failed sparse check for {image_path}: {e}")
            return False

    def convert_sparse_to_raw(self, sparse_img: Path, raw_img: Path) -> Path:
        """Convert sparse image to raw EXT4 image using simg2img."""
        if not self.can_convert_sparse():
            raise RuntimeError("simg2img is not available")

        raw_img.parent.mkdir(parents=True, exist_ok=True)
        cmd = [str(self.simg2img_path), str(sparse_img), str(raw_img)]
        self.logger.info("Converting sparse image with simg2img: %s", sparse_img.name)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "simg2img failed")
        return raw_img

    def ensure_raw_ext4(self, image_path: Path, temp_dir: Path) -> Path:
        """Ensure image is raw (convert if sparse), return resulting path."""
        if not image_path.exists():
            raise FileNotFoundError(str(image_path))

        if not self.is_sparse_image(image_path):
            return image_path

        if not self.can_convert_sparse():
            raise RuntimeError("Image is sparse but simg2img is missing")

        out_name = f"{image_path.stem}.raw.img"
        out_path = temp_dir / out_name
        return self.convert_sparse_to_raw(image_path, out_path)

    def prepare_partition_images(self, partitions: Dict[str, str], temp_dir: Path) -> Dict[str, str]:
        """Prepare mountable image set by converting known sparse partitions to raw.

        Only known filesystem partitions are converted automatically.
        """
        prepared = dict(partitions)
        fs_partitions = ("system", "vendor", "product", "odm")

        for part_name, file_path in partitions.items():
            lower = part_name.lower()
            if not any(lower.startswith(p) for p in fs_partitions):
                continue

            src = Path(file_path)
            try:
                prepared_path = self.ensure_raw_ext4(src, temp_dir)
                prepared[part_name] = str(prepared_path)
                if prepared_path != src:
                    self.logger.info("Prepared %s as raw EXT4: %s", part_name, prepared_path)
            except Exception as e:
                # Keep original path if conversion fails; caller can decide policy.
                self.logger.warning("Failed to prepare %s (%s): %s", part_name, src.name, e)

        return prepared
