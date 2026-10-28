from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile
from contextlib import ExitStack, contextmanager
import struct
import subprocess
import unittest
from unittest.mock import MagicMock, patch
import io
import os

from embercade.imports import ImportError as ManagedImportError, _copy_new, inspect_provider, _provider_metadata

from embercade.imports import import_cores, import_providers


XENIA_METADATA = {"Name": "Xenia Edge", "Exec": "xenia_edge %f", "StartupWMClass": "xenia_edge"}


def metadata(stream, _size):
    stream.seek(0)
    return {"Name": "Other"} if stream.read().endswith(b"unknown") else XENIA_METADATA


def elf(machine=62, *, appimage=False, symbols=True):
    header = bytearray(120)
    header[:7] = b"\x7fELF\x02\x01\x01"
    if appimage:
        header[8:11] = b"AI\x02"
    struct.pack_into("<HHI", header, 16, 3, machine, 1)
    struct.pack_into("<Q", header, 32, 64)
    struct.pack_into("<HH", header, 54, 56, 1)
    struct.pack_into("<IIQQQQQQ", header, 64, 1, 5, 0, 0, 0, 120, 120, 4096)
    if symbols:
        header.extend(b"retro_init\0retro_get_system_info\0retro_set_environment\0")
    return bytes(header)


def sectioned_appimage():
    """Bounded ELF fixture with sections and an appended SquashFS signature."""
    image = bytearray(elf(appimage=True, symbols=False))
    image.extend(bytes(328 - len(image)))
    struct.pack_into("<Q", image, 40, 128)
    struct.pack_into("<HH", image, 58, 64, 2)
    struct.pack_into("<I", image, 132, 1)  # file-backed section
    struct.pack_into("<QQ", image, 152, 320, 8)
    struct.pack_into("<I", image, 196, 8)  # SHT_NOBITS can extend past EOF
    struct.pack_into("<QQ", image, 216, 4096, 512)
    image[320:328] = b"section!"
    return bytes(image) + b"hsqs" + bytes(92)


