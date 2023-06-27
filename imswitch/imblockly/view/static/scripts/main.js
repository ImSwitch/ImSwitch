var microscope_address = `http://127.0.0.1:8000`
var outputArea = document.getElementById('output');
var stepButton = document.getElementById('stepButton');
var runButton = document.getElementById('runButton');
var ofmConnectButton = document.getElementById('ofmConnectButton');
var myInterpreter = null;
var options = {
    grid: {
        spacing: 25,
        length: 3,
        colour: '#ccc',
        snap: true
    },
    toolbox: toolbox,
    collapse: true,
    comments: true,
    disable: true,
    maxBlocks: Infinity,
    trashcan: true,
    horizontalLayout: (isExtension == true)? true:false,
    toolboxPosition: 'start',
    css: true,
    media: 'https://blockly-demo.appspot.com/static/media/',
    rtl: false,
    scrollbars: true,
    sounds: true,
    renderer: 'thrasos',
    oneBasedIndex: true,
    zoom: {
        controls: true,
        wheel: true,
        startScale: 1,
        maxScale: 3,
        minScale: 0.3,
        scaleSpeed: 1.2
    }
};


var blocklyArea = document.getElementById(`blocklyArea`);
var workspace = Blockly.inject(blocklyArea, options);


/* OpenFlexure Microscope utility functions */
async function pollAction(response) {
    // Poll an action until its status is completed
    // TODO: raise an error if it fails or is cancelled
    // For ease, this accepts and returns a response object from
    // axios.get
    while ((r.data.status == "running") | (r.data.status == "pending")) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        r = await axios.get(r.data.href);
    }
    return r;
}
async function getMicroscopeProperty(property_url) {
    return axios.get(`${microscope_address}/api/v2/${property_url}`)
        .then(r => r.data);
}
async function doMicroscopeAction(action_url, payload) {
    try {
        let r = await axios.get(`${ microscope_address}/${action_url}`, payload);
        await pollAction(r);
        console.log(`Action ${action_url} completed.`);
        return r.data;
    } catch (err) {
        console.log(`Action ${action_url} failed with error ${err}`);
    }
}

