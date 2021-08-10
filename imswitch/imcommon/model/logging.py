import inspect
import logging
import weakref

import coloredlogs


loggerRefs = {}


class LoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger, prefixes, instanceRef):
        super().__init__(logger, {})
        self.prefixes = prefixes
        self.instanceRef = instanceRef

    def process(self, msg, kwargs):
        processedPrefixes = []
        for prefix in self.prefixes:
            if callable(prefix):
                try:
                    processedPrefixes.append(prefix(self.instanceRef()))
                except Exception:
                    pass
            else:
                processedPrefixes.append(prefix)

        return f'[{" -> ".join(processedPrefixes)}] {msg}', kwargs


def initLogger(obj, moduleName, *, instanceName=None, tryInheritParent=False):
    """ Initializes a logger for the specified object. moduleName should always
    be __name__. """

    logger = None

    if tryInheritParent:
        # Use logger from first parent in stack that has one
        for frameInfo in inspect.stack():
            frameLocals = frameInfo[0].f_locals
            if 'self' not in frameLocals:
                continue

            parent = frameLocals['self']
            parentRef = weakref.ref(parent)
            if parentRef not in loggerRefs:
                continue

            logger = loggerRefs[parentRef]
            break

    if logger is None:
        # Create logger
        if inspect.isclass(obj):
            cls = obj
        else:
            cls = obj.__class__

        objRef = weakref.ref(obj)
        logger = LoggerAdapter(logging.getLogger(moduleName),
                               [cls.__name__, instanceName] if instanceName else [cls.__name__],
                               objRef)

        # Install coloredlogs
        coloredlogs.install(level='DEBUG', logger=logger.logger,
                            fmt='%(asctime)s %(levelname)s %(message)s')

        # Save logger so it can be used by tryInheritParent requesters later
        loggerRefs[objRef] = logger

    return logger
