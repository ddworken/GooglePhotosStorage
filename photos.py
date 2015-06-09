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

def getImages(filename):                #call this function with a filename (in the current working directory) and it will encode that file into a series of images that will be saved in the current working directory
    chunks = splitData(fileToB64Data(filename))
    for index,chunk in enumerate(chunks):
        getImage(chunk).save(filename + "-" + str(index) + ".png")  #filename format for this program is: [OriginalFileName]-[Number].png (e.g. test.txt-0.png)

def fileToB64Data(filename):            #converts a file into a base64 string
    with open(filename) as file:
        data = base64.b64encode(file.read())
    return data

def splitData(data):                    #takes a large string and splits it into a list of smaller strings with length of 833 since I can only encode 833 bytes per image
    dataChunks = []
    for i in range(len(data)/833):  #833 is the number of characters we can encode in any one image
        dataChunks.append(data[:833])
        data = data[833:]
    return dataChunks

def getImage(dataChunk):                #Takes a string (with less than 833 bytes) and returns an image containing said string
    return encode(dataChunk)

def encode(message):                    #This function comes from here: https://github.com/Lukasa/entweet and is used to encode text into an image
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
def getMessage(originalFilename):       #Given the the filename of the original file, this will search the current working directory for the images that contain said file and will return the original file
    listOfImages = glob.glob(originalFilename + "-*")
    listOfImages.sort()
    messages = []
    for filename in listOfImages:
        messages.append(getAMessage(filename))
    encodedMessage = ''.join(messages)
    encodedMessage += "=" * ((4 - len(encodedMessage) % 4) % 4) #When the length of the base64 encoded string is not divisible by 4, we need to add = until it is since the base64 library requires padding of base64 strings
    return base64.b64decode(encodedMessage)

def sortList(list, originalFilename):       #list.sort() does not work because I want the order the list to be: ['test-0.png','test-1.png','test-2.png'...] instead of ['test-0.png','test-1.png','test-10.png',test-11.png''test-2.png'...]
    tuples = []                             #So I break the filenames up into tuples: ([OriginalFilename],[Number],.png) and then sort the list of tuples based off of the second the number in the tuple
    for item in list:
        tuples.append(item.split('-'))      #Split on the - thereby creating tuples of ([OriginalFilename],[number].png)
    newTuples = []
    for item in tuples:
        newTuple = ((item[0]+'-',int(item[1].split('.')[0]),'.'+item[1].split('.')[1])) #convert the previously generated tuple into one that matches the spec above
        newTuples.append(newTuple)
    newTuples.sort(key=lambda tup: tup[1])  #sort the list of tuples based off of the number
    final = []
    for tuple in newTuples:
        final.append(''.join(tuple))        #reassemble the tuples into strings and then return the strings
    return final

def fileToBinary(filename):                 #given a filename, get the binary
    with open(filename) as file:
        binary = file.read()
    return binary

def getAMessage(filename):                  #given the name of an image, get the text encoded into the image
    binary = fileToBinary(filename)
    pseudoFile = cStringIO.StringIO(binary)
    image = Image.open(pseudoFile)
    return decode(image)

def decode(text_image):                     #This function comes from here: https://github.com/Lukasa/entweet and is used to go from image to text
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

def get_char_image(image, col, row):       #This function comes from here: https://github.com/Lukasa/entweet and is used to break the image up into individual characters
    return image.crop((
        col * char_width,
        row * char_height,
        (col + 1) * char_width,
        (row + 1) * char_height,
    ))

def get_image_char(image):                  #This function comes from here: https://github.com/Lukasa/entweet and is used to calculate the character in a given image
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

def rmsdiff(diff):                          #This function comes from here: https://github.com/Lukasa/entweet and is used to calculate the difference between characters
    h = diff.histogram()
    return math.sqrt(reduce(operator.add,
        map(lambda h, i: h*((i or 0)**2), h, range(256))
    ) / (float(char_width) * char_height))

def generate_image_map(chars):              #This function comes from here: https://github.com/Lukasa/entweet and is used to generate a map of the image so it can be decoded
    image = Image.new('RGB', (10000, 100))
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), chars, font=font)
    width, height = font.getsize(chars)
    image = image.crop((0, 0, width, height))
    return {c: get_char_image(image, i, 0) for i, c in enumerate(chars)}
image_map = generate_image_map(chars)