function exportBlocks() {
    try {
        var xml = Blockly.Xml.workspaceToDom(workspace);
        var xml_text = Blockly.Xml.domToText(xml);

        var link = document.createElement('a');
        link.download = "openflexure_blockly.xml";
        link.href = "data:application/octet-stream;utf-8," + encodeURIComponent(xml_text);
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (e) {
        window.location.href = "data:application/octet-stream;utf-8," + encodeURIComponent(xml_text);
        alert(e);
    }
}

function importBlocksFile(element) {
    try {
        var file = element.files[0];
        var fr = new FileReader();
        fr.onload = function (event) {
            var xml = Blockly.Xml.textToDom(event.target.result);
            workspace.clear();
            Blockly.Xml.domToWorkspace(xml, workspace);
        };
        fr.readAsText(file);
    } catch (e) {
        alert(e);
    }
}

function clearWorkspace() {
    workspace.clear();
    try {
        javascriptCode.value = `Javascript code...`
    } catch {
        
    }
}


function initApi(interpreter, globalObject) {
    // Add an API function for the alert() block, generated for "text_print" blocks.
    interpreter.setProperty(globalObject, 'alert',
        interpreter.createNativeFunction(function (text) {
            text = arguments.length ? text : '';
            outputArea.value += '\n' + text;
        })
    );

    // Add an API function for the prompt() block.
    var wrapper = function (text) {
        return prompt(text);
    };
    interpreter.setProperty(globalObject, 'prompt',
        interpreter.createNativeFunction(wrapper));

    // Add an API function for highlighting blocks.
    var wrapper = function (id) {
        id = String(id || '');
        return highlightBlock(id);
    };
    interpreter.setProperty(globalObject, 'highlightBlock',
        interpreter.createNativeFunction(wrapper));

    Blockly.JavaScript.addReservedWords('waitForSeconds');

    var wrapper = interpreter.createAsyncFunction(
        function (timeInSeconds, callback) {
            // Delay the call to the callback.
            console.log(`waiting ${timeInSeconds} seconds `);
            setTimeout(() => {
                console.log(`done waiting, completing async action `);
                callback();
            }, timeInSeconds * 1000);
        });
    interpreter.setProperty(globalObject, 'waitForSeconds', wrapper);

    //API functions to interact with the microscope
    Blockly.JavaScript.addReservedWords('getMicroscopeProperty');
    var wrapper = interpreter.createAsyncFunction(
        function (property_url, callback) {
            getMicroscopeProperty(property_url)
                .then(data => JSON.stringify(data))
                .then(callback);
        });
    interpreter.setProperty(globalObject, 'getMicroscopeProperty', wrapper);

    Blockly.JavaScript.addReservedWords('doMicroscopeAction');
    var wrapper = interpreter.createAsyncFunction(
        async (action_url, payload_string, callback) => {
            let data = await doMicroscopeAction(action_url, JSON.parse(payload_string))
            callback(JSON.stringify(data));
        });
    interpreter.setProperty(globalObject, 'doMicroscopeAction', wrapper);
}

var highlightPause = false;
var latestCode = '';

function highlightBlock(id) {
    workspace.highlightBlock(id);
    highlightPause = true;
}

function resetStepUi(clearOutput) {
    workspace.highlightBlock(null);
    highlightPause = false;

    if (clearOutput) {
        outputArea.value = 'Program output...\n=================';
    }
}

function generateCodeAndLoadIntoInterpreter() {
    // Generate JavaScript code and parse it.
    Blockly.JavaScript.STATEMENT_PREFIX = 'highlightBlock(%1);\n';
    Blockly.JavaScript.addReservedWords('highlightBlock');
    latestCode = Blockly.JavaScript.workspaceToCode(workspace);
    resetStepUi(true);
}

function startSteppingCode() {
    // Clear the program output.
    resetStepUi(true);
    console.log(latestCode)
    runButton.disabled=true
    myInterpreter = new Interpreter(latestCode, initApi);
    
    // And then show generated code in an alert.
    // In a timeout to allow the outputArea.value to reset first.
    setTimeout(function () {
        try {
            javascriptCode.value = latestCode;
        } catch (err) {
            
        }
        highlightPause = true;
        stepCode();
    }, 1);
    return;
}

function stepCode() {
    stepButton.disabled = true;
    if (!myInterpreter) return startSteppingCode();
    highlightPause = false;

    try {
        
        var hasMoreCode = myInterpreter.step();
        stepButton.disabled = false;
    } finally {
        if (!hasMoreCode) return stopSteppingCode();
    }
    if (hasMoreCode && !highlightPause) setTimeout(stepCode, 0)
}

function stopSteppingCode() {
    {
        // Program complete, no more code to execute.
        outputArea.value += '\n\n<< Program complete >>';

        myInterpreter = null;
        resetStepUi(false);

        // Cool down, to discourage accidentally restarting the program.
        stepButton.disabled = true;
        setTimeout(function () {
            stepButton.disabled = false;
            runButton.disabled = false;
        }, 2000);

        return;
    }
}

var runner = null;

function resetInterpreter() {
    myInterpreter = null;
    if (runner) {
        clearTimeout(runner);
        runner = null;
    }
}

function runCode() {
    if (!myInterpreter) {
        runButton.disabled = true;
        stepButton.disabled = true;
        // First statement of this code.
        // Clear the program output.
        resetStepUi(true);

        // And then show generated code in an alert.
        // In a timeout to allow the outputArea.value to reset first.
        setTimeout(function () {
            try {
                javascriptCode.value = latestCode;
            } catch (err) {
                
            }
            //alert('Ready to execute the following code\n' +
            // '===================================\n' +
            // latestCode);

            // Begin execution
            highlightPause = false;
            myInterpreter = new Interpreter(latestCode, initApi);
            runner = function () {
                if (myInterpreter) {
                    var hasMore = myInterpreter.run();
                    if (hasMore) {
                        // Execution is currently blocked by some async call.
                        // Try again later.
                        setTimeout(runner, 10);
                    } else {
                        // Program is complete.
                        outputArea.value += '\n\n<< Program complete >>';
                        runButton.disabled = false;
                        stepButton.disabled = false;
                        resetInterpreter();
                        resetStepUi(false);
                    }
                }
            };
            runner();
        }, 1);
        return;
    }
}

// Load the interpreter now, and upon future changes.
generateCodeAndLoadIntoInterpreter();
workspace.addChangeListener(function (event) {
    if (!event.isUiEvent) {
        // Something changed. Parser needs to be reloaded.
        console.log("Updating code")
        resetInterpreter();
        generateCodeAndLoadIntoInterpreter();
    }
});

function handleConnect() {
    var livePreviewImg = document.getElementById("livePreviewImg")
    runButton.disabled = false;
    stepButton.disabled = false;
    stepButton.disabled = false;
    //livePreviewImg.src = `${microscope_address}/api/v2/streams/mjpeg`
}

if (location.protocol === 'https:') {
    alert(`This page was loaded with 'https' and so will not be able to connect to the openUC2 Microscope.  Please make sure you connect with 'http'.`)
}

function openWebApp() {
    window.open(`${microscope_address}/api/v2/extensions/org.openflexure.blockly/static/index.html`);
}

function microscopeTest() {

}

document.addEventListener("DOMContentLoaded", function () {
    microscopeTest();
    try {
        javascriptCode.value = `Javascript code...`;
    } catch(err){

    }

    outputArea.value = `Program output...`
});
