"""Module for unit testing subcluster / resource entry configuration"""

# pylint: disable=W0703
# pylint: disable=R0904

import os
import sys
import unittest
import ConfigParser
import logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

global_logger = logging.getLogger(__name__)
if sys.version_info[0] >= 2 and sys.version_info[1] > 6:
    global_logger.addHandler(logging.NullHandler())
else:
    # NullHandler is only in python 2.7 and above
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

    global_logger.addHandler(NullHandler())

from osg_configure.configure_modules import localsettings

from osg_configure.modules import exceptions
from osg_configure.modules import subcluster
from osg_configure.modules import utilities

from osg_configure.modules.utilities import get_test_config


class TestSubcluster(unittest.TestCase):
    """Class for unit testing subcluster / resource entry configuration code"""

    def test_missing_sc(self):
        """
        Make sure that we have failures when there is no configured SC.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("subcluster/red-missing-sc.ini")
        config_parser.read(config_file)
        self.assertFalse(subcluster.check_config(config_parser), msg="Did not properly detect a missing SC.")

    def test_changeme4(self):
        """
        Make sure that we have failures because SC CHANGEME section is present.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("subcluster/changeme_section_sc.ini")
        config_parser.read(config_file)
        self.assertRaises(exceptions.SettingError, subcluster.check_config, config_parser) # detect enabled CHANGEME section.

    def test_missing_attributes(self):
        """
        Make sure that we have failures when there are missing attributes.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("subcluster/red-missing-attributes.ini")
        config_parser.read(config_file)
        self.assertRaises(exceptions.SettingError, subcluster.check_config, config_parser) # detect missing attrs.

    def test_new_config(self):
        """
        Make sure that we can correctly parse a correct new-style GIP config.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("subcluster/red-new-gip-config.ini")
        config_parser.read(config_file)
        self.assertTrue(subcluster.check_config(config_parser))

    def test_local_settings(self):
        """
        Test to see if the local settings parsing works.
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_parser.optionxform = str
        config_file = get_test_config("subcluster/local_settings.ini")
        config_parser.read(config_file)
        local_settings = localsettings.LocalSettings(logger= \
                                                         global_logger)
        local_settings.parse_configuration(config_parser)
        attributes = local_settings.get_attributes()
        self.assertTrue('default' not in attributes,
                        msg="Attributes set that weren't in the test config file")
        self.assertTrue('Foo' in attributes and attributes['Foo'] == 'value1',
                        msg="Incorrectly named key." \
                            "  Desired name: Foo; only found  %s." %
                            (" ".join(attributes.keys())))
        self.assertTrue(attributes['Foo'] == 'value1',
                        msg="Incorrect value wanted value1, " \
                            "got %s" % attributes['Foo'])
        self.assertTrue('bar' in attributes and attributes['bar'] == 'value2',
                        msg="Incorrectly named key." \
                            "  Desired name: bar; only found  %s." %
                            (" ".join(attributes.keys())))
        self.assertTrue('bar' in attributes and attributes['bar'] == 'value2',
                        msg="Incorrect value wanted value2, " \
                            "got %s" % attributes['bar'])

    def test_hepspec_valid(self):
        """
        Make sure a valid HEPSPEC value is accepted.
        """
        did_fail = False
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("subcluster/sc_samples.ini")
        config_parser.read(config_file)
        try:
            subcluster.check_section(config_parser, "Subcluster Valid")
        except exceptions.SettingError:
            did_fail = True
        self.assertFalse(did_fail, msg="Valid HEPSPEC entry threw an exception.")

    def test_hepspec_invalid(self):
        """
        Make sure a invalid HEPSPEC value no longer causes an error..
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("subcluster/sc_samples.ini")
        config_parser.read(config_file)
        try:
            subcluster.check_section(config_parser, "Subcluster Bad HEPSPEC")
        except exceptions.SettingError:
            self.fail(msg="Invalid HEPSPEC entry threw an exception.")
        try:
            subcluster.check_section(config_parser, "Subcluster Formerly Bad Cores")
        except exceptions.SettingError:
            self.fail(msg="Formerly Bad Cores entry threw an exception")

    def test_no_name(self):
        """
        Make sure a missing name causes an error
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("subcluster/sc_samples.ini")
        config_parser.read(config_file)
        self.assertRaises(exceptions.SettingError, subcluster.check_section, config_parser, "Subcluster No Name")

    def test_resource_entry(self):
        """
        Make sure a Resource Entry section is detected
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("subcluster/resourceentry.ini")
        config_parser.read(config_file)
        found_scs = subcluster.check_config(config_parser)
        self.assertTrue(found_scs, msg="Resource Entry Valid not found.")

    def test_resource_entry_2(self):
        """
        Make sure most subcluster attributes are optional for a
        Resource Entry section
        """
        config_parser = ConfigParser.SafeConfigParser()
        config_file = get_test_config("subcluster/resourceentry.ini")
        config_parser.read(config_file)
        did_fail = False
        for section in ["Resource Entry Valid Old Attribs",
                        "Resource Entry Valid New Attribs"]:
            try:
                subcluster.check_section(config_parser, section)
            except exceptions.SettingError:
                did_fail = True
            self.assertFalse(did_fail, msg="Section %s threw an exception." % section)


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)

    unittest.main()