#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Provide GCS functions to control a PI device."""
# Trailing newlines pylint: disable=C0305

from logging import debug
from collections import OrderedDict
import platform
import sys

# Invalid class name "basestring"  pylint: disable=C0103
# Redefining built-in 'basestring' pylint: disable=W0622
try:
    basestring
except NameError:
    basestring = str

# Redefining built-in 'unicode' pylint: disable=W0622
try:
    unicode
except NameError:
    unicode = str

__signature__ = 0x44d30904369891fbe9a995aec3c231da


def isdeviceavailable(supported_devices, device):
    """Checks if the divece is available."""
    module_is_valid = False

    # for unittests 'MagicMock' should allways be supported
    if type(device).__name__ == 'MagicMock':
        module_is_valid = True

    for supported_device in supported_devices:
        if supported_device:
            if isinstance(device, supported_device):
                module_is_valid = True

    return module_is_valid


def gethexstr(paramids):
    """Create string of 'paramids' with hexadecimal numbers.
    @param paramids : List of integers or integer convertibles of base 10 or 16.
    @return : String of 'paramids' with hexadecimal numbers.
    """
    for i, paramid in enumerate(paramids):
        try:
            paramids[i] = int(paramid)
        except ValueError:
            paramids[i] = int(paramid, base=16)
    return '[' + ', '.join(['0x%x' % x for x in paramids]) + ']'


def getsupportedcommands(qhlp, dostrip=True):
    """Parse qHLP answer and return list of available command names.
    @param qhlp : Answer of qHLP() as string.
    @param dostrip : If True strip first and last line from 'qhlp'.
    @return : List of supported command names (not function names).
    """
    qhlp = qhlp.splitlines()
    if dostrip:
        qhlp = qhlp[1:-1]
    cmds = []
    for line in qhlp:
        line = line.upper()
        cmds.append(line.split()[0].strip())
    return cmds


def getsupportedfunctions(qhlp, dostrip=True):
    """Parse qHLP answer and return list of available functions.
    @param qhlp : Answer of qHLP() as string.
    @param dostrip : If True strip first and last line from 'qhlp'.
    @return : List of supported function names (not command names).
    """
    funcnames = {
        'q*IDN': 'qIDN', '#3': 'GetPosStatus', '#5': 'IsMoving', '#6': 'HasPosChanged', '#7': 'IsControllerReady',
        '#8': 'IsRunningMacro', '#9': 'IsGeneratorRunning', '#11': 'GetDynamicMoveBufferSize', '#24': 'StopAll',
        '#4': 'GetStatus', '#27': 'SystemAbort'
    }
    qhlp = qhlp.splitlines()
    if dostrip:
        qhlp = qhlp[1:-1]
    funcs = []
    for line in qhlp:
        line = line.upper()
        funcname = line.split()[0]
        if funcname.endswith('?'):
            funcname = 'q%s' % funcname[:-1]
        if funcname == 'MAC':
            for item in ('BEG', 'DEF', 'DEF?', 'DEL', 'END', 'ERR?', 'NSTART', 'START', 'FREE?', 'STOP'):
                if line.find(item) >= 0:
                    if item.endswith('?'):
                        item = 'q%s' % item[:-1]
                    funcs.append('MAC_%s' % item)
        else:
            funcs.append(funcnames.get(funcname, funcname))
    return funcs


def getitemslist(items, valueconv=None, size=None):
    """Return list of 'items'.
    @param items : Can be None, single item or list of items.
    @param valueconv : Optionally convert each item in 'items' to this type.
    @param size : Optional size to extend 'items' with its last element as integer.
    @return : List of 'items'.
    """
    if isinstance(items, dict):
        raise TypeError('parameter type mismatch: %r' % items)
    if items in (None, '', {}):
        items = []
    items = items if isinstance(items, (list, set, tuple)) else [items]
    items = list(items)  # tuple has no attribute 'extend'
    if size:
        items.extend([items[-1]] * (size - len(items)))
    if valueconv:
        items = [convertvalue(item, valueconv) for item in items]
    return items


def getitemsvaluestuple(items, values, required=True):
    """Convert single values, lists or a dictionary lists of "items" and "values".
    @param items : Single item or list of items or dictionary of {item : value}.
    @param values : Single value or list of values or None if 'items' is a dictionary.
    @param required: If True 'values' must not be empty.
    @return : Tuple ([items], [values]).
    """
    if isinstance(items, dict):
        if values is None:
            values = list(items.values())
            items = list(items.keys())
        else:
            raise TypeError('parameter type mismatch: If <items> is a dictionary <values> must be "None"')

    items = getitemslist(items)
    values = getitemslist(values)
    if required:
        checksize((True, True), items, values)
    else:
        checksize((), items, values)
    return items, values


