#!/usr/bin/python3
import time, inspect, re, json, os, math, base64, zlib
import tkinter as tk
import tkinter.filedialog as filedialog
from PIL import Image, ImageDraw, ImageTk, ImageFont

W, H = 1192, 68*8

def vars_all(obj, replace=None):
    var = {}
    for attr in dir(obj):
        var[attr] = getattr(obj, attr) if not replace else replace(getattr(obj, attr), attr)
    return var

root2 = tk.Tk()
root2.title('Code')
textbox = tk.Text(root2,
                  height=20, width=80,
                  bg='#333', fg='white', insertbackground='yellow', borderwidth=2, relief=tk.SOLID)
textbox.pack(fill=tk.BOTH, expand=tk.YES)
textbox.focus()

root1 = tk.Tk()
root1.title('Preview')
root1.geometry('+0+0')
canvas = tk.Canvas(root1, bg='gray', width=W, height=H)
canvas.pack(fill=tk.NONE, expand=tk.NO)

img = Image.new('1', (W, H))
draw = ImageDraw.Draw(img)
draw.math = math
draw.w, draw.h = W, H
draw.x, draw.y = 0, 0

matchX, matchY = re.compile(r'\bx\b'), re.compile(r'\by\b')

imgTk = None
needRedraw = True
content = ''

BEGINNING = f"""# Generated with Pillow Designer
from PIL import Image, ImageDraw, ImageFont
import os, math

_cache = {{}}
img = Image.new({json.dumps(img.mode)}, ({W}, {H}), 1)
draw = ImageDraw.Draw(img)

"""
END = """if __name__ == '__main__':
    img.show()
"""
START = '\n#START\n'
STOP = '\n#STOP\n\n'

def insert(text):
    textbox.insert(textbox.index(tk.INSERT), text)
    textbox.mark_set(tk.INSERT, tk.END)

def select_all(event):
    event.widget.tag_add(tk.SEL, '1.0', tk.END)
    event.widget.mark_set(tk.INSERT, tk.END)
    return 'break'
textbox.bind('<Control-a>', select_all)

# Custom methods
_cache = {}

def customText(xy, text, fontFile, size):
    font_path = os.path.join('fonts', fontFile + '.ttf')
    key = f'font_{size}px'
    if not (key in _cache):
        _cache[key] = {}
    if not (fontFile in _cache[key]):
        _cache[key][fontFile] = ImageFont.truetype(font_path, size)
    draw.text(xy, text, font=_cache[key][fontFile])

customMethods = ['customText']
for customMethod in customMethods:
    setattr(draw, customMethod, globals()[customMethod])
# End Custom methods

def genScript():
    calls = []
    def encode(obj):
        try:
            return json.dumps(obj)
        except Exception as e:
            raise e # TODO
    def handler(name, args, kwargs):
        #print(name, args, kwargs)
        calls.append(f'{"draw." if not (name in customMethods) else ""}{name}({", ".join([encode(arg) for arg in args])}, {", ".join([kwarg + "=" + encode(kwargs[kwarg]) for kwarg in kwargs])})')
    try:
        exec(content, vars_all(draw, lambda val, attr: val if not callable(val) else lambda *args, **kwargs:handler(attr, args, kwargs)))
    except Exception as e:
        print(e)
    customs = []
    for customMethod in customMethods:
        customs.append(inspect.getsource(globals()[customMethod]))
    return '#' + base64.b64encode(zlib.compress(content.encode('utf-8'))).decode('utf-8') + '\n' + BEGINNING + ''.join(customs) + START + '\n'.join(calls) + STOP + END

def save():
    file = filedialog.asksaveasfile('wb',
                                    filetypes=(('Python Scripts', '*.py'), ('Pillow Designer File', '*.txt'), ('Portable Network Graphics', '*.png'), ('All Files', '*.*')),
                                    initialdir=os.getcwd(), master=root1 if root1.focus_displayof() else root2)
    if not file:
        return
    if file.name.endswith('.png'):
        img.save(file)
    elif file.name.endswith('.py'):
        file.write(genScript().replace('\n', '\r\n').encode('utf-8'))
    else:
        file.write(content.replace('\n', '\r\n').encode('utf-8'))
    file.close()
