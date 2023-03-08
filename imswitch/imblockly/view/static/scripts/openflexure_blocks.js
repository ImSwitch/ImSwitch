Blockly.defineBlocksWithJsonArray([{
  "type": "capture",
  "message0": "capture image",
  "previousStatement": null,
  "nextStatement": null,
  "colour": "#24c56c",
  "tooltip": "Capture an image.",
  "helpUrl": ""
},
{
  "type": "get_position",
  "message0": "%1",
  "args0": [
    {
      "type": "field_dropdown",
      "name": "axis_name",
      "options": [
        [
          "x position",
          "x"
        ],
        [
          "y position",
          "y"
        ],
        [
          "z position",
          "z"
        ]
      ]
    }
  ],
  "output": "Number",
  "colour": "#24c56c",
  "tooltip": "Get the current position of the stage.",
  "helpUrl": ""
},

{
  "type": "autofocus",
  "message0": "run %1",
  "args0": [
    {
      "type": "field_dropdown",
      "name": "autofocus_type",
      "options": [
        [
          "fast autofocus", "fast_autofocus"
        ],
        [
          "medium autofocus", "medium_autofocus"
        ],
        [
          "fine autofocus", "fine_autofocus"
        ]
      ]
    }
  ],
  "previousStatement": null,
  "nextStatement": null,
  "colour": "#24c56c",
  "tooltip": "Run the built-in autofocus.",
  "helpUrl": ""
},
{
  "type": "get_sharpness_metric",
  "message0": "sharpness metric",
  "output": "Number",
  "colour": "#24c56c",
  "tooltip": "Get the sharpness metric of the current field of view.",
  "helpUrl": ""
},
{
  "type": "wait_seconds",
  "message0": " wait %1 seconds",
  "args0": [{
    "type": "field_number",
    "name": "SECONDS",
    "min": 0,
    "max": 600,
    "value": 1
  }],
  "previousStatement": null,
  "nextStatement": null,
  "colour": "%{BKY_LOOPS_HUE}"
},
{
  "type": "move_stage_3d",
  "message0": "%1 %2 x %3 y %4 z %5",
  "args0": [
    {
      "type": "field_dropdown",
      "name": "abs_or_rel",
      "options": [
        [
          "move by",
          "RELATIVE"
        ],
        [
          "move to",
          "ABSOLUTE"
        ]
      ]
    },
    {
      "type": "input_dummy"
    },
    {
      "type": "input_value",
      "name": "x_steps",
      "check": "Number",
      "align": "RIGHT"
    },
    {
      "type": "input_value",
      "name": "y_steps",
      "check": "Number",
      "align": "RIGHT"
    },
    {
      "type": "input_value",
      "name": "z_steps",
      "check": "Number",
      "align": "RIGHT"
    }
  ],
  "inputsInline": false,
  "previousStatement": null,
  "nextStatement": null,
  "colour": "#24c56c",
  "tooltip": "Move the stage in three dimensions.",
  "helpUrl": ""
},
{
  "type": "move_stage",
  "message0": "%1 %2 %3 %4 %5",
  "args0": [
    {
      "type": "field_dropdown",
      "name": "axis_name",
      "options": [
        [
          "move x",
          "X"
        ],
        [
          "move y",
          "Y"
        ],
        [
          "move z",
          "Z"
        ]
      ]
    },
    {
      "type": "input_dummy"
    },
    {
      "type": "field_dropdown",
      "name": "abs_or_rel",
      "options": [
        [
          "by",
          "RELATIVE"
        ],
        [
          "to",
          "ABSOLUTE"
        ]
      ]
    },
    {
      "type": "input_dummy"
    },
    {
      "type": "input_value",
      "name": "steps",
      "check": "Number"
    }
  ],
  "inputsInline": true,
  "previousStatement": null,
  "nextStatement": null,
  "colour": "#24c56c",
  "tooltip": "Move the stage.",
  "helpUrl": ""
}
]);

Blockly.JavaScript['capture'] = function (block) {
  var code = `doMicroscopeAction("CommunicationChannel/acquireImage", "{}");\n`
  return code;
};