def getitemsparamsvaluestuple(itemdict, params, values):
    """Convert single values, lists or a dictionary lists of 'itemdict', 'params' and 'values'.
    @param itemdict : Single item or list of items or dictionary of {item : {param : value}}.
    @param params : Single value or list of values or None if 'itemdict' is a dictionary.
    @param values : Single value or list of values or None if 'itemdict' is a dictionary.
    @return : Tuple ([items], [params], [values]) where all three lists have the same length.
    """
    params = getitemslist(params)
    values = getitemslist(values)
    if isinstance(itemdict, dict):
        items = []
        for item in itemdict:
            for param in itemdict[item]:
                items.append(item)
                params.append(param)
                values.append(itemdict[item][param])
    else:
        items = getitemslist(itemdict)
    checksize((True, True, True), items, params, values)
    return items, params, values


def getitemsparamsidstuple(itemdict, params, ids):
    """Convert single values, lists or a dictionary lists of 'itemdict', 'params' and 'ids'.
    @param itemdict : Single item or list of items or dictionary of {[item, params] : [ids]}.
    @param params : Single value or list of values or None if 'itemdict' is a dictionary.
    @param ids : Single value or list of values or None if 'itemdict' is a dictionary.
    @return : Tuple ([items]], [params], [ids]) where all three lists have the same length.
    """
    params = getitemslist(params)
    ids = getitemslist(ids)
    if isinstance(itemdict, dict):
        items = []
        for item in itemdict:
            #           for param in itemdict[item]:
            #               items.append(item)
            #               params.append(param)
            #               ids.append(itemdict[item][param])
            items.append(item[0])
            params.append(item[1])
            for id in itemdict[item]:
                ids.append(id)
    else:
        items = getitemslist(itemdict)
    checksize((True, len(items), len(ids)), items, params, ids)
    return items, params, ids


# 'convertvalue' is too complex. The McCabe rating is 12 pylint: disable=R1260
#  Too many return statements pylint: disable=R0911
def convertvalue(value, totype):
    """Convert 'value' to 'totype'. For bool conversion "1" and "True" is regarded as True.
    @param value : Usually a string that gets converted. Can have whitespaces.
    @param totype : Type to convert to or None to not convert or True for automatic conversion.
    @return : Converted and stripped 'value'.
    """
    if totype is None:
        return value
    if not isinstance(value, (basestring, int, float, bool)):
        raise TypeError('parameter is of unexpected type: %r' % value)
    if isinstance(value, basestring):
        value = value.strip()
    if totype is True:
        return converttonumber(value)
    if totype is bool:
        if value in ['1', 'True']:
            return True
        if value in ['0', 'False']:
            return False
        raise ValueError('unexpected response %r for bool conversion' % value)
    if totype is int:
        try:
            return int(value, base=0)  # proper base is guessed
        except TypeError:
            return int(value)
    if totype is str and isinstance(value, unicode):
        try:
            return str(value)
        except UnicodeEncodeError:
            return value
    return totype(value)


def converttonumber(value):
    """Convert 'value' to int (dec or hex but no oct) or float if possible.
    @param value : String (no other types!) that gets converted. No whitespaces.
    @return : Converted 'value' as number or 'value' itself.
    """
    try:
        if value.find('.') < 0:
            if '0x' in value.lower():
                return int(value, base=16)
            return int(value, base=10)
        return float(value)
    except ValueError:
        try:
            return str(value)
        except UnicodeEncodeError:
            return value


def splitanswertolists(answer):
    """Split 'answer' into tuple (items, values) of lists.
    @param answer : String "item1 item2 ... = val1 val2 ...<LF>" or single "value".
    @return : Tuple ([[item1], [item2], ...], [[val1, val2, ...]]) or (None, [[values]]).
    """
    answer = answer.split('\n')
    if '=' in answer[0]:
        itemdim = len(answer[0].split('=')[0].split())
        items = [[] for _ in range(itemdim)]  # do not use [[]] * itemdim
    else:
        return None, [[x.strip() for x in answer]]
    values = []
    for line in answer:
        line = line.strip()
        if not line:
            continue
        itemvals = line.split('=')[0].split()
        for dim in range(itemdim):
            items[dim].append(itemvals[dim])
        values.append('='.join(line.split('=')[1:]).split())
    return items, values


