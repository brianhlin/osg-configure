#!/usr/bin/env python
from __future__ import print_function

import errno
import fnmatch
import pwd
import re
import sys

from collections import namedtuple
from itertools import ifilter


DEFAULT_VOMS_MAPFILE = "/usr/share/osg/voms-mapfile-default"
VOMS_MAPFILE = " /etc/grid-security/voms-mapfile "
BAN_MAPFILE = "/etc/grid-security/ban-voms-mapfile"


class Mapping(namedtuple('Mapping', 'pattern user')):
    """Pairs of VOMS attrib patterns and Unix users"""
    __slots__ = ()


def read_mapfiles():
    mappings = []

    # matches stuff like
    #   "/GLOW/*" glow
    #   "/cms/Role=pilot/Capability=NULL" cmspilot
    # and extracts the stuff between the quotes, and the username in the second field
    regex = re.compile(r'^\s*["](/[^"]+)["]\s+([A-Za-z0-9_]+)\s*(?:$|[#])')
    for filepath in [DEFAULT_VOMS_MAPFILE, VOMS_MAPFILE]:
        try:
            with open(filepath, 'r') as filehandle:
                for line in filehandle:
                    match = regex.match(line)
                    if not match:
                        continue
                    else:
                        mappings.append(Mapping(match.group(1), match.group(2)))
        except EnvironmentError as err:
            if err.errno == errno.ENOENT:
                continue
            else:
                raise

    return mappings


def read_banfile():
    # matches stuff like
    #    "/GLOW/*"
    # and extracts the stuff between the quotes
    regex = re.compile(r'^\s*["](/[^"]+)["]\s*(?:$|[#])')
    bans = []

    try:
        with open(BAN_MAPFILE, 'r') as filehandle:
            for line in filehandle:
                match = regex.match(line)
                if not match:
                    continue
                else:
                    bans.append(match.group(1))
    except EnvironmentError as err:
        if err.errno == errno.ENOENT:
            sys.stdout.write(BAN_MAPFILE + " not found - all mappings might fail!")
        else:
            raise

    return bans


def filter_out_bans(mappings, bans):
    new_mappings = []
    for mapping in mappings:
        for ban in bans:
            if fnmatch.fnmatch(mapping.pattern, ban):
                break
        else:
            new_mappings.append(mapping)
    return new_mappings


def filter_by_existing_users(mappings):
    usernames = [x[0] for x in pwd.getpwall()]
    new_mappings = [mapping for mapping in mappings if mapping.user in usernames]
    return new_mappings


def get_vos(mappings):
    regex = re.compile("^/(\w+)/")
    patterns = (m.pattern for m in mappings)
    matches = ifilter(None, (regex.match(p) for p in patterns))
    vo_groups = set(m.group(1).lower() for m in matches)

    return vo_groups


def get_allowed_vos():
    return get_vos(filter_by_existing_users(filter_out_bans(read_mapfiles(), read_banfile())))


def main(*args):
    print(get_allowed_vos())
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
