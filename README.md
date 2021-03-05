# ImSwitch
 
This is a new microscope control software based on the older control software tormenta (https://github.com/fedebarabas/tormenta), but re-designed to have a solid architecture that enables change and robust software architecture. It also includes image-reconstruction of RESOLFT and multifoci confocal images but aims at adapting to other microscopy modalities upon demand as well.

ImSwitch addresses some problems detected from the previous software:

 - Lack of modularity.
 - Difficulty to coordinate between branches and setups.
 - Bugs and errors.
 - Efficiency issues.
 - Difficulty to change code or to implement new modules.
 - GUI and functionality are mixed up.
 - Non-efficent threading.
 
The main characteristics of ImSwitch are:
- It is based in the Model-View-Presenter, a design pattern that separates GUI (view) from functionality (model), and uses an interface to interact with the user (controller). This makes the code modular, efficient and robust.
- Another focus of this version is to use inheritance to separate a general class from different implementations, very useful to create different versions of the same device for different optical setups. 
- The multithreading is managed in a smarter way than before.
- The code is intuitive to make it easy to understand and new users can easily implement new Widgets without having to understand all the parts of the code.
