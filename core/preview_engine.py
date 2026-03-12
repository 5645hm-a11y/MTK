"""Static preview engine for extracted Android filesystem content.

This engine builds lightweight preview metadata by scanning common Android
paths (framework, launcher apps, icon resources) from an extracted filesystem
root directory.
"""

from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class StaticPreviewModel:
    framework_apk: Optional[str]
    launcher_apk: Optional[str]
    icon_count: int
    wallpaper_candidates: List[str]
    accent_color_hint: Optional[str]


class PreviewEngine:
    """Build static UI preview metadata from extracted filesystem trees."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def build_static_preview(self, fs_root: Path) -> Optional[StaticPreviewModel]:
        if not fs_root.exists() or not fs_root.is_dir():
            return None

        framework = self._find_framework_apk(fs_root)
        launcher = self._find_launcher_apk(fs_root)
        icons = self._count_launcher_icons(launcher) if launcher else 0
        wallpapers = self._find_wallpapers(fs_root)

        return StaticPreviewModel(
            framework_apk=str(framework) if framework else None,
            launcher_apk=str(launcher) if launcher else None,
            icon_count=icons,
            wallpaper_candidates=wallpapers,
            accent_color_hint=None,
        )

    def _find_framework_apk(self, fs_root: Path) -> Optional[Path]:
        candidates = [
            fs_root / "system" / "framework" / "framework-res.apk",
            fs_root / "system_ext" / "framework" / "framework-res.apk",
            fs_root / "framework" / "framework-res.apk",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def _find_launcher_apk(self, fs_root: Path) -> Optional[Path]:
        search_roots = [
            fs_root / "system" / "app",
            fs_root / "system" / "priv-app",
            fs_root / "product" / "app",
            fs_root / "product" / "priv-app",
            fs_root / "app",
            fs_root / "priv-app",
        ]
        names = (
            "launcher", "quickstep", "trebuchet", "pixel", "home"
        )

        for root in search_roots:
            if not root.exists():
                continue
            for apk in root.rglob("*.apk"):
                low = apk.name.lower()
                if any(n in low for n in names):
                    return apk
        return None

    def _count_launcher_icons(self, apk_path: Path) -> int:
        try:
            with zipfile.ZipFile(apk_path, "r") as zf:
                return sum(
                    1
                    for n in zf.namelist()
                    if n.startswith("res/mipmap") and n.endswith(".png")
                )
        except Exception as e:
            self.logger.debug("Failed to parse launcher apk %s: %s", apk_path, e)
            return 0

    def _find_wallpapers(self, fs_root: Path) -> List[str]:
        results: List[str] = []
        search_roots = [
            fs_root / "system",
            fs_root / "product",
            fs_root / "vendor",
            fs_root,
        ]
        for root in search_roots:
            if not root.exists():
                continue
            for file in root.rglob("*wallpaper*"):
                if file.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                    results.append(str(file))
                if len(results) >= 20:
                    return results
        return results

    def model_to_dict(self, model: Optional[StaticPreviewModel]) -> Dict[str, object]:
        if model is None:
            return {}
        return {
            "framework_apk": model.framework_apk,
            "launcher_apk": model.launcher_apk,
            "icon_count": model.icon_count,
            "wallpaper_candidates": model.wallpaper_candidates,
            "accent_color_hint": model.accent_color_hint,
        }
