# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 10:38:40 2015
@author: ktritz
"""

import sys
import os
import importlib
import numpy as np
from .fdp_globals import FDP_DIR, VERBOSE


def parse_method(obj, level=None):
    if VERBOSE: print('Begin parse_method({}, {})'.format(obj, level))
    if level is None:
        branch = obj._get_branch()
        branch_list = branch.split('.')
        module = branch_list.pop()
        method_path = os.path.join(FDP_DIR,
                                   'methods',
                                   obj._root._name,
                                   *branch_list)
    elif level is 'top':
        module = 'methods'
        method_path = FDP_DIR
    else:
        module = obj._name
        method_path = os.path.join(FDP_DIR, 'methods')
    if VERBOSE: print('->parsing module "{}" in {}'.format(module, method_path))
    sys.path.insert(0, method_path)
    try:
        if VERBOSE: print('->Importing module {}'.format(module))
        method_object = importlib.import_module(module)
        if not hasattr(method_object, '__all__'):
            if VERBOSE: print('->No methods to attach\nEnd parse_method()')
            return
        for method in method_object.__all__:
            if VERBOSE: print('->Attaching method {}'.format(method))
            method_from_object = getattr(method_object, method)
            setattr(obj, method, method_from_object)
    except ImportError:
        pass
    sys.path.pop(0)
    if VERBOSE: print('End parse_method({}, {})'.format(obj, level))


def parse_defaults(element):
    keys = element.keys()
    method_defaults = '_{}_defaults'.format(element.get('method'))
    keys.remove('method')
    defaults_dict = {key: element.get(key) for key in keys}
    return method_defaults, defaults_dict


def parse_signal(obj, element):
    if VERBOSE: print('Begin parse_signal({}, {})'.
                      format(obj._name, element.get('name')))
    units = parse_units(obj, element)
    axes, transpose = parse_axes(obj, element)
    number_range = element.get('range')
    if number_range is None:
        name = element.get('name')
        title = element.get('title')
        desc = element.get('desc')
        mdspath, dim_of = parse_mdspath(obj, element)
        mdstree = parse_mdstree(obj, element)
        error = parse_error(obj, element)
        signal_dict = [{'_name': name, 'units': units, 'axes': axes,
                        '_mdsnode': mdspath, '_mdstree': mdstree,
                        '_dim_of': dim_of, '_error': error, '_parent': obj,
                        '_transpose': transpose, '_title': title,
                        '_desc': desc}]
    else:
        number_list = number_range.split(',')
        name_range = element.get('namerange')
        if name_range is None:
            name_list = number_list
        else:
            name_list = name_range.split(',')
            if len(name_list) != len(number_list):
                name_list = number_list
        if len(number_list) == 1:
            start = 0
            end = int(number_list[0])
            namestart = 0
            nameend = int(name_list[0])
        else:
            start = int(number_list[0])
            end = int(number_list[1])+1
            namestart = int(name_list[0])
            nameend = int(name_list[1])+1
        signal_dict = []
        if len(name_list)==3:
            digits = int(name_list[2])
        else:
            digits = int(np.ceil(np.log10(end-1)))
        for i, index in enumerate(range(start, end)):
            nrange = range(namestart, nameend)
            name = element.get('name').format(str(nrange[i]).zfill(digits))
            title = None
            if element.get('title'):
                title = element.get('title').format(str(index).zfill(digits))
            desc = None
            if element.get('desc'):
                desc = element.get('desc').format(str(index).zfill(digits))
            mdspath, dim_of = parse_mdspath(obj, element)
            mdspath = mdspath.format(str(index).zfill(digits))
            mdstree = parse_mdstree(obj, element)
            error = parse_error(obj, element)
            signal_dict.append({'_name': name, 'units': units, 'axes': axes,
                                '_mdsnode': mdspath, '_mdstree': mdstree,
                                '_dim_of': dim_of, '_error': error,
                                '_parent': obj, '_transpose': transpose,
                                '_title': title, '_desc': desc})
    if VERBOSE: print('End parse_signal({}, {})'.
                      format(obj._name, element.get('name')))
    return signal_dict


def parse_axes(obj, element):
    axes = []
    transpose = None
    time_ind = 0
    try:
        axes = [axis.strip() for axis in element.get('axes').split(',')]
        if 'time' in axes:
            time_ind = axes.index('time')
            if time_ind is not 0:
                transpose = list(range(len(axes)))
                transpose.pop(time_ind)
                transpose.insert(0, time_ind)
                axes.pop(time_ind)
                axes.insert(0, 'time')
    except:
        pass

    return axes, transpose


def parse_refs(obj, element, transpose=None):
    refs = None
    try:
        refs = [ref.strip() for ref in element.get('axes_refs').split(',')]
        if transpose is not None:
            refs = [refs[index] for index in transpose]
    except:
        pass

    return refs


def parse_units(obj, element):
    units = element.get('units')
    if units is None:
        try:
            units = obj.units
        except:
            pass
    return units


def parse_error(obj, element):
    error = element.get('error')
    if error is not None:
        mdspath = element.get('mdspath')
        if mdspath is None:
            try:
                mdspath = obj._mdspath
                error = '.'.join([mdspath, error])
            except:
                pass
        else:
            error = '.'.join([mdspath, error])
    return error


_path_dict = {}


def parse_mdspath(obj, element):
    global _path_dict

    key = (type(obj), element)
    try:
        return _path_dict[key]
    except KeyError:
        mdspath = element.get('mdspath')
        try:
            dim_of = int(element.get('dim_of'))
        except:
            dim_of = None
        if mdspath is None:
            try:
                mdspath = obj._mdspath
            except:
                pass
        if mdspath is not None:
            mdspath = '.'.join([mdspath, element.get('mdsnode')])
        else:
            mdspath = element.get('mdsnode')
        _path_dict[key] = (mdspath, dim_of)
        return mdspath, dim_of


def parse_mdstree(obj, element):
    mdstree = element.get('mdstree')
    if mdstree is None and hasattr(obj, '_mdstree'):
        mdstree = obj._mdstree
    return mdstree
