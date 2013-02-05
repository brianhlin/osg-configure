"""Unit tests to test slurm configuration"""

#pylint: disable=W0703
#pylint: disable=R0904

import os
import sys
import unittest
import ConfigParser
import logging

# setup system library path 
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.configure_modules import slurm
from osg_configure.modules.utilities import get_test_config

global_logger = logging.getLogger(__name__)
if sys.version_info[0] >= 2 and sys.version_info[1] > 6:
  global_logger.addHandler(logging.NullHandler())
else:
  # NullHandler is only in python 2.7 and above
  class NullHandler(logging.Handler):
    def emit(self, record):
      pass
            
  global_logger.addHandler(NullHandler())

class TestSlurm(unittest.TestCase):
  """
  Unit test class to test SlurmConfiguration class
  """

  def testParsing(self):
    """
    Test configuration parsing
    """
    
    config_file = get_test_config("slurm/slurm1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    options = {'OSG_JOB_MANAGER_HOME' : '/opt/slurm',
               'OSG_PBS_LOCATION' : '/opt/slurm',
               'OSG_JOB_CONTACT' : 'my.domain.com/jobmanager-pbs',
               'OSG_UTIL_CONTACT' : 'my.domain.com/jobmanager',
               'OSG_JOB_MANAGER' : 'SLURM'}
    for option in options:
      value = options[option]
      self.assertTrue(attributes.has_key(option), 
                      "Attribute %s missing" % option)
      err_msg = "Wrong value obtained for %s, " \
                "got %s instead of %s" % (option, attributes[option], value)
      self.assertEqual(attributes[option], value, err_msg)




  def testParsingDisabled(self):
    """
    Test PBS section parsing when set to disabled
    """
    
    config_file = get_test_config("slurm/slurm_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.assertEqual(len(attributes), 0, 
                     "Disabled configuration should have no attributes")
    
  def testParsingIgnored(self):
    """
    Test PBS section parsing when set to Ignore
    """
    
    config_file = get_test_config("slurm/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.assertEqual(len(attributes), 0, 
                     "Ignored configuration should have no attributes")

                            
  def testMissingPBSLocation(self):
    """
    Test the checkAttributes function to see if it catches missing pbs location
    """
    config_file = get_test_config("slurm/missing_location.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()    
    self.assertFalse(settings.checkAttributes(attributes), 
                     "Did not notice missing pbs location")


  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """
    config_file = get_test_config("slurm/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.assertTrue(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as invalid")

  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it works on valid settings
    """
    config_file = get_test_config("slurm/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.assertTrue(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as invalid")
    
  def testInvalidJobContact(self):
    """
    Test the checkAttributes function to see if it catches invalid job contacts
    """
    config_file = get_test_config("slurm/invalid_job_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      print e
      self.fail("Received exception while parsing configuration")
 
    attributes = settings.getAttributes()
    self.assertFalse(settings.checkAttributes(attributes), 
                     "Did not notice invalid host in jobcontact option")

  def testInvalidUtilityContact(self):
    """
    Test the checkAttributes function to see if it catches invalid
    utility contacts
    """
    config_file = get_test_config("slurm/invalid_utility_contact.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.assertFalse(settings.checkAttributes(attributes), 
                     "Did not notice invalid host in utility_contact option")

  def testServiceList(self):
    """
    Test to make sure right services get returned
    """
    
    config_file = get_test_config("slurm/check_ok.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set(['globus-gatekeeper',
                             'globus-gridftp-server'])
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))
    
    config_file = get_test_config("slurm/seg_enabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set(['globus-gatekeeper', 
                             'globus-gridftp-server'])
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))
    
    config_file = get_test_config("slurm/pbs_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set()
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))    

    config_file = get_test_config("slurm/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = slurm.SlurmConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
    services = settings.enabledServices()
    expected_services = set()
    self.assertEqual(services, expected_services,
                     "List of enabled services incorrect, " +
                     "got %s but expected %s" % (services, expected_services))      
      
if __name__ == '__main__':
  console = logging.StreamHandler()
  console.setLevel(logging.ERROR)
  global_logger.addHandler(console)  
  unittest.main()
