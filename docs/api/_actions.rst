**********************
Global-level functions
**********************

.. method:: getWaitForSignal(self, signal, pollIntervalSeconds=1)

   Returns a function that will wait for the specified signal to emit.
   The returned function will continuously check whether the signal has
   been emitted since its creation. The polling interval defaults to one
   second, and can be customized. 

.. method:: importScript(self, path)

   Imports the script at the specified path (either absolute or
   relative to the main script) and returns it as a module variable. 