def getdict_oneitem(answer, items, itemconv=None, valueconv=None):
    """Split 'answer' into item/values dict of according types.
    @param answer : String "item = val1 val2 ...<LF>".
    @param items : Items (e.g. axes/channels) as single item, list or None.
    @param itemconv : Conversion function for 'items'.
    @param valueconv : List of conversion functions for values. If there are more values than
    conversion functions the last given conversion function is used for the remaining values.
    @return : Ordered dictionary {item: [value1, value2, ...]} or {item: value}.
    """
    readitems, values = splitanswertolists(answer)
    if items is None:
        if not readitems:
            return {}
        items = readitems[0]
    else:
        items = getitemslist(items)
        itemconv = None
    answerdict = OrderedDict()
    multival = False
    for row, _ in enumerate(items):
        item = convertvalue(items[row], itemconv)
        answerdict[item] = []
        for colnum, value in enumerate(values[row]):
            if value:
                answerdict[item].append(convertvalue(value, valueconv[min(colnum, len(valueconv) - 1)]))
                multival |= colnum > 0
    if not multival:
        for item in answerdict:
            try:
                answerdict[item] = answerdict[item][0]
            except IndexError:
                answerdict[item] = ''
    return answerdict


# 'getdict_twoitems' is too complex. The McCabe rating is 14 pylint: disable=R1260
#  Too many branches (13/12) pylint: disable=R0912
#  Too many local variables (17/15) pylint: disable=R0914
#  Too many arguments (6/5) pylint: disable=R0913
def getdict_twoitems(answer, items1, items2, itemconv, valueconv, convlisttostring=False):
    """Split 'answer' into item/values dict of according types.
    @param answer : String "item1 item2 = val1 val2 ...<LF>" or tuple ([val1], [val2], ...).
    @param items1 : Items (e.g. axes/channels) as single item, list or empty.
    @param items2 : Items (e.g. axes/channels) as single item, list or empty.
    @param itemconv : List of two conversion functions for items. No tuple!
    @param valueconv : List of conversion functions for values. If there are more values than
    @param convlisttostring : force converting value lists to strings
    conversion functions the last given conversion function is used for the remaining values.
    @return : Ordered dictionary {item1: {item2: [value1, value2, ...]}} or
    {item1: {item2: value}}.
    """
    readitems, values = splitanswertolists(answer)
    if not items1:
        if not readitems:
            return {}
        items1 = readitems[0]
    else:
        items1 = getitemslist(items1, size=len(readitems[0]))
        itemconv[0] = None
    if not items2:
        if not readitems:
            return {}
        items2 = readitems[1]
    else:
        items2 = getitemslist(items2)
        itemconv[1] = None
    answerdict = OrderedDict()
    multival = False
    for row, _ in enumerate(items1):
        item1 = convertvalue(items1[row], itemconv[0])
        item2 = convertvalue(items2[row], itemconv[1])
        if item1 not in answerdict:
            answerdict[item1] = OrderedDict()
        answerdict[item1][item2] = []
        for colnum, value in enumerate(values[row]):
            if value:
                answerdict[item1][item2].append(convertvalue(value, valueconv[min(colnum, len(valueconv) - 1)]))
                multival |= colnum > 0

    if not multival or convlisttostring:
        for item1 in answerdict:
            for item2 in answerdict[item1]:
                try:
                    if not convlisttostring:
                        answerdict[item1][item2] = answerdict[item1][item2][0]
                    else:
                        answerdict[item1][item2] = ' '.join(convertvalue(e, str) for e in answerdict[item1][item2])

                except IndexError:
                    answerdict[item1][item2] = ''
    return answerdict


# 'getdict_threeitems' is too complex. The McCabe rating is 14 pylint: disable=R1260
#  Too many branches (13/12) pylint: disable=R0912
#  Too many local variables (17/15) pylint: disable=R0914
#  Too many arguments (6/5) pylint: disable=R0913
def getdict_threeitems(answer, items1, items2, items3, itemconv, valueconv):
    """Split 'answer' into item/values dict of according types.
    @param answer : String "item1 item2 item3= val1...<LF>" or tuple ([val1], [val2], ...).
    @param items1 : Items (e.g. axes/channels) as single item, list or empty.
    @param items2 : Items (e.g. axes/channels) as single item, list or empty.
    @param items3 : Items (e.g. axes/channels) as single item, list or empty.
    @param itemconv : List of two conversion functions for items. No tuple!
    @param valueconv : List of conversion functions for values. If there are more values than
    conversion functions the last given conversion function is used for the remaining values.
    @return : Ordered dictionary {[item1, item2]: [item3, value]}}
    """
    readitems, values = splitanswertolists(answer)
    if not items1:
        if not readitems:
            return {}
        items1 = readitems[0]
    else:
        items1 = getitemslist(items1, size=len(readitems[0]))
        itemconv[0] = None
    if not items2:
        if not readitems:
            return {}
        items2 = readitems[1]
    else:
        items2 = getitemslist(items2, size=len(readitems[1]))
        itemconv[1] = None
    if not items3:
        if not readitems:
            return {}
        items3 = readitems[2]
    else:
        items3 = getitemslist(items3, size=len(readitems[2]))
        itemconv[2] = None

    answerdict = OrderedDict()
    multival = False
    for row, _ in enumerate(items1):
        item1 = convertvalue(items1[row], itemconv[0])
        item2 = convertvalue(items2[row], itemconv[1])
        item3 = convertvalue(items3[row], itemconv[2])

        if (item1, item2) not in answerdict:
            answerdict[(item1, item2)] = OrderedDict()
        answerdict[(item1, item2)][item3] = []
        for colnum, value in enumerate(values[row]):
            if value:
                answerdict[(item1, item2)][item3].append(
                    convertvalue(value, valueconv[min(colnum, len(valueconv) - 1)])
                )

                multival |= colnum > 0
    if not multival:
        for (item1, item2) in answerdict:
            for item3 in answerdict[(item1, item2)]:
                try:
                    answerdict[(item1, item2)][item3] = answerdict[(item1, item2)][item3][0]
                except IndexError:
                    answerdict[(item1, item2)][item3] = ''
    return answerdict


