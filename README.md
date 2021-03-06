# ImSwitch
 
ImSwitch is a microscope control software that focuses in providing a stable and functional code to work with scanning-based microscopes, this includes confocal and targetted-switching super-resolution microscopes (STED, RESOLFT, MINFLUX). It also includes image-reconstruction of our RESOLFT parallelized systems and multifoci confocal images but aims at adapting to other microscopy modalities upon demand as well. ImSwitch has the ambition to work towards microscope automation by first providing a layered architecture that will later enable scripting within the software.

ImSwitch is inspired by Tormenta (https://github.com/fedebarabas/tormenta) and its later version Tempesta (https://github.com/TestaLab/Tempesta), both softwares have been a solid tool in microscopy labs and have grown based on feedback of users and developers during years (GPL of Tormenta 2017). ImSwitch comes with a different architecture and more support for polymorphism, which makes the software general enough to be able to be implemented in different microscopy modalities. 

ImSwitch addresses some problems detected from other custom-made softwares:

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
