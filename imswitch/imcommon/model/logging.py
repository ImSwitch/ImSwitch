import inspect
import logging
import weakref

import coloredlogs


baseLogger = logging.getLogger('imswitch')
coloredlogs.install(level='DEBUG', logger=baseLogger,
                    fmt='%(asctime)s %(levelname)s %(message)s')
objLoggers = {}


class LoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger, prefixes, objRef):
        super().__init__(logger, {})
        self.prefixes = prefixes
        self.objRef = objRef

    def process(self, msg, kwargs):
        processedPrefixes = []
        for prefix in self.prefixes:
            if callable(prefix):
                try:
                    processedPrefixes.append(prefix(self.objRef()))
                except Exception:
                    pass
            else:
                processedPrefixes.append(prefix)

        processedMsg = f'[{" -> ".join(processedPrefixes)}] {msg}'
        return processedMsg, kwargs


def initLogger(obj, *, instanceName=None, tryInheritParent=False):
    """ Initializes a logger for the specified object. obj should be either a
    class, object or string. """

    logger = None
    tryInheritParent = False # FIXME: Bypass why?! 
    if tryInheritParent:
        # Use logger from first parent in stack that has one
        for frameInfo in inspect.stack():
            frameLocals = frameInfo[0].f_locals
            if 'self' not in frameLocals:
                continue

            parent = frameLocals['self']
            parentRef = weakref.ref(parent)
            if parentRef not in objLoggers:
                continue

            logger = objLoggers[parentRef]
            break

    if logger is None:
        # Create logger
        if inspect.isclass(obj):
            objName = obj.__name__
            objRef = weakref.ref(obj)
        elif isinstance(obj, str):
            objName = obj
            objRef = None
        else:
            objName = obj.__class__.__name__
            objRef = weakref.ref(obj)

        logger = LoggerAdapter(baseLogger,
                               [objName, instanceName] if instanceName else [objName],
                               objRef)

        # Save logger so it can be used by tryInheritParent requesters later
        if objRef is not None:
            objLoggers[objRef] = logger

    return logger