class ProviderMetadataTests(unittest.TestCase):
    @contextmanager
    def metadata_reader(self, *, image=None, helpers=None, chunks=None, clock=None,
                        returncode=0, wait_error=None):
        """Exercise parsing/limits while substituting only the helper pipe."""
        image = sectioned_appimage() if image is None else image
        helpers = {"unsquashfs": "/usr/bin/unsquashfs"} if helpers is None else helpers
        desktop = (
            b"[Other]\nName=Ignored\n[Desktop Entry]\n"
            b"Name=Xenia Edge\nExec=xenia_edge %f\nStartupWMClass=xenia_edge\n"
            b"[Desktop Action]\nName=Also ignored\n"
        )
        chunks = [desktop, b""] if chunks is None else chunks
        process = MagicMock()
        process.__enter__.return_value = process
        process.stdout.fileno.return_value = 123
        process.wait.return_value = returncode
        if wait_error is not None:
            process.wait.side_effect = [wait_error, 0]
        selector = MagicMock()
        selector.__enter__.return_value = selector
        selector.get_map.return_value = {123: object()}
        selector.select.return_value = [(123, 1)]
        selector.unregister.side_effect = lambda _pipe: setattr(selector.get_map, "return_value", {})
        with TemporaryFile() as stream, ExitStack() as stack:
            stream.write(image)
            stream.flush()
            before_mtime = os.fstat(stream.fileno()).st_mtime_ns
            popen = stack.enter_context(patch("embercade.imports.subprocess.Popen", return_value=process))
            stack.enter_context(patch("embercade.imports.shutil.which", side_effect=helpers.get))
            stack.enter_context(patch("embercade.imports.selectors.DefaultSelector", return_value=selector))
            read = stack.enter_context(patch("embercade.imports.os.read", side_effect=chunks))
            if clock is not None:
                stack.enter_context(patch("embercade.imports.time.monotonic", side_effect=clock))
            try:
                yield stream, len(image), process, popen, read
            finally:
                stream.seek(0)
                self.assertEqual(stream.read(), image)
                self.assertEqual(os.fstat(stream.fileno()).st_mtime_ns, before_mtime)

    def test_unsquashfs_uses_section_end_and_parses_only_desktop_entry(self):
        with self.metadata_reader() as (stream, size, process, popen, _read):
            self.assertEqual(_provider_metadata(stream, size), XENIA_METADATA)
            self.assertEqual(popen.call_args.args[0], [
                "/usr/bin/unsquashfs", "-o", "328", "-cat",
                f"/proc/self/fd/{stream.fileno()}",
                "usr/share/applications/xenia_edge.desktop",
            ])
            self.assertEqual(popen.call_args.kwargs["pass_fds"], (stream.fileno(),))
            process.kill.assert_not_called()

    def test_7z_fallback_reads_only_known_metadata_to_stdout(self):
        with self.metadata_reader(helpers={"7z": "/usr/bin/7z"}) as (stream, size, process, popen, _read):
            self.assertEqual(_provider_metadata(stream, size), XENIA_METADATA)
            self.assertEqual(popen.call_args.args[0], [
                "/usr/bin/7z", "e", "-so", "-tSquashFS", "-spd",
                f"/proc/self/fd/{stream.fileno()}",
                "usr/share/applications/xenia_edge.desktop",
            ])
            self.assertEqual(popen.call_args.kwargs["pass_fds"], (stream.fileno(),))
            process.kill.assert_not_called()

    def test_no_archive_helper_is_a_clear_error_before_process_creation(self):
        with self.metadata_reader(helpers={}) as (stream, size, _process, popen, _read):
            with self.assertRaisesRegex(ManagedImportError, "unsquashfs or 7z is unavailable"):
                _provider_metadata(stream, size)
            popen.assert_not_called()

    def test_invalid_headers_and_missing_payload_never_start_a_helper(self):
        sections_outside_file = bytearray(sectioned_appimage())
        struct.pack_into("<Q", sections_outside_file, 40, len(sections_outside_file) + 1)
        section_outside_file = bytearray(sectioned_appimage())
        struct.pack_into("<QQ", section_outside_file, 152, len(section_outside_file) - 1, 8)
        missing_squashfs = bytearray(sectioned_appimage())
        missing_squashfs[328:332] = b"none"
        type_one = bytearray(sectioned_appimage())
        type_one[10] = 1
        cases = (
            (sectioned_appimage()[:63], "type-2 AppImage"),
            (type_one, "type-2 AppImage"),
            (sections_outside_file, "damaged AppImage section headers"),
            (section_outside_file, "damaged AppImage section"),
            (missing_squashfs, "missing AppImage SquashFS payload"),
        )
        for image, message in cases:
            with self.subTest(message=message), self.metadata_reader(image=image) as (stream, size, _process, popen, _read):
                with self.assertRaisesRegex(ManagedImportError, message):
                    _provider_metadata(stream, size)
                popen.assert_not_called()

    def test_truncated_section_read_is_rejected_even_if_size_was_larger(self):
        image = bytearray(sectioned_appimage())
        struct.pack_into("<Q", image, 40, len(image) + 64)
        with self.metadata_reader(image=image) as (stream, size, _process, popen, _read):
            with self.assertRaisesRegex(ManagedImportError, "truncated AppImage section header"):
                _provider_metadata(stream, size + 256)
            popen.assert_not_called()

    def test_output_limit_stops_only_the_metadata_helper(self):
        with self.metadata_reader(chunks=[b"x" * 8193]) as (stream, size, process, _popen, read):
            with self.assertRaisesRegex(ManagedImportError, "metadata is too large"):
                _provider_metadata(stream, size)
            self.assertEqual(read.call_args.args, (123, 8193))
            process.kill.assert_called_once_with()
            process.wait.assert_called_once_with()

    def test_stream_timeout_stops_only_the_metadata_helper(self):
        with self.metadata_reader(clock=[0, 10]) as (stream, size, process, _popen, read):
            with self.assertRaisesRegex(ManagedImportError, "inspection timed out"):
                _provider_metadata(stream, size)
            read.assert_not_called()
            process.kill.assert_called_once_with()
            process.wait.assert_called_once_with()

    def test_helper_wait_timeout_is_cleaned_up(self):
        timeout = subprocess.TimeoutExpired("metadata reader", 5)
        with self.metadata_reader(wait_error=timeout) as (stream, size, process, _popen, _read):
            with self.assertRaisesRegex(ManagedImportError, "inspection timed out"):
                _provider_metadata(stream, size)
            process.kill.assert_called_once_with()
            self.assertEqual(process.wait.call_count, 2)

    def test_failed_helper_cannot_report_successful_recognition(self):
        with self.metadata_reader(returncode=1) as (stream, size, process, _popen, _read):
            with self.assertRaisesRegex(ManagedImportError, "desktop entry not found"):
                _provider_metadata(stream, size)
            process.kill.assert_called_once_with()


