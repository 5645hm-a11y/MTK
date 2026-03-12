"""Firmware workflow orchestration.

Implements layered workflow:
Input -> Validation -> Extraction/Preparation -> Rendering metadata
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

from core.ext4_extractor import Ext4Extractor
from core.image_processor import ImageProcessor
from core.preview_engine import PreviewEngine
from core.scatter_parser import ScatterParser


class WorkflowEngine:
    """High-level data flow for imported IMG/scatter based projects."""

    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.image_processor = ImageProcessor(config)
        self.scatter_parser = ScatterParser()
        self.ext4_extractor = Ext4Extractor()
        self.preview_engine = PreviewEngine()

    def validate_input(self, partitions: Dict[str, str], scatter_path: Optional[Path] = None) -> Dict[str, object]:
        existing = []
        missing = []
        for name, p in partitions.items():
            if Path(p).exists():
                existing.append(name)
            else:
                missing.append(name)

        sparse = []
        for name, p in partitions.items():
            path = Path(p)
            if path.exists() and self.image_processor.is_sparse_image(path):
                sparse.append(name)

        scatter_ok = scatter_path.exists() if scatter_path else False
        scatter_details = {
            "partition_count": 0,
            "missing_in_scatter": [],
            "missing_img_from_scatter": [],
        }
        if scatter_ok:
            try:
                parsed = self.scatter_parser.parse(scatter_path)
                scatter_map = self.scatter_parser.to_map(parsed)
                imported_names = {name.lower() for name in partitions.keys()}
                scatter_names = set(scatter_map.keys())

                missing_in_scatter = sorted([n for n in imported_names if n not in scatter_names])
                missing_img_from_scatter = sorted([n for n in scatter_names if n not in imported_names])

                scatter_details = {
                    "partition_count": len(parsed),
                    "missing_in_scatter": missing_in_scatter,
                    "missing_img_from_scatter": missing_img_from_scatter,
                }
            except Exception as e:
                self.logger.warning("Scatter parse failed: %s", e)

        report = {
            "ok": len(missing) == 0,
            "existing_count": len(existing),
            "missing": missing,
            "sparse_partitions": sparse,
            "scatter_provided": scatter_path is not None,
            "scatter_exists": scatter_ok,
            "scatter_details": scatter_details,
            "android_version": self._infer_android_version(partitions),
        }
        return report

    def prepare_images(self, partitions: Dict[str, str], workspace_dir: Path) -> Dict[str, str]:
        temp_dir = workspace_dir / ".tmp" / "raw_images"
        prepared = self.image_processor.prepare_partition_images(partitions, temp_dir)

        # Extract EXT4 trees (best-effort) for static preview rendering.
        extracted_root = workspace_dir / "extracted_fs"
        targets = ["system", "vendor", "product", "odm"]
        for name in targets:
            if name not in prepared:
                continue
            src = Path(prepared[name])
            if not src.exists():
                continue
            out_dir = extracted_root / name
            ok = self.ext4_extractor.extract_raw_ext4(src, out_dir)
            if ok:
                self.logger.info("Extracted %s filesystem to %s", name, out_dir)

        return prepared

    def build_preview_metadata(self, workspace_dir: Path) -> Dict[str, object]:
        """Build static preview metadata from extracted filesystem roots if present."""
        fs_candidates = [
            workspace_dir / "extracted_fs",
            workspace_dir / "extracted_fs" / "system",
            workspace_dir / "extracted_fs" / "vendor",
            workspace_dir / "mounted_system",
            workspace_dir / "system_root",
        ]
        for fs_root in fs_candidates:
            model = self.preview_engine.build_static_preview(fs_root)
            if model is not None:
                return self.preview_engine.model_to_dict(model)
        return {}

    def _infer_android_version(self, partitions: Dict[str, str]) -> str:
        # Lightweight heuristic from partition layout.
        names = {k.lower() for k in partitions.keys()}
        if "super" in names:
            return "Android 10+ (dynamic partitions likely)"
        if "vendor" in names and "product" in names:
            return "Android 9+"
        if "vendor" in names:
            return "Android 8+"
        return "Unknown"
