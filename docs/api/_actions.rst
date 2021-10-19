**********************
Global-level functions
**********************

.. method:: getLogger(self) -> logging.LoggerAdapter

   Returns a logger instance that can be used to print formatted
   messages to the console. 

.. method:: getScriptDirPath(self) -> str

   Returns the path to the directory containing the running script.
   

.. method:: getWaitForSignal(self, signal: imswitch.imcommon.framework.qt.Signal, pollIntervalSeconds: float = 1.0) -> Callable[[], NoneType]

   Returns a function that will wait for the specified signal to emit.
   The returned function will continuously check whether the signal has
   been emitted since its creation. The polling interval defaults to one
   second, and can be customized. 

.. method:: importScript(self, path: str) -> Any

   Imports the script at the specified path (either absolute or
   relative to the main script) and returns it as a module variable. 

