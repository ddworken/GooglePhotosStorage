from PIL import Image, ImageFont, ImageDraw, ImageChops
import os
import math
import operator
import base64
import cStringIO
import glob

font_size = 24
padding = 5

font = ImageFont.truetype(
    os.path.join(os.path.dirname(__file__), 'Inconsolata-Regular.ttf'),
    size=font_size
)

char_width, char_height = font.getsize('A')
char_height += padding
chars = ''.join([chr(o) for o in range(32, 127)])

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#File to images

def getImages(filename):
    chunks = splitData(fileToB64Data(filename))
    for index,chunk in enumerate(chunks):
        getImage(chunk).save(filename + "-" + str(index) + ".png")

def fileToB64Data(filename):
    with open(filename) as file:
        data = base64.b64encode(file.read())
    return data

def splitData(data):
    dataChunks = []
    for i in range(len(data)/833):  #833 is the number of characters we can encode in any one image
        dataChunks.append(data[:833])
        data = data[833:]
    return dataChunks

def getImage(dataChunk):
    return encode(dataChunk)

def encode(message):
    image = Image.new('RGB', (10000, 10000))
    draw = ImageDraw.Draw(image)
    height = padding
    max_width = 0
    size = (0, 0)
    for line in message.splitlines():
        # Leave a space for blank lines.
        if not line:
            height += char_height
            continue
        size = font.getsize(line)
        draw.text((padding, height), line, font=font)
        height += char_height
        max_width = max(max_width, size[0] + 10)
    return image.crop((0, 0, max_width, height + 10))

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Images to file
def getMessage(originalFilename):
    listOfImages = glob.glob(originalFilename + "-*")
    listOfImages.sort()
    messages = []
    for filename in listOfImages:
        messages.append(getAMessage(filename))
    encodedMessage = ''.join(messages)
    encodedMessage += "=" * ((4 - len(encodedMessage) % 4) % 4)
    return base64.b64decode(encodedMessage)

def sortList(list, originalFilename):       #list.sort() does not work because I want the order the list to be: ['test-0.png','test-1.png','test-2.png'...] instead of ['test-0.png','test-1.png','test-10.png',test-11.png''test-2.png'...]
    tuples = []
    for item in list:
        tuples.append(item.split('-'))
    newTuples = []
    for item in tuples:
        newTuple = ((item[0]+'-',int(item[1].split('.')[0]),'.'+item[1].split('.')[1]))
        newTuples.append(newTuple)
    newTuples.sort(key=lambda tup: tup[1])
    final = []
    for tuple in newTuples:
        final.append(''.join(tuple))
    return final

def fileToBinary(filename):
    with open(filename) as file:
        binary = file.read()
    return binary

def getAMessage(filename):
    binary = fileToBinary(filename)
    pseudoFile = cStringIO.StringIO(binary)
    image = Image.open(pseudoFile)
    return decode(image)

def decode(text_image):
    width, height = text_image.size
    text_image = text_image.crop((padding, padding, width - padding, height - padding))
    width, height = text_image.size
    cols = int(width / char_width)
    rows = int(height / char_height)
    lines = []
    for row in range(rows):
        line = ''
        for col in range(cols):
            image = get_char_image(text_image, col, row)
            line += get_image_char(image)
        lines.append(line.strip())
    return '\n'.join(lines)

def get_char_image(image, col, row):
    return image.crop((
        col * char_width,
        row * char_height,
        (col + 1) * char_width,
        (row + 1) * char_height,
    ))

def get_image_char(image):
    diffs = {}
    for char, char_image in image_map.items():
        diff = ImageChops.difference(image, char_image)
        if diff.getbbox() is None:
            return char
        diffs[char] = diff
    min_rms = 10**6
    closest_char = ''
    for char, diff in diffs.items():
        rms = rmsdiff(diff)
        if rms < min_rms:
            min_rms = rms
            closest_char = char
    return closest_char

def rmsdiff(diff):
    h = diff.histogram()
    return math.sqrt(reduce(operator.add,
        map(lambda h, i: h*((i or 0)**2), h, range(256))
    ) / (float(char_width) * char_height))

def generate_image_map(chars):
    image = Image.new('RGB', (10000, 100))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), chars, font=font)
    width, height = font.getsize(chars)
    image = image.crop((0, 0, width, height))
    return {c: get_char_image(image, i, 0) for i, c in enumerate(chars)}
image_map = generate_image_map(chars)
