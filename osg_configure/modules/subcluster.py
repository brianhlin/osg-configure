import logging
import re
import ConfigParser

from osg_configure.modules import exceptions
from osg_configure.modules import utilities

REQUIRED = "required"
OPTIONAL = "optional"

STRING = "str"
POSITIVE_INT = "positive int"
POSITIVE_FLOAT = "positive float"
LIST = "list"
BOOLEAN = "boolean"

ENTRIES = {
    "name": (REQUIRED, STRING),
    "cpu_vendor": (REQUIRED, STRING),
    "cpu_model": (REQUIRED, STRING),
    "cores_per_node": (REQUIRED, POSITIVE_INT),
    "node_count": (REQUIRED, POSITIVE_INT),
    "cpus_per_node": (REQUIRED, POSITIVE_INT),
    "cpu_speed_mhz": (REQUIRED, POSITIVE_FLOAT),
    "ram_mb": (REQUIRED, POSITIVE_INT),
    "swap_mb": (OPTIONAL, POSITIVE_INT),
    "SI00": (OPTIONAL, POSITIVE_FLOAT),
    "HEPSPEC": (OPTIONAL, POSITIVE_FLOAT),
    "SF00": (OPTIONAL, POSITIVE_FLOAT),
    "inbound_network": (REQUIRED, BOOLEAN),
    "outbound_network": (REQUIRED, BOOLEAN),
    "cpu_platform": (REQUIRED, STRING),
    "allowed_vos": (OPTIONAL, STRING),
    "max_wall_time": (OPTIONAL, POSITIVE_INT),
    "extra_requirements": (OPTIONAL, STRING),
    "extra_transforms": (OPTIONAL, STRING),
}

BANNED_ENTRIES = {
    "name": "SUBCLUSTER_NAME",
    "node_count": "NUMBER_OF_NODE",
    "ram_mb": "MB_OF_RAM",
    "cpu_model": "CPU_MODEL_FROM_/proc/cpuinfo",
    "cpu_vendor": "VENDOR_AMD_OR_INTEL",
    "cpu_speed_mhz": "CLOCK_SPEED_MHZ",
    "cpu_platform": "x86_64_OR_i686",
    "cpus_per_node": "#_PHYSICAL_CHIPS_PER_NODE",
    "cores_per_node": "#_CORES_PER_NODE",
}

ENTRY_RANGES = {
    'SF00': (500, 320000),
    'SI00': (500, 320000),
    'HEPSPEC': (2, 3200),
    'ram_mb': (512, 8388608),
    'swap_mb': (512, 8388608),
    'cpus_per_node': (1, 2048),
    'cores_per_node': (1, 8192),
}


def check_entry(config, section, option, status, kind):
    """
    Check entries to make sure that they conform to the correct range of values
    """
    entry = None
    try:
        entry = str(config.get(section, option)).strip()
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError, ConfigParser.InterpolationError):
        pass
    if not entry and status == REQUIRED:
        raise exceptions.SettingError("Can't get value for mandatory setting %s in section %s." % \
                                      (option, section))
    elif not entry and status == OPTIONAL:
        return None
    if kind == STRING:
        # No parsing we can do for strings.
        return entry
    elif kind == POSITIVE_INT:
        try:
            entry = int(entry)
            if entry < 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise exceptions.SettingError("Value of option `%s` in section " \
                                          "`%s` should be a positive integer, but it is `%s`" % \
                                          (option, section, entry))
        return entry
    elif kind == POSITIVE_FLOAT:
        try:
            entry = float(entry)
            if entry < 0:
                raise ValueError()
        except (TypeError, ValueError):
            raise exceptions.SettingError("Value of option `%s` in section " \
                                          "`%s` should be a positive float, but it is `%s`" % \
                                          (option, section, entry))
        return entry
    elif kind == BOOLEAN:
        entry = entry.lower()
        possible_vals = ['t', 'true', 'yes', 'y', 'enable', 'enabled', 'f',
                         'false', 'no', 'n', 'disable', 'disabled']
        positive_vals = ['t', 'true', 'yes', 'y', 'enable', 'enabled']
        if entry not in possible_vals:
            raise exceptions.SettingError("Value of option `%s` in section " \
                                          "`%s` should be a boolean, but it is `%s`" % (option,
                                                                                        section,
                                                                                        entry))
        return entry in positive_vals
    elif kind == LIST:
        regex = re.compile(r'\s*,*\s*')
        entry = regex.split(entry)
        return entry

    else:
        # Kind of entry isn't known... OK for now.
        return entry


