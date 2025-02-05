# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2016-2018 Canonical Ltd
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

import os
from unittest.mock import patch

import fixtures
import progressbar
import requests

from snapcraft_legacy.internal import indicators
from tests.legacy import unit


class DumbTerminalTests(unit.TestCase):
    @patch("os.isatty")
    def setUp(self, mock_os_isatty):
        super().setUp()
        self.mock_os_isatty = mock_os_isatty
        self.mock_os_isatty.return_value = True

    def test_tty_terminal(self):
        self.assertTrue(indicators.is_dumb_terminal())

    def test_not_a_tty_terminal(self):
        self.mock_os_isatty.return_value = False
        self.assertFalse(indicators.is_dumb_terminal())

    def test_dumb_terminal_environment(self):
        self.useFixture(fixtures.EnvironmentVariable("TERM", "dumb"))
        self.assertTrue(indicators.is_dumb_terminal())

    def test_vt100_terminal_environmment(self):
        self.useFixture(fixtures.EnvironmentVariable("TERM", "vt100"))
        self.assertFalse(indicators.is_dumb_terminal())


class TestProgressBarInitialization:

    scenarios = [("Terminal", {"is_dumb": True}), ("Dumb Terminal", {"is_dumb": False})]

    def test_init_progress_bar_with_length(self, monkeypatch, is_dumb):
        monkeypatch.setattr(indicators, "is_dumb_terminal", lambda: is_dumb)

        pb = indicators._init_progress_bar(10, "destination", "message")

        assert pb.maxval == 10
        assert "message" in pb.widgets

        pb_widgets_types = [type(w) for w in pb.widgets]

        assert type(progressbar.Percentage()) in pb_widgets_types
        assert (type(progressbar.Bar()) in pb_widgets_types) is not is_dumb

    def test_init_progress_bar_with_unknown_length(self, monkeypatch, is_dumb):
        monkeypatch.setattr(indicators, "is_dumb_terminal", lambda: is_dumb)

        pb = indicators._init_progress_bar(0, "destination", "message")

        assert pb.maxval == progressbar.UnknownLength
        assert "message" in pb.widgets

        pb_widgets_types = [type(w) for w in pb.widgets]

        assert (type(progressbar.AnimatedMarker()) in pb_widgets_types) is not is_dumb


class IndicatorsDownloadTests(unit.FakeFileHTTPServerBasedTestCase):
    def setUp(self):
        super().setUp()

        dest_dir = "dst"
        os.makedirs(dest_dir)
        self.file_name = "snapcraft.yaml"
        self.dest_file = os.path.join(dest_dir, self.file_name)
        self.source = "http://{}:{}/{file_name}".format(
            *self.server.server_address, file_name=self.file_name
        )

    def test_download_request_stream(self):
        request = requests.get(self.source, stream=True, allow_redirects=True)
        indicators.download_requests_stream(request, self.dest_file)

        self.assertTrue(os.path.exists(self.dest_file))

    def test_download_urllib_source(self):
        indicators.download_urllib_source(self.source, self.dest_file)

        self.assertTrue(os.path.exists(self.dest_file))
