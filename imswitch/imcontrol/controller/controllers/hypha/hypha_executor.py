

import sys
import io
import contextlib
import ast
import traceback
import array
import wave
import asyncio


import base64
from functools import partial

class OutputRecorder:
    def __init__(self):
        self.outputs = []

    def write(self, type, content):
        self.outputs.append({"type": type, "content": content})
    
    def show(self, type, content, attrs={}):
        self.outputs.append({"type": type, "content": content, "attrs": attrs})


# For redirecting stdout and stderr later.
class JSOutWriter(io.TextIOBase):
    def __init__(self, recorder):
        self._recorder = recorder

    def write(self, s):
        return self._recorder.write("stdout", s)

class JSErrWriter(io.TextIOBase):
    def __init__(self, recorder):
        self._recorder = recorder

    def write(self, s):
        return self._recorder.write("stderr", s)

def setup_matplotlib(output_recorder, store):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    def show():
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        # img = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('utf-8')
        # output_recorder.show("img", img)
        file_id = store.put('file', buf.getvalue(), 'plot.png')
        output_recorder.show("img", store.get_url(file_id))
        plt.clf()

    plt.show = show

def show_image(output_recorder, store, image, **attrs):
    from PIL import Image
    if not isinstance(image, Image.Image):
        image = Image.fromarray(image)
    buf = io.BytesIO()
    image.save(buf, format='png')
    # data = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('utf-8')
    file_id = store.put('file', buf.getvalue(), 'plot.png')
    output_recorder.show("img", store.get_url(file_id))


def show_animation(output_recorder, store, frames, duration=100, format="apng", loop=0, **attrs):
    from PIL import Image
    buf = io.BytesIO()
    img, *imgs = [frame if isinstance(frame, Image.Image) else Image.fromarray(frame) for frame in frames]
    img.save(buf, format='png' if format == "apng" else format, save_all=True, append_images=imgs, duration=duration, loop=0)
    # img = f'data:image/{format};base64,' + base64.b64encode(buf.getvalue()).decode('utf-8')
    # output_recorder.show("img", img, attrs)
    file_id = store.put('file', buf.getvalue(), 'plot.png')
    output_recorder.show("img", store.get_url(file_id))

def convert_audio(data):
    try:
        import numpy as np
        is_numpy = isinstance(data, np.ndarray)
    except ImportError:
        is_numpy = False
    if is_numpy:
        if len(data.shape) == 1:
            channels = 1
        if len(data.shape) == 2:
            channels = data.shape[0]
            data = data.T.ravel()
        else:
            raise ValueError("Too many dimensions (expected 1 or 2).")
        return ((data * (2**15 - 1)).astype("<h").tobytes(), channels)
    else:
        data = array.array('h', (int(x * (2**15 - 1)) for x in data))
        if sys.byteorder == 'big':
            data.byteswap()
        return (data.tobytes(), 1)

def show_audio(output_recorder, store, samples, rate):
    bytes, channels = convert_audio(samples)
    buf = io.BytesIO()
    with wave.open(buf, mode='wb') as w:
        w.setnchannels(channels)
        w.setframerate(rate)
        w.setsampwidth(2)
        w.setcomptype('NONE', 'NONE')
        w.writeframes(bytes)
    # audio = 'data:audio/wav;base64,' + base64.b64encode(buf.getvalue()).decode('utf-8')
    # output_recorder.show("audio", audio)
    file_id = store.put('file', buf.getvalue(), 'audio.wav')
    output_recorder.show("audio", store.get_url(file_id))



def preprocess_code(source):
    """Parse the source code and separate it into main code and last expression."""
    parsed_ast = ast.parse(source)
    
    last_node = parsed_ast.body[-1] if parsed_ast.body else None
    
    if isinstance(last_node, ast.Expr):
        # Separate the AST into main body and last expression
        main_body_ast = ast.Module(body=parsed_ast.body[:-1], type_ignores=parsed_ast.type_ignores)
        last_expr_ast = last_node
        
        # Convert main body AST back to source code for exec
        main_body_code = ast.unparse(main_body_ast)
        
        return main_body_code, last_expr_ast
    else:
        # If the last node is not an expression, treat the entire code as the main body
        return source, None
    

async def execute_code(store, source, context):
    # HACK: Prevent 'wave' import from failing because audioop is not included with pyodide.
    import types
    embed = types.ModuleType('embed')
    sys.modules['embed'] = embed
    output_recorder = OutputRecorder()

    embed.image = partial(show_image, output_recorder, store)
    embed.animation = partial(show_animation, output_recorder, store)
    embed.audio = partial(show_audio, output_recorder, store)

    out = JSOutWriter(output_recorder)
    err = JSErrWriter(output_recorder)
   
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            setup_matplotlib(output_recorder, store)
            source, last_expression = preprocess_code(source)
            code = compile(source, "<string>", "exec", ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

            result = eval(code, context)
            if result is not None:
                result = await result
            if last_expression:
                if isinstance(last_expression.value, ast.Await):
                    # If last expression is an await, compile and execute it as async
                    last_expr_code = compile(ast.Expression(last_expression.value), "<string>", "eval", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
                    result = await eval(last_expr_code, context)
                else:
                    # If last expression is not an await, compile and evaluate it normally
                    last_expr_code = compile(ast.Expression(last_expression.value), "<string>", "eval")
                    result = eval(last_expr_code, context)
                if result is not None:
                    print(result)
            return output_recorder.outputs
        except:
            traceback.print_exc()
            raise

async def main():
    code = """
# plot a line plot for example
import matplotlib.pyplot as plt
import numpy as np
x = np.linspace(0, 10, 100)
y = np.sin(x)
plt.plot(x, y)
plt.show()
"""
    from hypha_store import HyphaDataStore

    store = HyphaDataStore()
    await store.setup(None)
    result = await execute_code(store, code, {})
    print(result)

if __name__ == "__main__":
    asyncio.run(main())