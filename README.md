# ImSwitch
``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) to provide a solution for flexible control of multiple microscope modalities.

## Statement of need

The constant development of novel microscopy methods with an increased number of dedicated
hardware devices poses significant challenges to software development. 
ImSwitch is designed to be compatible with many different microscope modalities and customizable to the
specific design of individual custom-built microscopes, all while using the same software. We
would like to involve the community in further developing ImSwitch in this direction, believing
that it is possible to integrate current state-of-the-art solutions into one unified software.

## Requirements and installation

To run ImSwitch, you must have Python 3.7 or later as well as the required Python packages installed. Additionally, certain components (the image reconstruction module and support for TIS cameras) require the software to be running on Windows.

Install ImSwitch by running this command in the root directory of the repository:

```
pip install .
```

You will then be able to start ImSwitch with this command:

```
imswitch
```

## Documentation and testing

* ImSwitch has automated testing through GitHub Actions, including UI and unit tests. It is also possible to manually inspect and test the software without any device since it contains mockers that are automatically initialized if the instrumentation specified in the config file is not detected.

* It is possible to implement, import and test user-defined scripts in the scripting module. 

* Further documentation is available at [imswitch.readthedocs.io](https://imswitch.readthedocs.io).

## Contributing

Read the [contributing section](https://imswitch.readthedocs.io/en/latest/contributing.html) in the documentation if you want to help us improve and further develop ImSwitch!
