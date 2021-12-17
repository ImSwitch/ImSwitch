"""
Created on Tue Oct 12 15:05:00 2021

@author: jacopoabramo
"""


from .MultiManager import MultiManager


from imswitch.imcommon.model import initLogger
import sys
import io

from labthings import Server
from labthings import ActionView, PropertyView, create_app, fields, find_component, op
from labthings.example_components import PretendSpectrometer
from labthings.json import encode_json

class LabThingManager(MultiManager):
    def __init__(self, setupInfo):
        super().__init__()
        self.start_labthing()

    

    def start_labthing(self):
        
        # Create LabThings Flask app
        app, labthing = create_app(
            __name__,
            title="My Lab Device API",
            description="Test LabThing-based API",
            version="0.1.0",
        )

        # Attach an instance of our component
        # Usually a Python object controlling some piece of hardware
        my_spectrometer = PretendSpectrometer()
        labthing.add_component(my_spectrometer, "org.labthings.example.mycomponent")


        # Add routes for the API views we created
        labthing.add_view(DenoiseProperty, "/integration_time")
        labthing.add_view(QuickDataProperty, "/quick-data")
        labthing.add_view(MeasurementAction, "/actions/measure")

        Server(app).run()



# Wrap in a semantic annotation to automatically set schema and args
class DenoiseProperty(PropertyView):
    """Value of integration_time"""

    schema = fields.Int(required=True, minimum=100, maximum=500)
    semtype = "LevelProperty"

    @op.readproperty
    def get(self):
        # When a GET request is made, we'll find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        return my_component.integration_time

    @op.writeproperty
    def put(self, new_property_value):
        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")

        # Apply the new value
        my_component.integration_time = new_property_value

        return my_component.integration_time


"""
Create a view to quickly get some noisy data, and register is as a Thing property
"""


class QuickDataProperty(PropertyView):
    """Show the current data value"""

    # Marshal the response as a list of floats
    schema = fields.List(fields.Float())

    @op.readproperty
    def get(self):
        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")
        return my_component.data



"""
Create a view to start an averaged measurement, and register is as a Thing action
"""


class MeasurementAction(ActionView):
    # Expect JSON parameters in the request body.
    # Pass to post function as dictionary argument.
    args = {
        "averages": fields.Integer(
            missing=20, example=20, description="Number of data sets to average over",
        )
    }
    # Marshal the response as a list of numbers
    schema = fields.List(fields.Number)

    # Main function to handle POST requests
    @op.invokeaction
    def post(self, args):
        """Start an averaged measurement"""

        # Find our attached component
        my_component = find_component("org.labthings.example.mycomponent")

        # Get arguments and start a background task
        n_averages = args.get("averages")

        # Return the task information
        return my_component.average_data(n_averages)