class ImportTests(unittest.TestCase):
    def test_core_import_skips_broken_and_wrong_arch_and_preserves_source(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            valid = source / "nestopia_libretro.so"
            valid.write_bytes(elf())
            (source / "arm_libretro.so").write_bytes(elf(machine=183))
            (source / "broken_libretro.so").write_bytes(b"\x7fELFbroken")
            (source / "notcore_libretro.so").write_bytes(elf(symbols=False))
            source_before = {p.name: p.read_bytes() for p in source.iterdir()}
            data = root / "data"
            result = import_cores(source, data)
            self.assertEqual((result.found, result.valid, result.imported), (4, 1, 1))
            self.assertEqual(len(result.skipped), 3)
            self.assertEqual((data / "cores" / valid.name).read_bytes(), valid.read_bytes())
            self.assertEqual({p.name: p.read_bytes() for p in source.iterdir()}, source_before)

    def test_duplicate_and_conflict_do_not_overwrite(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "nestopia_libretro.so").write_bytes(elf())
            data = root / "data"
            import_cores(source, data)
            duplicate = import_cores(source, data)
            self.assertEqual((duplicate.imported, duplicate.present), (0, 1))
            original = (data / "cores/nestopia_libretro.so").read_bytes()
            (source / "nestopia_libretro.so").write_bytes(elf() + b"new")
            conflict = import_cores(source, data)
            self.assertEqual(conflict.conflicts, ("nestopia_libretro.so",))
            self.assertEqual((data / "cores/nestopia_libretro.so").read_bytes(), original)

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_known_provider_import_unknown_skip_and_executable(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            xenia = source / "xenia_edge_linux.AppImage"
            xenia.write_bytes(elf(appimage=True, symbols=False))
            unknown = source / "other.AppImage"
            unknown.write_bytes(elf(appimage=True, symbols=False) + b"unknown")
            before = xenia.read_bytes()
            result = import_providers(source, root / "data")
            self.assertEqual((result.found, result.valid, result.imported), (2, 1, 1))
            self.assertEqual(len(result.skipped), 1)
            imported = root / "data/providers/xenia/xenia_edge_linux.AppImage"
            self.assertEqual(imported.read_bytes(), before)
            self.assertTrue(imported.stat().st_mode & 0o100)
            self.assertEqual(xenia.read_bytes(), before)

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_identical_renamed_reimport_reuses_path_and_never_copies(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source, other = root / "source", root / "new source"
            source.mkdir()
            other.mkdir()
            supplied = source / "any-name.AppImage"
            supplied.write_bytes(elf(appimage=True))
            supplied.chmod(0o600)
            before = (supplied.read_bytes(), supplied.stat().st_mode, supplied.stat().st_mtime_ns)
            first = import_providers(source, root / "data")
            managed, = first.imported_paths
            managed_before = managed.stat()
            (other / "renamed.appimage").write_bytes(supplied.read_bytes())
            with patch("embercade.imports._copy_new", side_effect=AssertionError("no copy expected")):
                for folder in (source, other, managed.parent):
                    result = import_providers(folder, root / "data")
                    self.assertEqual((result.present, result.imported_paths), (1, (managed,)))
            self.assertEqual(managed.stat().st_mtime_ns, managed_before.st_mtime_ns)
            self.assertEqual(managed.stat().st_ino, managed_before.st_ino)
            self.assertEqual((supplied.read_bytes(), supplied.stat().st_mode, supplied.stat().st_mtime_ns), before)
            self.assertEqual(tuple(managed.parent.iterdir()), (managed,))

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_different_build_conflict_preserves_working_copy(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            file = source / "build.AppImage"
            file.write_bytes(elf(appimage=True))
            managed, = import_providers(source, root / "data").imported_paths
            before = (managed.read_bytes(), managed.stat())
            file.write_bytes(elf(appimage=True) + b"different")
            result = import_providers(source, root / "data")
            self.assertEqual((result.imported, result.present), (0, 0))
            self.assertEqual(result.conflicts, (managed.name,))
            self.assertEqual(managed.read_bytes(), before[0])
            self.assertEqual(managed.stat().st_mtime_ns, before[1].st_mtime_ns)
            self.assertEqual(tuple(managed.parent.iterdir()), (managed,))

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_distinct_candidates_refused_before_any_copy(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            for index in range(2):
                (source / f"build{index}.AppImage").write_bytes(elf(appimage=True) + bytes([index]))
            result = import_providers(source, root / "data")
            self.assertEqual(len(result.ambiguous), 2)
            self.assertEqual(result.imported, 0)
            self.assertFalse((root / "data").exists())

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_equivalent_candidates_collapse_to_one_copy(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            for name in ("old.AppImage", "copy.APPIMAGE"):
                (source / name).write_bytes(elf(appimage=True))
            result = import_providers(source, root / "data")
            self.assertEqual((result.found, result.valid, result.imported), (2, 1, 1))
            self.assertFalse(result.ambiguous)

    def test_empty_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(import_providers(root, root / "data").found, 0)
            self.assertFalse((root / "data").exists())

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_executable_appimage_header_is_inspected_not_mislabelled_as_corrupt(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            image = bytearray(elf(appimage=True) + b"unknown")
            struct.pack_into("<H", image, 16, 2)  # ET_EXEC is valid for AppImage runtimes
            (root / "Other.AppImage").write_bytes(image)
            result = import_providers(root, root / "data")
            self.assertEqual(result.valid, 0)
            self.assertIn("unsupported provider", result.skipped[0])

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_unknown_deceptive_name_and_invalid_files_are_not_imported(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "xenia-edge-deceptive.AppImage").write_bytes(elf(appimage=True) + b"unknown")
            (source / "broken.AppImage").write_bytes(b"\x7fELF")
            unreadable = source / "unreadable.AppImage"
            unreadable.write_bytes(elf(appimage=True))
            unreadable.chmod(0)
            (source / "native.AppImage").write_bytes(elf())
            result = import_providers(source, root / "data")
            self.assertEqual((result.found, result.valid, len(result.skipped)), (4, 0, 4))
            self.assertFalse((root / "data").exists())

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_missing_managed_reimport_and_damaged_managed_refusal(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "source.AppImage").write_bytes(elf(appimage=True))
            managed, = import_providers(source, root / "data").imported_paths
            managed.unlink()
            self.assertEqual(import_providers(source, root / "data").imported, 1)
            managed.write_bytes(b"damaged")
            result = import_providers(source, root / "data")
            self.assertTrue(result.conflicts)
            self.assertEqual(managed.read_bytes(), b"damaged")

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_managed_permission_repair_does_not_touch_source(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            supplied = source / "source.AppImage"
            supplied.write_bytes(elf(appimage=True))
            supplied.chmod(0o600)
            managed, = import_providers(source, root / "data").imported_paths
            managed.chmod(0o600)
            self.assertEqual(import_providers(source, root / "data").present, 1)
            self.assertTrue(managed.stat().st_mode & 0o100)
            self.assertFalse(supplied.stat().st_mode & 0o100)

    def test_changed_source_copy_has_no_partial_target_or_temp(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "managed.AppImage"
            with self.assertRaisesRegex(ManagedImportError, "Source changed"):
                _copy_new(io.BytesIO(b"changed"), "wrong-digest", target, executable=True)
            self.assertEqual(tuple(target.parent.iterdir()), ())

    @patch("embercade.imports._provider_metadata", side_effect=metadata)
    def test_symlinked_managed_root_refused(self, _metadata):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (root / "data").symlink_to(outside)
            with self.assertRaisesRegex(ManagedImportError, "symlink"):
                import_providers(source, root / "data")
            self.assertEqual(tuple(outside.iterdir()), ())

    def test_fifo_inspection_does_not_block_or_execute(self):
        with TemporaryDirectory() as directory:
            fifo = Path(directory) / "pipe.AppImage"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(ManagedImportError, "regular file"):
                inspect_provider(fifo)

    def test_source_symlink_is_not_imported(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            original = root / "outside_libretro.so"
            original.write_bytes(elf())
            (source / "outside_libretro.so").symlink_to(original)
            result = import_cores(source, root / "data")
            self.assertEqual(result.imported, 0)
            self.assertEqual(len(result.skipped), 1)


if __name__ == "__main__":
    unittest.main()