def check_section(config, section):
    """
    Check attributes related to a subcluster and make sure that they are consistent
    """
    if section.lower().find('changeme') >= 0:
        msg = "You have a section named 'Subcluster CHANGEME', you must change this name.\n"
        msg += "'Subcluster Main' is an example"
        raise exceptions.SettingError(msg)

    for option, value in ENTRIES.items():
        status, kind = value
        entry = check_entry(config, section, option, status, kind)
        if option in BANNED_ENTRIES and entry == BANNED_ENTRIES[option]:
            raise exceptions.SettingError("Value for %s in section %s is " \
                                          "a default or banned entry (%s); " \
                                          "you must change this value." % \
                                          (option, section, BANNED_ENTRIES[option]))
        if entry is None:
            continue

        try:
            range_min, range_max = ENTRY_RANGES[option]

            if not (range_min <= entry <= range_max):
                msg = ("Value for %(option)s in section %(section)s is outside allowed range"
                       ", %(range_min)d-%(range_max)d" % locals())
                if option == 'HEPSPEC':
                    msg += '.  The conversion factor from HEPSPEC to SI2K is 250'
                raise exceptions.SettingError(msg)
        except KeyError:
            pass


def check_config(config):
    """
    Check all subcluster definitions in an entire config
    :type config: ConfigParser.ConfigParser
    :return: True if there are any subcluster definitions, False otherwise
    """
    has_sc = False
    for section in config.sections():
        if not section.lower().startswith('subcluster'):
            continue
        has_sc = True
        check_section(config, section)
    return has_sc


def resource_catalog_from_config(config, logger=utilities.NullLogger, default_allowed_vos=None):
    """
    Create a ResourceCatalog from the subcluster entries in a config
    :type config: ConfigParser.ConfigParser
    :type logger: logging.Logger or None
    :rtype: ResourceCatalog
    """
    assert isinstance(config, ConfigParser.ConfigParser)
    from osg_configure.modules import resourcecatalog

    rc = resourcecatalog.ResourceCatalog()

    subclusters_without_max_wall_time = []
    for section in config.sections():
        prefix = None
        if section.lower().startswith('subcluster'):
            prefix = 'subcluster'
        elif section.lower().startswith('resource entry'):
            prefix = 'resource entry'
        else:
            continue

        check_section(config, section)

        rcentry = resourcecatalog.RCEntry()

        subcluster = section[len(prefix):].lstrip()

        rcentry.name = config.get(section, 'name')
        rcentry.cpus = config.getint(section, 'cores_per_node')
        rcentry.memory = config.getint(section, 'ram_mb')
        rcentry.allowed_vos = utilities.config_safe_get(config, section, 'allowed_vos',
                                                        default=default_allowed_vos)
        max_wall_time = utilities.config_safe_get(config, section, 'max_wall_time')
        if not max_wall_time:
            rcentry.max_wall_time = 1440
            subclusters_without_max_wall_time.append(subcluster)
        else:
            rcentry.max_wall_time = max_wall_time.strip()
        rcentry.queue = utilities.config_safe_get(config, section, 'queue')

        # The ability to specify extra requirements is disabled until admins demand it
        # rcentry.extra_requirements = utilities.config_safe_get(config, section, 'extra_requirements')
        rcentry.extra_requirements = None
        rcentry.extra_transforms = utilities.config_safe_get(config, section, 'extra_transforms')

        rc.add_rcentry(rcentry)
    # end for section in config.sections()

    if subclusters_without_max_wall_time:
        logger.warning("No max_wall_time specified for some subclusters; defaulting to 1440."
                       "\nAdd 'max_wall_time=1440' to the following subcluster(s) to clear this warning:"
                       "\n%s" % ", ".join(subclusters_without_max_wall_time))

    return rc
