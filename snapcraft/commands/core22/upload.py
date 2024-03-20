# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Snapcraft Store uploading related commands."""

import pathlib
import textwrap
from typing import TYPE_CHECKING, Any, List, Optional

from dataclasses import dataclass
from craft_cli import BaseCommand, emit
from craft_cli.errors import ArgumentParsingError
from overrides import overrides
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from snapcraft import store, utils
from snapcraft_legacy._store import get_data_from_snap_file

if TYPE_CHECKING:
    import argparse


@dataclass(frozen=True)
class ComponentOption:
    """Argparse helper to validate and convert a 'component' option.

    Receives a callable to convert the string from command line to the desired object.

    Example of use:

        parser.add_argument('--component',  type=ComponentOption())
    """

    name: str | None = None
    filename: int | None = None

    def __call__(self, value):
        """Run by argparse to validate and convert the given argument."""
        parts = [x.strip() for x in value.split("=")]
        parts = [p for p in parts if p]
        if len(parts) == 2:
            name, filename = parts
            return ComponentOption(name, filename)

        raise ValueError("the component format must be <name>=<filename>")


class StoreUploadCommand(BaseCommand):
    """Upload a snap to the Snap Store."""

    name = "upload"
    help_msg = "Upload a snap to the Snap Store"
    overview = textwrap.dedent(
        """
        By passing --release with a comma-separated list of channels the snap would
        be released to the selected channels if the store review passes for this
        <snap-file>.

        This operation will block until the store finishes processing this <snap-
        file>.

        If --release is used, the channel map will be displayed after the operation
        takes place.
        """
    )

    @overrides
    def fill_parser(self, parser: "argparse.ArgumentParser") -> None:
        parser.add_argument(
            "snap_file",
            metavar="snap-file",
            type=str,
            help="Snap to upload",
        )
        parser.add_argument(
            "--release",
            metavar="channels",
            dest="channels",
            type=str,
            default=None,
            help="Optional comma-separated list of channels to release to",
        )
        parser.add_argument(
            "--component",
            action="append",
            type=ComponentOption(),
            default=[],
            help=(
                "The component(s) to upload with the snap, in the format ."
                "`name=filename`. This option can be used multiple times."
            ),
        )

    @overrides
    def run(self, parsed_args):
        snap_file = pathlib.Path(parsed_args.snap_file)
        if not snap_file.exists() or not snap_file.is_file():
            raise ArgumentParsingError(f"{str(snap_file)!r} is not a valid file")

        channels: Optional[List[str]] = None
        if parsed_args.channels:
            channels = parsed_args.channels.split(",")

        client = store.StoreClientCLI()

        snap_yaml, manifest_yaml = get_data_from_snap_file(snap_file)
        snap_name = snap_yaml["name"]
        built_at = None
        if manifest_yaml:
            built_at = manifest_yaml.get("snapcraft-started-at")

        components = parsed_args.component
        expected_components = _get_components(snap_yaml)

        # validation could be simplified with sets (i.e. unions and differences)
        if expected_components:
            if not components:
                raise ValueError(
                    "Snap has components but no component files were provided. "
                    "Use `--component <name>=<filename>`."
                )

            for expected_component in expected_components:
                if expected_component not in [component.name for component in components]:
                    raise ValueError(
                        f"Component {expected_component!r} is missing."
                    )

            for provided_component in components:
                if provided_component.name not in expected_components:
                    raise ValueError(
                        f"Unknown component {provided_component.name!r}."
                    )

                component_filepath = snap_file.parent / provided_component.filename
                if not component_filepath.exists():
                    raise RuntimeError(f"{component_filepath} does not exist!")

        client.verify_upload(snap_name=snap_name)

        upload_id = client.store_client.upload_file(
            filepath=snap_file, monitor_callback=create_callback
        )

        component_upload_ids: dict[str, str] = {}
        for component in components:
            component_file = snap_file.parent / component.filename
            build_id = client.store_client.upload_file(
                filepath=component_file, monitor_callback=create_callback
            )
            component_upload_ids[component.name] = build_id

        revision = client.notify_upload(
            snap_name=snap_name,
            upload_id=upload_id,
            built_at=built_at,
            channels=channels,
            snap_file_size=snap_file.stat().st_size,
            components=component_upload_ids,
        )

        message = f"Revision {revision!r} created for {snap_name!r}"
        if channels:
            message += f" and released to {utils.humanize_list(channels, 'and')}"
        emit.message(message)


def _get_components(snap_yaml: dict[str, Any]) -> list[str] | None:
    """Return a dictionary of component names to their filenames."""
    if not snap_yaml.get("components"):
        emit.debug("No components found in snap metadata.")
        return None

    return snap_yaml["components"].keys()


def create_callback(encoder: MultipartEncoder):
    """Create a callback suitable for upload_file."""
    with emit.progress_bar("Uploading...", encoder.len, delta=False) as progress:

        def progress_callback(monitor: MultipartEncoderMonitor):
            progress.advance(monitor.bytes_read)

        return progress_callback


class StoreLegacyPushCommand(StoreUploadCommand):
    """Legacy command to upload a snap to the Snap Store."""

    name = "push"
    hidden = True
