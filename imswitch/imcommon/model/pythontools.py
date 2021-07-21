import re


def joinModulePath(segment1, segment2):
    """ Joins two module path segments, e.g. "imswitch.imcommon.model" and
    "pythontools" into "imswitch.imcommon.model.pythontools", with security
    checks. """

    if not isinstance(segment1, str) or not isinstance(segment2, str):
        raise TypeError('Module path segments must be strings')

    if not segment1.endswith('.'):
        segment1 += '.'

    joinedPath = segment1 + segment2
    if ('..' in joinedPath or not joinedPath.startswith(segment1)
            or bool(re.search('[^A-z0-9.]', joinedPath))):
        raise ValueError('Module path segments include ".." or invalid characters')

    return joinedPath
