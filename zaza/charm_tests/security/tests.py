#!/usr/bin/env python3

# Copyright 2018 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Encapsulate general security testing."""

import unittest

import zaza.model as model
import zaza.charm_lifecycle.utils as utils
import zaza.utilities.openstack as zaza_openstack


def _make_test_function(application, file_details):
    def test(self):
        until = file_details.get('until')
        since = file_details.get('since')
        expected_owner = file_details.get("owner", "root")
        expected_group = file_details.get("group", "root")
        expected_mode = file_details.get("mode", "600")
        for unit in model.get_units(application):
            # Have we configured a until or since for this file?
            if until or since:
                release = zaza_openstack \
                    .get_current_os_release_pair(application).split('_')[-1]
                current_release = zaza_openstack.get_os_release(release)
                if until:
                    until_release = zaza_openstack.get_os_release(until)
                    if current_release >= until_release:
                        return self.skipTest("{!r} is before {!r}".
                                             format(until, release))
                if since:
                    since_release = zaza_openstack.get_os_release(since)
                    if current_release <= since_release:
                        return self.skipTest("{!r} is after {!r}".
                                             format(since, release))
            unit = unit.entity_id
            result = model.run_on_unit(
                unit, 'stat -c "%U %G %a" {}'.format(file_details['path']))
            ownership = result['Stdout']
            owner, group, mode = ownership.split()
            self.assertEqual(expected_owner,
                             owner,
                             "Owner is incorrect for {}: {}"
                             .format(unit, owner))
            self.assertEqual(expected_group,
                             group,
                             "Group is incorrect for {}: {}"
                             .format(unit, group))
            self.assertEqual(expected_mode,
                             mode,
                             "Mode is incorrect for {}: {}"
                             .format(unit, mode))
    return test


def _add_tests():
    def class_decorator(cls):
        """Add tests based on input yaml to `cls`."""
        files = utils.get_charm_config('./file-assertions.yaml')
        deployed_applications = model.sync_deployed()
        for name, attributes in files.items():
            # Lets make sure to only add tests for deployed applications
            if name in deployed_applications:
                for file in attributes['files']:
                    test_func = _make_test_function(name, file)
                    test_name = 'test_{}_{}'.format(name, file['path'])
                    if file.get('until'):
                        test_name += '_until_{}'.format(file['until'])
                    if file.get('since'):
                        test_name += '_since_{}'.format(file['since'])
                    setattr(
                        cls,
                        test_name,
                        test_func)
        return cls
    return class_decorator


class FileOwnershipTest(unittest.TestCase):
    """Encapsulate File ownership tests."""

    pass


FileOwnershipTest = _add_tests()(FileOwnershipTest)
