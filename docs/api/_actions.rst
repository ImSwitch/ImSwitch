.. role:: raw-html-m2r(raw)
   :format: html


class **_actions** (builtins.object)  
------------------------------------------

These functions are available at the global level.  

Methods defined here:  

**getWaitForSignal** (self, signal, pollIntervalSeconds=1)

Returns a function that will wait for the specified signal to emit.\ :raw-html-m2r:`<br>`
The returned function will continuously check whether the signal has\ :raw-html-m2r:`<br>`
been emitted since its creation. The polling interval defaults to one\ :raw-html-m2r:`<br>`
second, and can be customized.

**importScript** (self, path)

Imports the script at the specified path (either absolute or\ :raw-html-m2r:`<br>`
relative to the main script) and returns it as a module variable.

----

Data descriptors defined here:  

**\ **dict**\ **

dictionary for instance variables (if defined)

**\ **weakref**\ **

list of weak references to the object (if defined)
