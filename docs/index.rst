********
ImSwitch
********

``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) design pattern and enabling flexible control of multiple microscope modalities.

The constant development of novel microscopy methods with an increased number of dedicated
hardware devices poses significant challenges to software development. 
ImSwitch is designed to be compatible with many different microscope modalities and customizable to the
specific design of individual custom-built microscopes, all while using the same software. We
would like to involve the community in further developing ImSwitch in this direction, believing
that it is possible to integrate current state-of-the-art solutions into one unified software.

In this documentation page you will find all information you need about the installation, usage and development of ImSwitch,
both from the user perspective (GUI description and use cases) as
well as for developers (scripting and API modules, and hardware control and JSON config files).

.. toctree::
    :hidden:
    :caption: Software info

    installation
    changelog
    contributing

.. toctree::
    :hidden:
    :caption: Usage

    gui
    use-cases
    scripting

.. toctree::
    :hidden:
    :caption: Internals and specifications

    Hdf5datafile
    modules
    imcontrol-setups

.. toctree::
    :hidden:
    :caption: Extending ImSwitch

    adding-device-support
    low-level-managers

.. toctree::
    :glob:
    :hidden:
    :caption: Scripting API reference

    api/*
