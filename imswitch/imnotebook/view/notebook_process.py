
import os
import subprocess
import threading
import signal
import time

from .logger import log

_process = None
_monitor = None
_webaddr = None


def testnotebook(notebook_executable="jupyter-notebook"):
    return 0 == os.system("%s --version" % notebook_executable)


def startnotebook(notebook_executable="jupyter-notebook", port=8888, directory='',
                  configfile=os.path.join(os.path.dirname(__file__), 'jupyterqt_notebook_config.py')):
    global _process, _monitor, _webaddr
    if _process is not None:
        raise ValueError("Cannot start notebook: one is already running in this module")
    log("Starting Jupyter notebook process")
    # it is necessary to redirect all 3 outputs or .app does not open
    notebookp = subprocess.Popen([notebook_executable,
                            "--port=%s" % port,
                            "--config=\"%s\"" % configfile,
                            "--notebook-dir=%s" % directory], bufsize=1,
                            stderr=subprocess.PIPE)

    log("Waiting for server to start...")
    webaddr = None
    while webaddr is None:
        line = notebookp.stderr.readline().decode('utf-8').strip()
        log(line)
        if "http://" in line:
            start = line.find("http://")
            # end = line.find("/", start+len("http://")) new notebook
            # needs a token which is at the end of the line
            webaddr = line[start:]
    log("Server found at %s, migrating monitoring to listener thread" % webaddr)

    # pass monitoring over to child thread
    def process_thread_pipe(process):
        while process.poll() is None:  # while process is still alive
            log(process.stderr.readline().decode('utf-8').strip())
    notebookmonitor = threading.Thread(name="Notebook Monitor", target=process_thread_pipe,
                                       args=(notebookp,), daemon=True)
    notebookmonitor.start()
    _process = notebookp
    _monitor = notebookmonitor
    _webaddr = webaddr
    return webaddr


def stopnotebook():
    global _process, _monitor, _webaddr
    if _process is None:
        return
    log("Sending interrupt signal to jupyter-notebook")
    _process.send_signal(signal.SIGINT)
    try:
        log("Waiting for jupyter to exit...")
        time.sleep(1)
        _process.send_signal(signal.SIGINT)
        _process.wait(10)
        log("Final output:")
        log(_process.communicate())

    except subprocess.TimeoutExpired:
        log("control c timed out, killing")
        _process.kill()

    _process = None
    _monitor = None
    _webaddr = None

