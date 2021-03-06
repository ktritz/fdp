#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 24 12:49:36 2017

@author: drsmith
"""

import os
from .fdp_globals import FdpError


MACHINES = ['nstxu', 'diiid', 'cmod']

MDS_SERVERS = {
    'nstxu': 'skylark.pppl.gov:8501'
}

EVENT_SERVERS = {
    'nstxu': 'skylark.pppl.gov:8501',
    'ltx': 'lithos.pppl.gov:8000'
}

LOGBOOK_CREDENTIALS = {
    'nstxu': {
        'server': 'sql2008.pppl.gov\sql2008',
        'username': os.getenv('USER') or os.getenv('USERNAME'),
        'password': 'pfcworld',
        'database': 'nstxlogs',
        'port': '62917',
        'table': 'entries'
    }
}

def machineAlias(machine):

    aliases = {
        'nstxu': ['nstx', 'nstxu', 'nstx-u'],
        'diiid': ['diiid', 'diii-d', 'd3d'],
        'cmod': ['cmod', 'c-mod']
    }

    for key, value in aliases.iteritems():
        if machine.lower() in value:
            return key
    # invalid machine name
    txt = '"{}" is not a valid machine name\n'.format(machine)
    txt = txt + 'Valid machines are:\n'
    for values in aliases.itervalues():
        txt = txt + '  {}\n'.format(values)
    raise FdpError(txt)
