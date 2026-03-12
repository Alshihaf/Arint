# tools/file_explorer.py
import os
import shutil
import time
import hashlib
import mimetypes
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Union, List, Optional, Callable

class FileExplorer:
    """
    Modul eksplorasi dan manipulasi file system tanpa batasan keamanan.
    Dilengkapi dengan berbagai fitur lanjutan dan pencatatan log.
    """

    def __init__(self, log_file: Optional[str] = "logs/file_access.log"):
        """
        Inisialisasi file explorer.
        :param log_file: Path ke file log (None = nonaktifkan logging)
        """
        self.log_file = Path(log_file) if log_file else None
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, level: str, message: str):
        """Mencatat aktivitas ke file log."""
        if not self.log_file:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {level}: {message}\n")
        except Exception:
            pass  # abaikan error logging

    # ================== OPERASI DASAR ==================

    def list_dir(self, path: Union[str, Path] = ".") -> Optional[List[str]]:
        """Mendaftar isi direktori."""
        target = Path(path).expanduser().resolve()
        if not target.exists():
            self._log("ERROR", f"list_dir: path tidak ditemukan {target}")
            return None
        if not target.is_dir():
            self._log("ERROR", f"list_dir: bukan direktori {target}")
            return None
        try:
            items = [str(p) for p in target.iterdir()]
            self._log("INFO", f"list_dir: {target} -> {len(items)} items")
            return items
        except Exception as e:
            self._log("ERROR", f"list_dir: {e}")
            return None

    def read_file(self, path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
        """Membaca konten file teks."""
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            self._log("ERROR", f"read_file: bukan file {target}")
            return None
        try:
            with open(target, 'r', encoding=encoding, errors='ignore') as f:
                content = f.read()
            self._log("INFO", f"read_file: {target} ({len(content)} chars)")
            return content
        except Exception as e:
            self._log("ERROR", f"read_file: {e}")
            return None

    def read_binary(self, path: Union[str, Path]) -> Optional[bytes]:
        """Membaca file sebagai binary."""
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            self._log("ERROR", f"read_binary: bukan file {target}")
            return None
        try:
            with open(target, 'rb') as f:
                content = f.read()
            self._log("INFO", f"read_binary: {target} ({len(content)} bytes)")
            return content
        except Exception as e:
            self._log("ERROR", f"read_binary: {e}")
            return None

    def write_file(self, path: Union[str, Path], content: Union[str, bytes], encoding: str = 'utf-8') -> bool:
        """Menulis konten ke file (teks atau binary). Buat direktori jika perlu."""
        target = Path(path).expanduser().resolve()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            mode = 'wb' if isinstance(content, bytes) else 'w'
            if mode == 'w':
                with open(target, mode, encoding=encoding) as f:
                    f.write(content)
            else:
                with open(target, mode) as f:
                    f.write(content)
            size = len(content)
            self._log("INFO", f"write_file: {target} ({size} bytes)")
            return True
        except Exception as e:
            self._log("ERROR", f"write_file: {e}")
            return False

    def append_text(self, path: Union[str, Path], text: str, encoding: str = 'utf-8') -> bool:
        """Menambahkan teks ke akhir file."""
        target = Path(path).expanduser().resolve()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'a', encoding=encoding) as f:
                f.write(text)
            self._log("INFO", f"append_text: {target} ({len(text)} chars)")
            return True
        except Exception as e:
            self._log("ERROR", f"append_text: {e}")
            return False

    def append_binary(self, path: Union[str, Path], data: bytes) -> bool:
        """Menambahkan data binary ke akhir file."""
        target = Path(path).expanduser().resolve()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'ab') as f:
                f.write(data)
            self._log("INFO", f"append_binary: {target} ({len(data)} bytes)")
            return True
        except Exception as e:
            self._log("ERROR", f"append_binary: {e}")
            return False

    def delete(self, path: Union[str, Path]) -> bool:
        """Menghapus file atau direktori (rekursif jika direktori)."""
        target = Path(path).expanduser().resolve()
        if not target.exists():
            self._log("WARNING", f"delete: path tidak ditemukan {target}")
            return False
        try:
            if target.is_file() or target.is_symlink():
                target.unlink()
                self._log("INFO", f"delete file: {target}")
            elif target.is_dir():
                shutil.rmtree(target)
                self._log("INFO", f"delete directory recursively: {target}")
            return True
        except Exception as e:
            self._log("ERROR", f"delete: {e}")
            return False

    def make_dir(self, path: Union[str, Path], exist_ok: bool = True) -> bool:
        """Membuat direktori baru (termasuk parent)."""
        target = Path(path).expanduser().resolve()
        try:
            target.mkdir(parents=True, exist_ok=exist_ok)
            self._log("INFO", f"make_dir: {target}")
            return True
        except Exception as e:
            self._log("ERROR", f"make_dir: {e}")
            return False

    def rename(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """Mengganti nama atau memindahkan file/direktori."""
        src_path = Path(src).expanduser().resolve()
        dst_path = Path(dst).expanduser().resolve()
        if not src_path.exists():
            self._log("ERROR", f"rename: sumber tidak ditemukan {src_path}")
            return False
        try:
            # Buat direktori tujuan jika perlu
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            src_path.rename(dst_path)
            self._log("INFO", f"rename: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            self._log("ERROR", f"rename: {e}")
            return False

    def copy(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """Menyalin file atau direktori (rekursif)."""
        src_path = Path(src).expanduser().resolve()
        dst_path = Path(dst).expanduser().resolve()
        if not src_path.exists():
            self._log("ERROR", f"copy: sumber tidak ditemukan {src_path}")
            return False
        try:
            if src_path.is_file():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                self._log("INFO", f"copy file: {src_path} -> {dst_path}")
            elif src_path.is_dir():
                shutil.copytree(src_path, dst_path)
                self._log("INFO", f"copy directory: {src_path} -> {dst_path}")
            return True
        except Exception as e:
            self._log("ERROR", f"copy: {e}")
            return False

    def move(self, src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """Memindahkan file atau direktori."""
        return self.rename(src, dst)

    def get_info(self, path: Union[str, Path]) -> Optional[dict]:
        """Mengembalikan informasi file/direktori."""
        target = Path(path).expanduser().resolve()
        if not target.exists():
            return None
        stat = target.stat()
        info = {
            "path": str(target),
            "exists": True,
            "is_file": target.is_file(),
            "is_dir": target.is_dir(),
            "is_symlink": target.is_symlink(),
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "mode": stat.st_mode,
            "owner": stat.st_uid,
            "group": stat.st_gid,
        }
        self._log("INFO", f"get_info: {target}")
        return info

    # ================== PENCARIAN ==================

    def search_files(self, pattern: str, start_path: Union[str, Path] = ".", recursive: bool = True) -> Optional[List[str]]:
        """Mencari file dengan pola wildcard (misal '*.txt')."""
        start = Path(start_path).expanduser().resolve()
        if not start.is_dir():
            self._log("ERROR", f"search: start_path bukan direktori {start}")
            return None
        try:
            if recursive:
                matches = [str(p) for p in start.rglob(pattern)]
            else:
                matches = [str(p) for p in start.glob(pattern)]
            self._log("INFO", f"search: {pattern} di {start} -> {len(matches)} hasil")
            return matches
        except Exception as e:
            self._log("ERROR", f"search: {e}")
            return None

    def find_by_name(self, name: str, start_path: Union[str, Path] = ".", exact: bool = False) -> List[str]:
        """Mencari file berdasarkan nama (case-sensitive). Jika exact=False, gunakan substring."""
        start = Path(start_path).expanduser().resolve()
        if not start.is_dir():
            return []
        results = []
        try:
            for p in start.rglob('*'):
                if exact:
                    if p.name == name:
                        results.append(str(p))
                else:
                    if name in p.name:
                        results.append(str(p))
            self._log("INFO", f"find_by_name: {name} di {start} -> {len(results)} hasil")
            return results
        except Exception as e:
            self._log("ERROR", f"find_by_name: {e}")
            return []

    # ================== FITUR LANJUTAN ==================

    def get_hash(self, path: Union[str, Path], algorithm: str = 'sha256') -> Optional[str]:
        """Menghitung hash file (md5, sha1, sha256, dll)."""
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            self._log("ERROR", f"get_hash: bukan file {target}")
            return None
        try:
            hash_obj = hashlib.new(algorithm)
            with open(target, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_obj.update(chunk)
            hex_digest = hash_obj.hexdigest()
            self._log("INFO", f"get_hash: {target} [{algorithm}] = {hex_digest}")
            return hex_digest
        except Exception as e:
            self._log("ERROR", f"get_hash: {e}")
            return None

    def get_mime_type(self, path: Union[str, Path]) -> Optional[str]:
        """Mendapatkan MIME type file."""
        target = Path(path).expanduser().resolve()
        if not target.exists():
            return None
        mime_type, _ = mimetypes.guess_type(str(target))
        if mime_type is None:
            return "application/octet-stream"
        self._log("INFO", f"get_mime_type: {target} -> {mime_type}")
        return mime_type

    def get_disk_usage(self, path: Union[str, Path] = ".") -> Optional[dict]:
        """Mendapatkan informasi penggunaan disk."""
        target = Path(path).expanduser().resolve()
        if not target.exists():
            return None
        try:
            stat = shutil.disk_usage(target)
            info = {
                "total": stat.total,
                "used": stat.used,
                "free": stat.free,
                "percent_used": (stat.used / stat.total) * 100
            }
            self._log("INFO", f"get_disk_usage: {target}")
            return info
        except Exception as e:
            self._log("ERROR", f"get_disk_usage: {e}")
            return None

    def compress(self, source: Union[str, Path], destination: Union[str, Path], format: str = 'zip') -> bool:
        """Mengompres file/direktori ke format zip (saat ini hanya zip)."""
        src = Path(source).expanduser().resolve()
        dst = Path(destination).expanduser().resolve()
        if not src.exists():
            self._log("ERROR", f"compress: sumber tidak ditemukan {src}")
            return False
        try:
            if format.lower() == 'zip':
                with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as zf:
                    if src.is_file():
                        zf.write(src, arcname=src.name)
                    else:
                        for root, dirs, files in os.walk(src):
                            for file in files:
                                full_path = os.path.join(root, file)
                                rel_path = os.path.relpath(full_path, src)
                                zf.write(full_path, arcname=rel_path)
            else:
                self._log("ERROR", f"compress: format {format} tidak didukung")
                return False
            self._log("INFO", f"compress: {src} -> {dst} ({format})")
            return True
        except Exception as e:
            self._log("ERROR", f"compress: {e}")
            return False

    def decompress(self, archive: Union[str, Path], destination: Union[str, Path]) -> bool:
        """Mengekstrak arsip zip ke direktori tujuan."""
        arc = Path(archive).expanduser().resolve()
        dst = Path(destination).expanduser().resolve()
        if not arc.is_file():
            self._log("ERROR", f"decompress: arsip tidak ditemukan {arc}")
            return False
        try:
            with zipfile.ZipFile(arc, 'r') as zf:
                zf.extractall(dst)
            self._log("INFO", f"decompress: {arc} -> {dst}")
            return True
        except Exception as e:
            self._log("ERROR", f"decompress: {e}")
            return False

    def split_file(self, path: Union[str, Path], chunk_size: int, output_dir: Optional[Union[str, Path]] = None) -> bool:
        """Memecah file menjadi bagian-bagian dengan ukuran chunk_size bytes."""
        src = Path(path).expanduser().resolve()
        if not src.is_file():
            self._log("ERROR", f"split_file: bukan file {src}")
            return False
        if output_dir is None:
            output_dir = src.parent / f"{src.name}_parts"
        else:
            output_dir = Path(output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            part_num = 0
            with open(src, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    part_path = output_dir / f"{src.name}.part{part_num:03d}"
                    with open(part_path, 'wb') as part_f:
                        part_f.write(chunk)
                    part_num += 1
            self._log("INFO", f"split_file: {src} -> {output_dir} ({part_num} parts)")
            return True
        except Exception as e:
            self._log("ERROR", f"split_file: {e}")
            return False

    def join_files(self, part_pattern: str, output_path: Union[str, Path]) -> bool:
        """Menggabungkan bagian-bagian file (misal dari split_file)."""
        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            part_files = sorted(Path().glob(part_pattern))
            with open(output, 'wb') as out_f:
                for part in part_files:
                    with open(part, 'rb') as in_f:
                        shutil.copyfileobj(in_f, out_f)
            self._log("INFO", f"join_files: {len(part_files)} parts -> {output}")
            return True
        except Exception as e:
            self._log("ERROR", f"join_files: {e}")
            return False

    def watch_directory(self, path: Union[str, Path], callback: Callable, interval: float = 1.0):
        """
        Sederhana polling direktori untuk memantau perubahan.
        callback akan dipanggil dengan (event_type, path) setiap ada perubahan.
        Hanya untuk demonstrasi; implementasi nyata gunakan watchdog.
        """
        target = Path(path).expanduser().resolve()
        if not target.is_dir():
            raise ValueError(f"Bukan direktori: {target}")
        snapshot = {}
        def get_state():
            state = {}
            for p in target.rglob('*'):
                if p.is_file():
                    state[str(p)] = p.stat().st_mtime
            return state
        try:
            while True:
                time.sleep(interval)
                new_state = get_state()
                for p, mtime in new_state.items():
                    if p not in snapshot:
                        callback('created', p)
                    elif snapshot[p] != mtime:
                        callback('modified', p)
                for p in list(snapshot.keys()):
                    if p not in new_state:
                        callback('deleted', p)
                snapshot = new_state
        except KeyboardInterrupt:
            pass
        self._log("INFO", f"watch_directory selesai: {target}")

    # ================== EDIT FILE ==================

    def read_lines(self, path: Union[str, Path], encoding: str = 'utf-8') -> Optional[List[str]]:
        """Membaca file teks dan mengembalikan daftar baris (termasuk newline)."""
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            self._log("ERROR", f"read_lines: bukan file {target}")
            return None
        try:
            with open(target, 'r', encoding=encoding) as f:
                lines = f.readlines()
            self._log("INFO", f"read_lines: {target} ({len(lines)} lines)")
            return lines
        except Exception as e:
            self._log("ERROR", f"read_lines: {e}")
            return None

    def write_lines(self, path: Union[str, Path], lines: List[str], encoding: str = 'utf-8') -> bool:
        """Menulis daftar baris ke file (setiap baris akan ditulis apa adanya)."""
        target = Path(path).expanduser().resolve()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'w', encoding=encoding) as f:
                f.writelines(lines)
            self._log("INFO", f"write_lines: {target} ({len(lines)} lines)")
            return True
        except Exception as e:
            self._log("ERROR", f"write_lines: {e}")
            return False

    def append_line(self, path: Union[str, Path], line: str, encoding: str = 'utf-8') -> bool:
        """Menambahkan satu baris ke akhir file (menambahkan newline jika perlu)."""
        if not line.endswith('\n'):
            line += '\n'
        return self.append_text(path, line, encoding)

    def prepend_to_file(self, path: Union[str, Path], text: str, encoding: str = 'utf-8') -> bool:
        """Menambahkan teks di awal file (menggeser konten lama)."""
        target = Path(path).expanduser().resolve()
        try:
            if target.exists():
                with open(target, 'r', encoding=encoding) as f:
                    old_content = f.read()
            else:
                old_content = ''
            with open(target, 'w', encoding=encoding) as f:
                f.write(text + old_content)
            self._log("INFO", f"prepend_to_file: {target} ({len(text)} chars ditambahkan di awal)")
            return True
        except Exception as e:
            self._log("ERROR", f"prepend_to_file: {e}")
            return False

    def replace_in_file(self, path: Union[str, Path], old: str, new: str, count: int = -1, encoding: str = 'utf-8') -> int:
        """
        Mengganti substring dalam file.
        :param count: Jumlah maksimum penggantian (-1 = semua)
        :return: Jumlah penggantian yang dilakukan
        """
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            self._log("ERROR", f"replace_in_file: bukan file {target}")
            return 0
        try:
            with open(target, 'r', encoding=encoding) as f:
                content = f.read()
            new_content, replacements = self._replace_count(content, old, new, count)
            if replacements > 0:
                with open(target, 'w', encoding=encoding) as f:
                    f.write(new_content)
            self._log("INFO", f"replace_in_file: {target} ({replacements} penggantian)")
            return replacements
        except Exception as e:
            self._log("ERROR", f"replace_in_file: {e}")
            return 0

    def _replace_count(self, text: str, old: str, new: str, count: int) -> tuple:
        """Membantu replace dengan menghitung jumlah penggantian."""
        if count == 0:
            return text, 0
        if count < 0:
            return text.replace(old, new), text.count(old)
        parts = text.split(old, count)
        new_text = new.join(parts)
        replacements = len(parts) - 1
        return new_text, replacements

    def insert_into_file(self, path: Union[str, Path], position: int, text: str, encoding: str = 'utf-8') -> bool:
        """
        Menyisipkan teks pada posisi tertentu (dalam bytes untuk binary, atau karakter untuk teks).
        Untuk file teks, posisi adalah indeks karakter.
        """
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            self._log("ERROR", f"insert_into_file: bukan file {target}")
            return False
        try:
            with open(target, 'rb') as f:
                content = f.read()
            if position < 0 or position > len(content):
                self._log("ERROR", f"insert_into_file: posisi {position} di luar rentang (0-{len(content)})")
                return False
            data = text.encode(encoding)
            new_content = content[:position] + data + content[position:]
            with open(target, 'wb') as f:
                f.write(new_content)
            self._log("INFO", f"insert_into_file: {target} pada posisi {position} ({len(data)} bytes)")
            return True
        except Exception as e:
            self._log("ERROR", f"insert_into_file: {e}")
            return False

    def insert_line_at(self, path: Union[str, Path], line_number: int, line: str, encoding: str = 'utf-8') -> bool:
        """Menyisipkan baris pada nomor baris tertentu (baris dimulai dari 1)."""
        lines = self.read_lines(path, encoding)
        if lines is None:
            return False
        if line_number < 1 or line_number > len(lines) + 1:
            self._log("ERROR", f"insert_line_at: line_number {line_number} di luar rentang (1-{len(lines)+1})")
            return False
        if not line.endswith('\n'):
            line += '\n'
        lines.insert(line_number - 1, line)
        return self.write_lines(path, lines, encoding)

    def delete_line_at(self, path: Union[str, Path], line_number: int, encoding: str = 'utf-8') -> bool:
        """Menghapus baris pada nomor baris tertentu."""
        lines = self.read_lines(path, encoding)
        if lines is None:
            return False
        if line_number < 1 or line_number > len(lines):
            self._log("ERROR", f"delete_line_at: line_number {line_number} di luar rentang (1-{len(lines)})")
            return False
        del lines[line_number - 1]
        return self.write_lines(path, lines, encoding)

    def truncate_file(self, path: Union[str, Path], size: int) -> bool:
        """Memotong file hingga ukuran tertentu (dalam bytes)."""
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            self._log("ERROR", f"truncate_file: bukan file {target}")
            return False
        try:
            with open(target, 'r+b') as f:
                f.truncate(size)
            self._log("INFO", f"truncate_file: {target} -> {size} bytes")
            return True
        except Exception as e:
            self._log("ERROR", f"truncate_file: {e}")
            return False

    def touch(self, path: Union[str, Path]) -> bool:
        """Membuat file kosong atau memperbarui timestamp akses/modifikasi."""
        target = Path(path).expanduser().resolve()
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
            self._log("INFO", f"touch: {target}")
            return True
        except Exception as e:
            self._log("ERROR", f"touch: {e}")
            return False

    def chmod(self, path: Union[str, Path], mode: int) -> bool:
        """Mengubah permission file (mode dalam octal, misal 0o755)."""
        target = Path(path).expanduser().resolve()
        if not target.exists():
            self._log("ERROR", f"chmod: path tidak ditemukan {target}")
            return False
        try:
            target.chmod(mode)
            self._log("INFO", f"chmod: {target} -> {oct(mode)}")
            return True
        except Exception as e:
            self._log("ERROR", f"chmod: {e}")
            return False

    # ================== UTILITAS ==================

    def which(self, program: str) -> Optional[str]:
        """Mencari executable di PATH (seperti perintah which)."""
        path = shutil.which(program)
        if path:
            self._log("INFO", f"which: {program} -> {path}")
            return path
        self._log("WARNING", f"which: {program} tidak ditemukan")
        return None

    def get_env_var(self, name: str) -> Optional[str]:
        """Mendapatkan nilai environment variable."""
        value = os.environ.get(name)
        self._log("INFO", f"get_env_var: {name} = {value}")
        return value

    def set_env_var(self, name: str, value: str) -> None:
        """Mengatur environment variable (hanya untuk proses saat ini)."""
        os.environ[name] = value
        self._log("INFO", f"set_env_var: {name} = {value}")

    def execute_command(self, command: str, cwd: Optional[Union[str, Path]] = None) -> dict:
        """
        Menjalankan perintah sistem dan mengembalikan output.
        (Membutuhkan modul subprocess)
        """
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
            self._log("INFO", f"execute_command: {command} -> returncode {result.returncode}")
            return output
        except Exception as e:
            self._log("ERROR", f"execute_command: {e}")
            return {"stdout": "", "stderr": str(e), "returncode": -1, "success": False}