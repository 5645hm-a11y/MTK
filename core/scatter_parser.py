"""MediaTek scatter file parser for validation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ScatterPartition:
    partition_name: str
    file_name: str
    is_download: bool
    linear_start_addr: Optional[str]
    partition_size: Optional[str]


class ScatterParser:
    """Parse MTK scatter text files into structured partition records."""

    def parse(self, scatter_path: Path) -> List[ScatterPartition]:
        if not scatter_path.exists():
            raise FileNotFoundError(str(scatter_path))

        lines = scatter_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        partitions: List[ScatterPartition] = []
        current: Dict[str, str] = {}

        def flush_current() -> None:
            if not current:
                return
            pname = current.get("partition_name", "").strip()
            if not pname:
                current.clear()
                return
            fname = current.get("file_name", "").strip()
            is_download = current.get("is_download", "false").strip().lower() == "true"
            partitions.append(
                ScatterPartition(
                    partition_name=pname,
                    file_name=fname,
                    is_download=is_download,
                    linear_start_addr=current.get("linear_start_addr"),
                    partition_size=current.get("partition_size"),
                )
            )
            current.clear()

        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("- partition_index"):
                flush_current()
                continue

            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            current[key.strip()] = value.strip()

        flush_current()
        return partitions

    def to_map(self, partitions: List[ScatterPartition]) -> Dict[str, ScatterPartition]:
        return {p.partition_name.lower(): p for p in partitions}
