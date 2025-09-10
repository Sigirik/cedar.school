import os
import posixpath
from dataclasses import dataclass
from typing import BinaryIO

from django.conf import settings

try:
    import paramiko  # optional; only needed if RECORDING_STORAGE=SFTP
except ImportError:
    paramiko = None


@dataclass
class SavedFile:
    public_url: str
    size: int


class AbstractRecordingStorage:
    def save_fileobj(self, fileobj: BinaryIO, dst_rel_path: str) -> SavedFile:
        raise NotImplementedError

    def save_local_path(self, src_path: str, dst_rel_path: str) -> SavedFile:
        with open(src_path, "rb") as f:
            return self.save_fileobj(f, dst_rel_path)


class LocalRecordingStorage(AbstractRecordingStorage):
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_fileobj(self, fileobj: BinaryIO, dst_rel_path: str) -> SavedFile:
        dst_abs = os.path.join(self.base_dir, dst_rel_path)
        os.makedirs(os.path.dirname(dst_abs), exist_ok=True)

        size = 0
        with open(dst_abs, "wb") as out:
            while True:
                chunk = fileobj.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                size += len(chunk)

        public_url = f"/media/recordings/{dst_rel_path}"
        return SavedFile(public_url=public_url, size=size)


class SFTPRecordingStorage(AbstractRecordingStorage):
    def __init__(self, host: str, port: int, username: str, password: str,
                 base_dir: str, public_base: str):
        if paramiko is None:
            raise RuntimeError("paramiko is not installed. pip install paramiko")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_dir = base_dir.rstrip("/")
        self.public_base = public_base.rstrip("/")

    def _connect(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.host, port=self.port,
                       username=self.username, password=self.password)
        sftp = client.open_sftp()
        return client, sftp

    def _ensure_dirs(self, sftp, remote_path: str):
        parts = remote_path.strip("/").split("/")
        path = ""
        for p in parts[:-1]:
            path = f"{path}/{p}" if path else f"/{p}"
            try:
                sftp.stat(path)
            except FileNotFoundError:
                sftp.mkdir(path)

    def save_fileobj(self, fileobj: BinaryIO, dst_rel_path: str) -> SavedFile:
        client, sftp = self._connect()
        try:
            remote_path = posixpath.join(self.base_dir, dst_rel_path).replace("\\", "/")
            self._ensure_dirs(sftp, remote_path)

            size = 0
            with sftp.file(remote_path, "wb") as out:
                while True:
                    chunk = fileobj.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    size += len(chunk)

            public_url = f"{self.public_base}/{dst_rel_path}".replace("//", "/").replace(":/", "://")
            return SavedFile(public_url=public_url, size=size)
        finally:
            sftp.close()
            client.close()


def get_storage() -> AbstractRecordingStorage:
    backend = settings.RECORDING_STORAGE
    if backend == "LOCAL":
        return LocalRecordingStorage(settings.RECORDING_LOCAL_DIR)
    if backend == "SFTP":
        return SFTPRecordingStorage(
            host=os.getenv("SFTP_HOST"),
            port=int(os.getenv("SFTP_PORT", "22")),
            username=os.getenv("SFTP_USERNAME"),
            password=os.getenv("SFTP_PASSWORD"),
            base_dir=os.getenv("SFTP_BASE_DIR"),
            public_base=os.getenv("SFTP_PUBLIC_BASE"),
        )
    raise RuntimeError(f"Unsupported RECORDING_STORAGE={backend}")
