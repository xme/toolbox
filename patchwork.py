#!/usr/bin/python
#
# patchwork.py - Generate a patchwork of images
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
#

import glob
import time
try:
    from progress.bar import Bar
except:
    print "Install Python progress"
    exit(1)
try:
    from PIL import Image
except:
    print "Install Python PIL"
    exit(1)

images = []
imagesPerLine = 150	# How many pictures per line
widx = 0
ridx = 0
width = 5000
height = 5000  		# For very big picture
totalWidth = 0
totalImages = 0

totalFiles=0
for filename in glob.glob('./screenshot-*.jpg'):
    totalFiles+=1
bar = Bar('Reading images', max=totalFiles)

for filename in glob.glob('./screenshot-*.jpg'):
    if widx < imagesPerLine:
        # Load picture into the array
        try:
            im = Image.open(filename)
            # Skip white images
            extrema = im.convert("L").getextrema()
            if extrema == (0, 255):
                images.append(im)
                width=min(width, im.width)
                totalWidth+=width
                height=min(height, im.height)
                widx+=1
                totalImages+=1
        except:
            print "Cannot process: %s" % filename
    else:
        # Create an horizontal image based on x previous images
        dst = Image.new('RGB', (totalWidth, height))
        for i in range(imagesPerLine):
            wpercent = (width/float(images[i].size[0]))
            hsize = int((float(images[i].size[1])*float(wpercent)))
            img = images[i].resize((width,hsize), Image.ANTIALIAS)
            dst.paste(img, (i * width, 0))
            images[i].close()
        dst.save("row-" + str(ridx) + ".jpg")
        widx=0
        ridx+=1
        totalWidth=0
        images = []
    bar.next()

bar.finish()
print "Processed images: %d" % totalImages
images = []
ridx = 0
width = 0
height = 0
totalHeight = 0

totalFiles=0
for filename in glob.glob('./row-*.jpg'):
    totalFiles+=1
bar = Bar('Creating patchwork', max=totalFiles)
for filename in glob.glob('./row-*.jpg'):
    im = Image.open(filename)
    images.append(im)
    width=im.width
    height=im.height
    totalHeight+=height
    ridx+=1
    bar.next()
bar.finish()
print "New image: %d x %d" % (width, totalHeight)
bar = Bar('Dumping file', max=ridx)
dst = Image.new('RGB', (width, totalHeight))
for i in range(ridx):
    dst.paste(images[i], (0, i * height))
    images[i].close()
    bar.next()
dst.save("wall.jpg")
bar.finish()
exit(0)
