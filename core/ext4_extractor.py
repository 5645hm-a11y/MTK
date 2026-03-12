"""EXT4 raw extraction support (Windows + WSL).

Uses WSL debugfs to export filesystem content from raw EXT4 images without
requiring privileged mount on Windows host.
"""

from __future__ import annotations

import logging
import shlex
import subprocess
from pathlib import Path
from typing import Optional


class Ext4Extractor:
    """Extract EXT4 raw images using WSL debugfs when available."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def is_wsl_available(self) -> bool:
        try:
            result = subprocess.run(["wsl.exe", "--status"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def _to_wsl_path(self, windows_path: Path) -> str:
        try:
            result = subprocess.run(
                ["wsl.exe", "wslpath", "-a", str(windows_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "wslpath failed")
            return result.stdout.strip()
        except Exception as e:
            raise RuntimeError(f"Failed converting path for WSL: {windows_path} ({e})")

    def _has_debugfs(self) -> bool:
        result = subprocess.run(
            ["wsl.exe", "bash", "-lc", "command -v debugfs >/dev/null 2>&1"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0

    def extract_raw_ext4(self, image_path: Path, output_dir: Path) -> bool:
        """Extract full EXT4 tree into output_dir via `debugfs rdump`."""
        try:
            if not image_path.exists():
                self.logger.warning("Image not found for EXT4 extraction: %s", image_path)
                return False

            if not self.is_wsl_available():
                self.logger.warning("WSL not available; cannot extract EXT4")
                return False
            if not self._has_debugfs():
                self.logger.warning("debugfs missing in WSL (install e2fsprogs)")
                return False

            output_dir.mkdir(parents=True, exist_ok=True)

            img_wsl = self._to_wsl_path(image_path)
            out_wsl = self._to_wsl_path(output_dir)

            # Note: rdump / <dir> recursively extracts filesystem tree.
            cmd = (
                f"mkdir -p {shlex.quote(out_wsl)} && "
                f"debugfs -R {shlex.quote('rdump / ' + out_wsl)} {shlex.quote(img_wsl)}"
            )

            self.logger.info("Extracting EXT4 image via WSL debugfs: %s", image_path.name)
            result = subprocess.run(
                ["wsl.exe", "bash", "-lc", cmd],
                capture_output=True,
                text=True,
                timeout=1800,
            )
            if result.returncode != 0:
                self.logger.warning("debugfs extraction failed: %s", (result.stderr or result.stdout).strip())
                return False

            return True
        except Exception as e:
            self.logger.warning("EXT4 extraction crashed but was ignored safely: %s", e)
            return False
