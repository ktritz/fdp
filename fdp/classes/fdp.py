# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 19:35:36 2015

@author: ktritz
"""
from . import fdp_globals, factory, machine

VERBOSE = fdp_globals.VERBOSE


class Fdp(object):
    """
    The primary data object in FDP and the top-level container for machines.
    """
    def __getattr__(self, attribute):
        if VERBOSE: print('{}.__getattr__({})'.
                          format(self.__class__, attribute))
        machine_name = fdp_globals.machineAlias(attribute)
        if machine_name not in fdp_globals.MACHINES:
            raise fdp_globals.FdpError('Invalid machine name')
        # subclass machine.Machine() for <machine_name>
        MachineClassName = ''.join(['Machine', machine_name.capitalize()])
        MachineClass = type(MachineClassName, (machine.Machine, ), {})
        MachineClass._name = machine_name
        # parse fdp/methods and fdp/methods/<machine_name>
        factory.parse_method(MachineClass, level='top')
        factory.parse_method(MachineClass, level=machine_name)
        return MachineClass(machine_name)

    def __dir__(self):
        return fdp_globals.MACHINES
