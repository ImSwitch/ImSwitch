********************
Module Configuration
********************

ImSwitch consists of multiple different modules:

+----------------------+-------------------+
| Name                 | ID                |
+======================+===================+
| Hardware Control     | ``imcontrol``     |
+----------------------+-------------------+
| Image Reconstruction | ``imreconstruct`` |
+----------------------+-------------------+
| Scripting            | ``imscripting``   |
+----------------------+-------------------+

The list of enabled modules is defined in the /config/modules.json file. This file is automatically
created the first time the program starts, but it is also possible to create or modify it manually
according to this template:

.. code-block:: json

   {
       "ID_of_module_1",
       "ID_of_module_2",
       ...
   }

Modules that are not enabled will not show up in the program. By default, the hardware control and
scripting modules are enabled.
