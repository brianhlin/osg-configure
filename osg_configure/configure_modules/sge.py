#!/usr/bin/python

""" Module to handle attributes related to the sge jobmanager configuration """

import ConfigParser, os

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules import exceptions
from osg_configure.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['SGEConfiguration']

SGE_CONFIG_FILE = '/etc/grid-services/available/jobmanager-sge'

class SGEConfiguration(JobManagerConfiguration):
  """Class to handle attributes related to sge job manager configuration"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(SGEConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('SGEConfiguration.__init__ started')    
    self.__mappings = {'sge_root': 'OSG_SGE_ROOT',
                       'sge_cell': 'OSG_SGE_CELL',
                       'job_contact': 'OSG_JOB_CONTACT',
                       'util_contact': 'OSG_UTIL_CONTACT',
                       'accept_limited': 'accept_limited'}
    self.__optional = ['accept_limited']
    self.__defaults = {'accept_limited' : 'False'}
    
    self.__set_default = True
    self.config_section = "SGE"
    self.logger.debug('SGEConfiguration.__init__ completed')    
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('SGEConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.logger.debug('SGE section not found in config file')
      self.logger.debug('SGEConfiguration.parseConfiguration completed')    
      return
    
    if not self.setStatus(configuration):
      self.logger.debug('SGEConfiguration.parseConfiguration completed')    
      return True
       
    self.attributes['OSG_JOB_MANAGER'] = 'SGE'
    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting,
                                   self.__optional, 
                                   self.__defaults)
                                   
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)
        
    # fill in values for sge_location and home
    if self.__mappings['sge_root'] in self.attributes:
      self.attributes['OSG_JOB_MANAGER_HOME'] = \
        self.attributes[self.__mappings['sge_root']]
      self.attributes['OSG_SGE_LOCATION'] = \
        self.attributes[self.__mappings['sge_root']]
    else:
      self.attributes['OSG_JOB_MANAGER_HOME'] = 'UNAVAILABLE'
      self.attributes['OSG_SGE_LOCATION'] = 'UNAVAILABLE'
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))

    if (configuration.has_section('Managed Fork') and
        configuration.has_option('Managed Fork', 'enabled') and
        configuration.get('Managed Fork', 'enabled').upper == 'TRUE'):
      self.__set_default = False
   
    self.logger.debug('SGEConfiguration.parseConfiguration completed')    

  def getAttributes(self):
    """Return settings"""
    self.logger.debug('SGEConfiguration.getAttributes started')    
    if not self.enabled:
      self.logger.debug('SGE not enabled, returning empty dictionary')
      self.logger.debug('SGEConfiguration.parseConfiguration completed')    
      return {}
    self.logger.debug('SGEConfiguration.parseConfiguration completed')    
    return self.attributes
  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('SGEConfiguration.checkAttributes started')    
    attributes_ok = True
    if not self.enabled:
      self.logger.debug('SGE not enabled, returning True')
      self.logger.debug('SGEConfiguration.checkAttributes completed')    
      return attributes_ok
    
    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('SGEConfiguration.checkAttributes completed')    
      return attributes_ok

    # Make sure all settings are present
    for setting in self.__mappings:
      if self.__mappings[setting] not in self.attributes:
        raise exceptions.SettingError("Missing setting for %s in %s section" %
                                      (setting, self.config_section))

    # make sure locations exist
    if not validation.valid_location(self.attributes[self.__mappings['sge_root']]):
      attributes_ok = False
      self.logger.error("In %s section" % self.config_section)
      self.logger.error("%s points to non-existent location: %s" % 
                          ('sge_root',
                           self.attributes[self.__mappings['sge_root']]))

    settings_file = os.path.join(self.attributes[self.__mappings['sge_root']],
                                 self.attributes[self.__mappings['sge_cell']], 
                                 'common', 
                                 'settings.sh')
    
    if not validation.valid_file(settings_file):
      attributes_ok = False
      self.logger.error("In %s section" % self.config_section)
      self.logger.error("$SGE_ROOT/$SGE_CELL/common/settings.sh points to " \
                        "non-existent location: %s" % settings_file)

    if not self.validContact(self.attributes[self.__mappings['job_contact']], 
                             'sge'):
      attributes_ok = False
      self.logger.error("%s is not a valid job contact: %s" % 
                          ('job_contact',
                           self.attributes[self.__mappings['job_contact']]))
      
    if not self.validContact(self.attributes[self.__mappings['util_contact']], 
                             'sge'):
      attributes_ok = False
      self.logger.error("%s is not a valid util contact: %s" % 
                          ('util_contact',
                           self.attributes[self.__mappings['util_contact']]))      
      
    self.logger.debug('SGEConfiguration.checkAttributes completed')    
    return attributes_ok 
  
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('SGEConfiguration.configure started')

    if not self.enabled:
      self.logger.debug('SGE not enabled, returning True')    
      self.logger.debug('SGEConfiguration.configure completed')    
      return True

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('SGEConfiguration.configure completed')    
      return True

    # The accept_limited argument was added for Steve Timm.  We are not adding
    # it to the default config.ini template because we do not think it is
    # useful to a wider audience.
    # See VDT RT ticket 7757 for more information.
    if self.attributes[self.__mappings['accept_limited']].upper() == "TRUE":
      if not self.enable_accept_limited(SGE_CONFIG_FILE):
          self.logger.error('Error writing to condor configuration')
          self.logger.debug('SGEConfiguration.configure completed')
          return False
    elif self.attributes[self.__mappings['accept_limited']].upper() == "FALSE":
      if not self.disable_accept_limited(SGE_CONFIG_FILE):
          self.logger.error('Error writing to condor configuration')
          self.logger.debug('SGEConfiguration.configure completed')
          return False

    if self.__set_default:
        self.logger.debug('Configuring gatekeeper to use regular fork service')
        self.set_default_jobmanager('fork')

    self.logger.debug('SGEConfiguration.configure started')    
    return True
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "SGE"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]
