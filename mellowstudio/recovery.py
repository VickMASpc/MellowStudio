"""Per-document recovery snapshots, independent of Qt and editable project files.

Each recovery is a separate validated project archive with metadata. A failed
write never destroys another recovery, and an unsaved document gets an isolated
session key. Recovery is intentionally opt-in on startup.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import time
from uuid import uuid4

from .model import Document, project_save


@dataclass(frozen=True)
class RecoveryEntry:
    token: str
    project_name: str
    project_path: str | None
    created_at: float
    archive: Path
    manifest: Path


class RecoveryStore:
    def __init__(self, root: str | Path, keep_per_document: int = 4):
        self.root = Path(root)
        self.keep_per_document = max(1, int(keep_per_document))

    @staticmethod
    def token_for(project_path: str | Path | None, session_id: str) -> str:
        if project_path is None:
            identity = 'unsaved:' + session_id
        else:
            # Windows paths have case-insensitive identity; resolve is still safe
            # for nonexistent paths as used by Save As.
            identity = 'file:' + os.path.normcase(str(Path(project_path).resolve()))
            if os.name == 'nt':
                identity = identity.casefold()
        return sha256(identity.encode('utf-8')).hexdigest()[:24]

    def write(self, doc: Document, project_path: str | Path | None,
              session_id: str) -> RecoveryEntry:
        self.root.mkdir(parents=True, exist_ok=True)
        token = self.token_for(project_path, session_id)
        timestamp = time.time()
        stem = f'{token}-{time.time_ns()}-{uuid4().hex[:8]}'
        archive = self.root / (stem + '.mellowzip')
        manifest = self.root / (stem + '.json')
        payload = {
            'schema': 1,
            'token': token,
            'project_name': doc.name,
            'project_path': str(Path(project_path).resolve()) if project_path else None,
            'created_at': timestamp,
            'archive': archive.name,
            'logical_size': [doc.width, doc.height],
        }
        metadata_tmp = None
        try:
            project_save(doc, archive, backup=False)
            # The manifest is published only once the archive was saved.
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                    dir=self.root, suffix='.json.tmp', delete=False) as f:
                metadata_tmp = Path(f.name)
                json.dump(payload, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(metadata_tmp, manifest)
            metadata_tmp = None
        except Exception:
            if metadata_tmp is not None:
                metadata_tmp.unlink(missing_ok=True)
            manifest.unlink(missing_ok=True)
            archive.unlink(missing_ok=True)
            raise
        self.prune(token)
        return RecoveryEntry(token, doc.name, payload['project_path'],
                             timestamp, archive, manifest)

    def entries(self) -> list[RecoveryEntry]:
        result = []
        if not self.root.is_dir():
            return result
        for manifest in self.root.glob('*.json'):
            try:
                info = json.loads(manifest.read_text(encoding='utf-8'))
                if info.get('schema') != 1 or len(info['token']) != 24:
                    continue
                filename = info['archive']
                if Path(filename).name != filename or not filename.endswith('.mellowzip'):
                    continue
                archive = self.root / filename
                if not archive.is_file():
                    continue
                result.append(RecoveryEntry(info['token'], info['project_name'],
                    info.get('project_path'), float(info['created_at']), archive, manifest))
            except (ValueError, TypeError, KeyError, OSError):
                continue
        return sorted(result, key=lambda x: x.created_at, reverse=True)

    @staticmethod
    def discard(entry: RecoveryEntry) -> None:
        entry.manifest.unlink(missing_ok=True)
        entry.archive.unlink(missing_ok=True)

    def discard_token(self, token: str) -> None:
        for entry in self.entries():
            if entry.token == token:
                self.discard(entry)

    def prune(self, token: str) -> None:
        matching = [e for e in self.entries() if e.token == token]
        for old in matching[self.keep_per_document:]:
            self.discard(old)