def load():
    file = filedialog.askopenfile(
        filetypes=(('Python Scripts', '*.py'), ('Pillow Designer File', '*.txt'), ('All Files', '*.*')),
        initialdir=os.getcwd(), master=root1 if root1.focus_displayof() else root2)
    if not file:
        return
    if file.name.endswith('.py'):
        content2 = zlib.decompress(base64.b64decode(file.readline()[1:]))
    else:
        content2 = file.read()
    file.close()
    textbox.delete('1.0', tk.END)
    insert(content2)

def addCommand(menu, text, cb, key=None):
    menu.add_command(label=text, command=cb, accelerator=None if not key else key[1])
    cb2 = lambda e: cb() or 'break' # to prevent defoult (like Ctrl+T)
    if key:
        textbox.bind(key[0], cb2)
        root1.bind(key[0], cb2)

menubar = tk.Menu(root2)
filemenu = tk.Menu(menubar, tearoff=False)
#filemenu.add_separator()
addCommand(filemenu, 'Save', save, ('<Control-s>', 'Ctrl+S'))
addCommand(filemenu, 'Open', load, ('<Control-o>', 'Ctrl+O')) # TODO
menubar.add_cascade(label='File', menu=filemenu)

insertmenu1 = tk.Menu(menubar, tearoff=False)
addCommand(insertmenu1, 'Text', lambda: insert('customText((x, y), \'Text\', \'UbuntuMono-Regular\', 20)\n'), ('<Control-t>', 'Ctrl+T'))
addCommand(insertmenu1, 'Rectangle', lambda: insert('rectangle((x, y, x, y), width=4)\n'), ('<Control-r>', 'Ctrl+R'))
addCommand(insertmenu1, 'Ellipse', lambda: insert('ellipse((x, y, x, y), width=4)\n'), ('<Control-e>', 'Ctrl+E'))
addCommand(insertmenu1, 'Triangle', lambda: insert('polygon((x, y, x, y, x, y), width=4)\n'), ('<Control-p>', 'Ctrl+P'))
addCommand(insertmenu1, 'Line', lambda: insert('line((x, y, x, y), width=4)\n'), ('<Control-l>', 'Ctrl+L'))
menubar.add_cascade(label='Insert', menu=insertmenu1)

insertmenu2 = tk.Menu(menubar, tearoff=False)
for attr in dir(draw):
    if attr.startswith('_'):
        continue
    # inspect.getargspec(getattr(draw, attr)).args[1:])
    addCommand(insertmenu2, attr, lambda param=attr + (f'({", ".join(inspect.signature(getattr(draw, attr)).parameters.keys())})\n' if callable(getattr(draw, attr)) else ''): insert(param))

menubar.add_cascade(label='Insert (Raw)', menu=insertmenu2)

root2.config(menu=menubar)

def mouseMove(event):
    global needRedraw
    draw.x, draw.y = event.x, event.y
    needRedraw = True
canvas.bind("<Motion>", mouseMove)
def mouseClick(event):
    content2 = matchX.sub(str(draw.x), matchY.sub(str(draw.y), content, 1), 1)
    textbox.delete('1.0', tk.END)
    #print(content2)
    insert(content2)
canvas.bind("<Button-1>", mouseClick)

def redraw(event):
    global content, needRedraw
    # Set up event to trigger multiple times
    # event.widget == textbox
    if not event.widget.edit_modified():  # check if the text has been modified
        return
    event.widget.edit_modified(False)
    content = event.widget.get("1.0", "end-1c")
    # Draw
    needRedraw = True

def _really_draw():
    global imgTk
    draw.rectangle((0, 0, img.width, img.height), fill=0xff)
    try:
        exec(content, vars_all(draw))
    except Exception as e:
        print(e)
    imgTk = ImageTk.PhotoImage(img, master=root1)
    canvas.create_image(W/2, H/2, image=imgTk)
    
textbox.bind('<<Modified>>', redraw)

while True:
    try:
        if needRedraw:
            _really_draw()
            needRedraw = False
        root1.update()
        root2.update()
    except:
        break
    time.sleep(1/15)
try:
    root1.destroy()
except:
    pass
try:
    root2.destroy()
except:
    pass
