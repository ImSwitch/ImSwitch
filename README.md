# ImSwitch

[![DOI](https://joss.theoj.org/papers/10.21105/joss.03394/status.svg)](https://doi.org/10.21105/joss.03394)
![image-sc-badge](https://img.shields.io/badge/image.sc-community_partner-pink.svg?logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAABgAAAAXCAYAAAARIY8tAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAVgSURBVEhLfZV5TFRHHMe%2F897u211guUREQCH1AqEoEvBqgtqiiWc9QNTYJm2a9LBBrRLTNFH%2FaCqpV9DURJuaNlVrrUlLsNo0ajXWemIDiiBYOZVjF3bZe5f3pvPmPdai1k%2By2fl95%2FjN%2FH6%2FmUfwfxz5ZZQg4AZARuvKi6G0VmmvKcDOnYquDOM5B1s%2B%2FnUcE1P3TQlShQiXdPmllHR1Jx2807iAebuV8NOeel3mDHNQVnYxVoKnkcmJLVHKg9Ov0ImqbmRHSTRLfIwKZb8unx9QKIp6%2BvBNTX27ROkYCtoSCLiyUqoPe7WRgKD%2Fc4zUs01dXGsTvrjK%2BvGpaCstGvYrNRnxw827%2BP72PaiLq%2BMISLpFitnMJ%2BmEHfDQEGzUzWFI7ARDUI8Pvu%2Bqsb%2FqD8y19evqU2QoW93FW5J0c8gBJURQKtgeTKqVmZWI3LwU3hOGhSN4uQbOsi%2Fhr7oEMihzmURFIOKtxZDys7gtEBIdkLGLGwzuYOuG6tcoJcvVttlsQHFpDmbOHquaYYK36%2BGuPAHF4dIEUYRpXgFiD5TDvLQQEe8sY9sz8i5K6LqelZtz1bawfftFAxXIXhYe7mzuG%2BMQZX2aUJWbNgeOubyQ2aAhIt9fBX%2FJIvhFbawwMg7mJYW8zXJhECnZx4qBiPlTitcSQjaoHfEjIrB2%2FVQIAkE7i%2FXRpnY%2B4YnXjyqHG6MDQUxxurnW4aL46oId16%2B2wWKRkJwSDSMrhsB5dnUCIbY0SfdmTq8TmLvP%2BQyGURLhdLLyY5hZCJ5l18R0uAwGKGzSb30WKCwvXm8Ip3%2BsQ%2BWeP%2FHP7Vaeq6eIO8RZM9atYQfnGfW4g7j2VxtkmaIgIxFJEWYM1NqRwjad6iEYMAgnMlzOxkFqnXzLyiszjMsVQE19P%2FoVA5KDA6x0ZfWSnSF7Np20jHS5zj6wjCwMCAZ9OBAbZ8HYtFjU%2Fv1Eswd9nlluV0K%2F4o6si0l57BZNPPi5ecl49LAPDod2chV18QnennOPUqKXiceT049N9NsW5Xi74GMJ6zVGsiEEfv8guru0eKupXW6%2FJ92P9U4qz5nwZo9ZzG6LouiKF5ExZww%2BWJKjlic62p08bDIR0CtZx4d8xnnEvuKTBpaQSepCQqwVjnfXoPpaL9paHarEGe%2B3YZWtDk6jAdML82GXtHIc4u6KOchkc%2B02L44cuoE%2Bu%2F5SUNogsOLcoVkMtou0aWn4qGwmStbmIDraxO%2FFgoQA744JDaK8iSXyGbz6pYuINCIQGORtBqUU28SKrNT7Hhozn9VuKvUHWDgIjDkTeNnNmJ3GL5zV50GoronPynZ58OrC2WhmoejxB7n23qQ0JLOC%2BP1cM5oabVxjD9%2BF3ZWLPxPIqVOyIJPNTOHb8J%2B5DIVdLBWxrx%2FKwePwHj%2FLbRUj21ZpnBVT42N0RUMNy5XLj3ibFWoQVFYfPcqLvaLhaqc3Y%2BZkduGyISuQO3uhdPbAw54GuaNbHcIRRsUj8sMSSLkZ%2BLm1C7X9A1zP7KZouv4Ytt5w7I%2Furlz6tdrkzwOrEipKhm0saLzWQnca4Dt9HpTFXIWyb4Fl9XzE7N8KqSCba%2F%2Bl5mYnmh%2FYNYNSh5EKn2qG7kAl7mRFC3ukdusmR2Geq5ISsHFlESzFRSCsiobwyVpin4MIu744sLBXt3iJh7Gt2x5NfO5GVk1JAwax9e28rLQrI2L5oJhnStMZDPEvm8rqZuFeqpew95o%2BjHBEZu%2F8dm741g1zoGJfWZ6lQMnNe33G1Q6T9FCXX4oQUvI3NZgscsDfsvfQcu2F1HnOQZijF82CPHCDnSZDV14MpW2KyTgN6xdqGR8G8C9BoRdv%2F1UFDQAAAABJRU5ErkJggg%3D%3D)



``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) to provide a solution for flexible control of multiple microscope modalities.

## Statement of need

The constant development of novel microscopy methods with an increased number of dedicated
hardware devices poses significant challenges to software development.
ImSwitch is designed to be compatible with many different microscope modalities and customizable to the
specific design of individual custom-built microscopes, all while using the same software. We
would like to involve the community in further developing ImSwitch in this direction, believing
that it is possible to integrate current state-of-the-art solutions into one unified software.

## Installation

### Option A: Standalone bundles for Windows

Windows users can download ImSwitch in standalone format from the [releases page on GitHub](https://github.com/kasasxav/ImSwitch/releases). Further information is available there. An existing Python installation is *not* required.

### Option B: Install using pip

ImSwitch is also published on PyPI and can be installed using pip. Python 3.7 or later is required. Additionally, certain components (the image reconstruction module and support for TIS cameras) require the software to be running on Windows, but most of the functionality is available on other operating systems as well.

To install ImSwitch from PyPI, run the following command:

```
pip install ImSwitch
```

You will then be able to start ImSwitch with this command:

```
imswitch
```
(Developers installing ImSwitch from the source repository should run `pip install -r requirements-dev.txt` instead, and start it using ``python -m imswitch``)

## Documentation

Further documentation is available at [imswitch.readthedocs.io](https://imswitch.readthedocs.io).

## Testing

ImSwitch has automated testing through GitHub Actions, including UI and unit tests. It is also possible to manually inspect and test the software without any device since it contains mockers that are automatically initialized if the instrumentation specified in the config file is not detected.

## Contributing

Read the [contributing section](https://imswitch.readthedocs.io/en/latest/contributing.html) in the documentation if you want to help us improve and further develop ImSwitch!
