# Tempesta-v2.0
 
This is a new version of the control software Tempesta from TestaLab (www.testalab.org). The new version uses the same principles and code as before, but making substantial structural changes.

The v2.0 addresses some problems detected from the previous version:

 - Lack of modularity.
 - Difficulty to coordinate between branches and setups.
 - Bugs and errors.
 - Efficiency issues.
 - Difficulty to change code or to implement new modules.
 - GUI and functionality are mixed up.
 - Non-efficent threading.
 
The main characteristics of Tempesta v2.0 are:
- It is based in the Model-View-Controller, a design pattern that separates GUI (view) from functionality (model), and uses an interface to interact with the user (controller). This makes the code modular, efficient and robust.

- Another focus of this version is to use inheritance to separate a general class from different implementations, very useful to create different versions of the same device for different optical setups. 

- The multithreading will be managed in a smarter way than before.
- The code is intuitive to make it easy to understand and new users can easily implement new Widgets without having to understand all the parts of the code.


 
 