Blockly.JavaScript['move_relative'] = function (block) {
  var value_x_steps = Blockly.JavaScript.valueToCode(block, 'x_steps', Blockly.JavaScript.ORDER_ATOMIC);
  var value_y_steps = Blockly.JavaScript.valueToCode(block, 'y_steps', Blockly.JavaScript.ORDER_ATOMIC);
  var value_z_steps = Blockly.JavaScript.valueToCode(block, 'z_steps', Blockly.JavaScript.ORDER_ATOMIC);
  var payload = `"{\\"isAbsolute\\": false, \\"axis\\": "X", \\"dist\\": ${value_x_steps}}"`

  var code = `doMicroscopeAction("PositionerController/movePositioner?positionerName=ESP32Stage&axis=X&dist=1000", ${payload});\n`;
  return code;
};

Blockly.JavaScript['autofocus'] = function (block) {
  // three autofocus options. Fast, Medium and fine match the settings in Openflexure server V2.10 webApp 
  var dropdown_autofocus_type = block.getFieldValue('autofocus_type');
  switch (dropdown_autofocus_type) {
    case 'fast_autofocus':
      var autofocus_command = 'fast_autofocus';
      var payload = '\\"dz\\": 2000'
      break;
    case 'medium_autofocus':
      var autofocus_command = 'autofocus';
      var payload = '\\"dz\\": [-90, -60, -30, 0, 30, 60, 90]'
      break;
    case 'fine_autofocus':
      var autofocus_command = 'autofocus';
      var payload = '\\"dz\\": [-30, -20, -10, 0, 10, 20, 30]'
      break;
    default:
      var autofocus_command = 'fast_autofocus';
      var payload = '\\"dz\\": 2000'
        ;
  }
  var code = `doMicroscopeAction("extensions/org.openflexure.autofocus/${autofocus_command}", "{ ${payload} }");\n`;
  return code;
};

Blockly.JavaScript['get_sharpness_metric'] = function (block) {
  var code = `JSON.parse(doMicroscopeAction("extensions/org.openflexure.autofocus/measure_sharpness", "{}")).sharpness`;
  return [code, Blockly.JavaScript.ORDER_ATOMIC];
};


Blockly.JavaScript['wait_seconds'] = function (block) {
  var seconds = Number(block.getFieldValue('SECONDS'));
  var code = `waitForSeconds(${seconds});\n`;
  return code;
};

Blockly.JavaScript['get_position'] = function (block) {
  var dropdown_axis_name = block.getFieldValue('axis_name');
  code = `JSON.parse(getMicroscopeProperty(\"instrument/state/stage/position\")).${dropdown_axis_name}`;
  return [code, Blockly.JavaScript.ORDER_ATOMIC];
};

Blockly.JavaScript['move_stage_3d'] = function (block) {
  var dropdown_abs_or_rel = block.getFieldValue('abs_or_rel');
  var value_x_steps = Blockly.JavaScript.valueToCode(block, 'x_steps', Blockly.JavaScript.ORDER_ATOMIC) || 0;
  var value_y_steps = Blockly.JavaScript.valueToCode(block, 'y_steps', Blockly.JavaScript.ORDER_ATOMIC) || 0;
  var value_z_steps = Blockly.JavaScript.valueToCode(block, 'z_steps', Blockly.JavaScript.ORDER_ATOMIC) || 0;

  var code = (
    `var x_steps = ${value_x_steps};\n` +
    `var y_steps = ${value_y_steps};\n` +
    `var z_steps = ${value_z_steps};\n` +
    `doMicroscopeAction("actions/stage/move", JSON.stringify({"absolute": ${dropdown_abs_or_rel == "ABSOLUTE" ? true : false}, "x": x_steps, "y": y_steps, "z": z_steps} ));\n`
  );

  return code;
};

Blockly.JavaScript['move_stage'] = function (block) {
  var dropdown_axis_name = block.getFieldValue('axis_name');
  var dropdown_abs_or_rel = block.getFieldValue('abs_or_rel');
  var value_steps = Blockly.JavaScript.valueToCode(block, 'steps', Blockly.JavaScript.ORDER_ATOMIC) || 0;
  let axis_name = dropdown_axis_name[0].toUpperCase();

  var code = `doMicroscopeAction("PositionerController/movePositioner?positionerName=ESP32Stage&axis=${axis_name}&dist=${value_steps}&isAbsolute=${dropdown_abs_or_rel == "ABSOLUTE" ? true : false}",0);\n`; //", ${payload}

  /*var code = (
    `var steps = ${value_steps};\n` +
    `doMicroscopeAction("actions/stage/move", JSON.stringify({"absolute": ${dropdown_abs_or_rel == "ABSOLUTE" ? true : false}, "${axis_name}": steps}));\n`
  );*/
  return code;
};
