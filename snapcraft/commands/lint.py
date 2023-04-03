# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023 Canonical Ltd.
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

"""Snapcraft lint commands."""

import argparse
import os
import subprocess
import tempfile
import textwrap
from typing import Dict, Any, Optional
from pathlib import Path

import yaml
from craft_cli import BaseCommand, emit
from craft_cli.errors import ArgumentParsingError
from overrides import overrides

from snapcraft import errors, linters, projects, providers
from snapcraft.linters import LinterStatus
from snapcraft.parts.lifecycle import (
    apply_yaml,
    extract_parse_info,
    process_yaml,
)
from snapcraft.projects import Project
from snapcraft.utils import get_host_architecture, is_managed_mode


class LintCommand(BaseCommand):
    """Lint-related commands."""

    name = "lint"
    help_msg = "Lint a snap file"
    overview = textwrap.dedent(
        """
        Creates an instance, installs a snap file, and lints the contents of the snap.
        """
    )

    @overrides
    def fill_parser(self, parser: "argparse.ArgumentParser") -> None:
        parser.add_argument(
            "snap_file",
            metavar="snap-file",
            type=Path,
            help="Snap file to lint",
        )
        parser.add_argument(
            "--use-lxd",
            action="store_true",
            help="Use LXD to lint",
        )
        parser.add_argument(
            "--http-proxy",
            type=str,
            default=os.getenv("http_proxy"),
            help="Set http proxy",
        )
        parser.add_argument(
            "--https-proxy",
            type=str,
            default=os.getenv("https_proxy"),
            help="Set https proxy",
        )

    @overrides
    def run(self, parsed_args):
        """Run the linter command."""
        emit.debug("Running linter.")
        snap_file = Path(parsed_args.snap_file)

        if not snap_file.exists() or not snap_file.is_file():
            raise ArgumentParsingError(f"{str(snap_file)!r} is not a valid file.")

        if (
            not is_managed_mode()
            and not os.getenv("SNAPCRAFT_BUILD_ENVIRONMENT") == "host"
        ):
            self._run_in_provider(parsed_args)
        else:
            emit.debug("Running snapcraft linter inside a managed instance.")
            self._run_linter(snap_file=snap_file)

        emit.debug("linter run successfully")

    def _run_linter(self, snap_file: Path):
        """Run snapcraft linter on an installed snap's directory."""
        snap_metadata = self._load_snap_metadata(snap_file, Path("meta/snap.yaml"))

        # TODO: ensure snap is not core18|20

        # install snap
        command = ["snap", "install", str(snap_file), "--dangerous"]
        emit.debug("Installing snap {snap_file}.")
        try:
            subprocess.check_output(command, text=True)
        except subprocess.SubprocessError as error:
            raise errors.SnapcraftError(
                "Failed to install snap {snap_data['name']}.",
            ) from error


        lint_filters = self._get_lint_filters(snap_file=snap_file)

        issues = linters.run_linters(
            Path(f"/snap/{snap_metadata['name']}/current/"), lint=lint_filters
        )
        status = linters.report(issues, intermediate=True)

        # In case of linter errors, stop execution and return the error code.
        if status in (LinterStatus.ERRORS, LinterStatus.FATAL):
            raise errors.LinterError("Linter errors found", exit_code=status)

    def _run_in_provider(self, parsed_args):
        """Setup an instance and execute `snapcraft lint` inside the instance."""
        # setup provider
        emit.debug("Checking build provider availability")
        provider_name = "lxd" if parsed_args.use_lxd else None
        provider = providers.get_provider(provider_name)
        providers.ensure_provider_is_available(provider)

        # create base configuration
        instance_name = "snapcraft-linter"
        project_path = Path().absolute()
        build_base = providers.SNAPCRAFT_BASE_TO_PROVIDER_BASE["core22"]
        base_configuration = providers.get_base_configuration(
            alias=build_base,
            instance_name=instance_name,
            http_proxy=parsed_args.http_proxy,
            https_proxy=parsed_args.https_proxy,
        )

        # launch instance
        emit.progress("Launching instance...")
        with provider.launched_environment(
            project_name="linter",
            project_path=project_path,
            base_configuration=base_configuration,
            build_base=build_base.value,
            instance_name=instance_name,
        ) as instance:
            # push snap file into instance
            instance.push_file(
                source=parsed_args.snap_file,
                destination=Path("/root") / parsed_args.snap_file.name,
            )

            # run linter in managed mode
            cmd = ["snapcraft", "lint", str(parsed_args.snap_file)]
            instance.execute_run(cmd, check=True)

    def _load_snap_metadata(
        self, snap_file: Path, file: Path
    ) -> Optional[Dict[Any, Any]]:
        """Load yaml data from a snap file.

        :param snap_file: Snap package to extract data from.
        :param file: Relative path of yaml file inside snap package to load.

        :returns: A dictionary containing the snap metadata or None if the file
        does not exist.
        """
        snap_file = snap_file.resolve()

        with tempfile.TemporaryDirectory(prefix=str(snap_file.parent)) as temp_dir:
            emit.debug(f"Unsquashing snap file {snap_file.name}")

            # unsquashfs [options] filesystem [directories or files to extract]
            # options:
            # -force: if file already exists then overwrite
            # -dest <pathname>: unsquash to <pathname>
            extract_command = ["unsquashfs", "-force", "-dest", temp_dir, snap_file]

            try:
                subprocess.check_output(extract_command, text=True)
            except subprocess.SubprocessError as error:
                raise errors.SnapcraftError(
                    f"Failed to unsquash snap file {snap_file.name}"
                ) from error

            try:
                with open(Path(temp_dir) / file) as snap_yaml:
                    return yaml.safe_load(snap_yaml)
            except FileNotFoundError:
                emit.progress(
                    f"Could not find file {file} in snap package {snap_file.name}."
                )
                return None

    def _get_lint_filters(self, snap_file: Path) -> Optional[projects.Lint]:
        """Get lint filters from snapcraft.yaml, if present.

        The snapcraft.yaml will exist if the snap was built with `--enable-manifest`.

        :returns: The linter configuration defined for the snap.
        """
        snapcraft_yaml = self._load_snap_metadata(
            snap_file, Path("snap/snapcraft.yaml")
        )

        if not snapcraft_yaml:
            emit.debug("Not applying lint filters.")
            return None

        # Run this to trigger legacy behavior
        yaml_data = process_yaml(snap_file)
        # process yaml before unmarshalling the data
        arch = get_host_architecture()
        yaml_data_for_arch = apply_yaml(yaml_data, arch, arch)
        # discard parse-info - it is not needed
        extract_parse_info(yaml_data_for_arch)
        project = Project.unmarshal(yaml_data_for_arch)

        return project.lint