def splitparams(answer, separator):
    """Split 'answer' into list of strings according to GCS1/GCS2 or 'separator'.
    @param answer : String to split.
    @param separator : True for GCS2, False for GCS1 or separator as string.
    @return : List of strings with removed leading and trailing whitespaces.
    """
    if not answer:
        return []
    answer = answer.strip()
    if isinstance(separator, basestring):
        answer = answer.split(separator)
    else:
        if separator:  # GCS2
            answer = answer.split()
        else:  # GCS1
            answer = list(answer)
    return [x.strip() for x in answer]


def getgcsheader(headerstr):
    """Split textual GCS header to key/value pairs.
    @param headerstr : GCS header with lines "# key = value <LF>" as string.
    @return : Ordered dictionary of header items.
    """
    header = OrderedDict()
    for line in headerstr.split('\n'):
        line = line.lstrip('#').strip()
        items = line.split('=')
        if len(items) == 2:
            header[items[0].strip()] = items[1].strip()
    for key in header:
        header[key] = converttonumber(header[key])
    return header


def getbitcodeditems(value, allitems=None, items=None):
    """Return boolean dictionary of 'items' according to corresponding bit in 'value'.
    If 'allitems' is None the number of bits in 'value' is used.
    @param value : Integer of the bit mask.
    @param allitems : Single item or list or None.
    Length must not match the bit width of 'value'.
    @param items : Item or list or None. Only these items are returned.
    If None then 'allitems' are returned.
    @return : Ordered dictionary {items: value} where value is True or False.
    """
    bits = bin(value)[2:][::-1]  # LSB is left
    if allitems is None:
        items = getitemslist(items)
        maxitem = max([int(x) for x in items]) if items else 0
        allitems = list(range(1, max(len(bits), maxitem) + 1))
    allitems = allitems if isinstance(allitems, (list, set, tuple)) else [allitems]
    answerdict = OrderedDict()
    items = items or allitems
    items = items if isinstance(items, (list, set, tuple)) else [items]
    for i, _ in enumerate(allitems):
        itemfound = None
        for j, _ in enumerate(items):
            if str(allitems[i]) == str(items[j]):
                itemfound = j
                break
        if itemfound is not None:
            try:
                answerdict[items[itemfound]] = bits[i] == '1'
            except IndexError:
                answerdict[items[itemfound]] = False
    return answerdict


def checksize(sizes, *args):
    """Check size of 'args'.
    @param sizes : Desired size of 'args' as list of length <= len(args). Integer for size, True if any size but
    required. If length is smaller than number of 'args' then the remaining args must have the same size.
    @param args : Items to be checked as single items, tuples or lists.
    """
    listsize = None
    for i, arg in enumerate(args):
        arg = getitemslist(arg)
        if i < len(sizes):
            size = sizes[i]
        elif i == len(sizes):
            size = len(arg)
        if size is True:
            if not arg:
                raise TypeError('a required parameter is missing')
            listsize = listsize or len(arg)
            size = listsize
        if size != len(arg):
            raise TypeError('parameter size mismatch: %r' % arg)


def logsysinfo():
    """Log which processor, operating system and python is used, useful for support."""
    debug('Processor: %s', platform.processor())
    debug('OS: %s, Architecture: %s', platform.platform(), platform.machine())
    pyver = '{0.major}.{0.minor}.{0.micro} {0.releaselevel}'.format(sys.version_info)
    debug('Python: %s %s', pyver, platform.architecture()[0])

def getparamstringofnsinglearguments(*arguments):
    """
    Gets a GCS-Command-Parameter-String of N parameters
    :param arguments: N parameters as string or list
    :return: string with parameters
    """
    parms = ''
    for i in arguments:
        if isinstance(i, str):
            parms = parms + ' ' + i
        elif isinstance(i, list):
            parms = parms + ' ' + ' '.join(str(param) for param in i)
        else:
            raise TypeError

    return parms
