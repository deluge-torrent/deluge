#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Bryan Davis <casadebender+pil@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at 
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software 
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT 
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the 
# License for the specific language governing permissions and limitations 
# under the License.
#
# $Id$
"""Alternate PIL plugin for dealing with Microsoft .ico files. Handles XOR
transparency masks, XP style 8bit alpha channels and Vista style PNG image 
parts.

>>> import PIL.Image
>>> import Win32IconImagePlugin
>>> ico = PIL.Image.open("down.ico")
>>> print ico.info['sizes']
set([(16, 16), (48, 48), (256, 256), (32, 32)])
>>> ico.size = (16, 16)
>>> ico.show()

This implementation builds on several samples that I found around the net.
Karsten Hiddemann posted a hint on Image-SIG_ that got me started on this.
Some time later I found a `django snippet`_ by *dc* that I borrowed the
``struct.unpack`` syntax from. I also spent a lot of time looking at the
IcoImagePlugin, BmpImagePlugin, PngImagePlugin and other files from PIL.

Icon format references:
  * http://en.wikipedia.org/wiki/ICO_(file_format)
  * http://msdn.microsoft.com/en-us/library/ms997538.aspx

Example icon to test with `down.ico`_

.. _Image-SIG http://mail.python.org/pipermail/image-sig/2008-May/004986.html
.. _django snippet http://www.djangosnippets.org/snippets/1287/
.. _down.ico http://www.axialis.com/tutorials/iw/down.ico
"""

import logging
import struct
import PIL.Image
import PIL.ImageChops
import PIL.ImageFile
import PIL.BmpImagePlugin
import PIL.PngImagePlugin


_MAGIC = '\0\0\1\0'
log = logging.getLogger(__name__)


class Win32IcoFile (object):
  """
  Decoder for Microsoft .ico files.
  """

  def __init__ (self, buf):
    """
    Args:
      buf: file-like object containing ico file data
    """
    self.buf = buf
    self.entry = []

    header = struct.unpack('<3H', buf.read(6))
    if (0, 1) != header[:2]:
      raise SyntaxError, 'not an ico file'

    self.nb_items = header[2]

    dir_fields = ('width', 'height', 'nb_color', 'reserved', 'planes', 'bpp',
        'size', 'offset')
    for i in xrange(self.nb_items):
      directory = list(struct.unpack('<4B2H2I', buf.read(16)))
      for j in xrange(3):
        if not directory[j]:
          directory[j] = 256
      icon_header = dict(zip(dir_fields, directory))
      icon_header['color_depth'] = (
          icon_header['bpp'] or 
          (icon_header['nb_color'] == 16 and 4))
      icon_header['dim'] = (icon_header['width'], icon_header['height'])
      self.entry.append(icon_header)
    #end for (read headers)

    # order by size and color depth
    self.entry.sort(lambda x, y: \
        cmp(x['width'], y['width']) or cmp(x['color_depth'], y['color_depth']))
    self.entry.reverse()
  #end __init__


  def sizes (self):
    """
    Get a list of all available icon sizes and color depths.
    """
    return set((h['width'], h['height']) for h in self.entry)
  #end sizes


  def get_image (self, size, bpp=False):
    """
    Get an image from the icon

    Args:
      size: tuple of (width, height)
      bpp: color depth
    """
    idx = 0
    for i in range(self.nb_items):
      h = self.entry[i]
      if size == h['dim'] and (bpp == False or bpp == h['color_depth']):
        return self.frame(i)

    return self.frame(0)
  #end get_image


  def frame (self, idx):
    """
    Get the icon from frame idx

    Args:
      idx: Frame index

    Returns:
      PIL.Image
    """
    header = self.entry[idx]
    self.buf.seek(header['offset'])
    data = self.buf.read(8)
    self.buf.seek(header['offset'])
    if data[:8] == PIL.PngImagePlugin._MAGIC:
      # png frame
      im = PIL.PngImagePlugin.PngImageFile(self.buf)

    else:
      # XOR + AND mask bmp frame
      im = PIL.BmpImagePlugin.DibImageFile(self.buf)
      log.debug("Loaded image: %s %s %s %s", im.format, im.mode, im.size,
          im.info)

      # change tile dimension to only encompass XOR image
      im.size = im.size[0], im.size[1] / 2
      d, e, o, a = im.tile[0]
      im.tile[0] = d, (0,0) + im.size, o, a

      # figure out where AND mask image starts
      mode = a[0]
      bpp = 8
      for k in PIL.BmpImagePlugin.BIT2MODE.keys():
        if mode == PIL.BmpImagePlugin.BIT2MODE[k][1]:
          bpp = k
          break
      #end for
      log.debug("o:%s, w:%s, h:%s, bpp:%s", o, im.size[0], im.size[1], bpp)
      and_mask_offset = o + (im.size[0] * im.size[1] * (bpp / 8.0))

      if 32 == bpp:
        # 32-bit color depth icon image allows semitransparent areas
        # PIL's DIB format ignores transparency bits, recover them
        # The DIB is packed in BGRX byte order where X is the alpha channel

        # Back up to start of bmp data
        self.buf.seek(o)
        # extract every 4th byte (eg. 3,7,11,15,...)
        alpha_bytes = self.buf.read(im.size[0] * im.size[1] * 4)[3::4]

        # convert to an 8bpp grayscale image
        mask = PIL.Image.frombuffer(
            'L',            # 8bpp
            im.size,        # (w, h)
            alpha_bytes,    # source chars
            'raw',          # raw decoder
            ('L', 0, -1)    # 8bpp inverted, unpadded, reversed
        )

        # apply mask image as alpha channel
        im = im.convert('RGBA')
        im.putalpha(mask)
        log.debug("image mode: %s", im.mode)

      else:
        # get AND image from end of bitmap
        w = im.size[0]
        if (w % 32) > 0:
          # bitmap row data is aligned to word boundaries
          w += 32 - (im.size[0] % 32)
        # the total mask data is padded row size * height / bits per char
        total_bytes = long((w * im.size[1]) / 8)
        log.debug("tot=%d, off=%d, w=%d, size=%d", 
            len(data), and_mask_offset, w, total_bytes)

        self.buf.seek(and_mask_offset)
        maskData = self.buf.read(total_bytes)

        # convert raw data to image
        mask = PIL.Image.frombuffer(
            '1',            # 1 bpp
            im.size,        # (w, h)
            maskData,       # source chars
            'raw',          # raw decoder
            ('1;I', int(w/8), -1)  # 1bpp inverted, padded, reversed
        )

        # now we have two images, im is XOR image and mask is AND image
        # set mask as alpha channel
        im = im.convert('RGBA')
        im.putalpha(mask)
        log.debug("image mode: %s", im.mode)
      #end if !'RGBA'
    #end if (png)/else(bmp)

    return im
  #end frame


  def __repr__ (self):
    s = 'Microsoft Icon: %d images (max %dx%d %dbpp)' % (
        len(self.entry), self.entry[0]['width'], self.entry[0]['height'], 
        self.entry[0]['bpp'])
    return s
  #end __repr__
#end Win32IcoFile


class Win32IconImageFile (PIL.ImageFile.ImageFile):
  """
  PIL read-only image support for Microsoft .ico files.

  By default the largest resolution image in the file will be loaded. This can 
  be changed by altering the 'size' attribute before calling 'load'.

  The info dictionary has a key 'sizes' that is a list of the sizes available 
  in the icon file.

  Handles classic, XP and Vista icon formats.
  """

  format = 'ICO'
  format_description = 'Microsoft icon'

  def _open (self):
    self.ico = Win32IcoFile(self.fp)
    self.info['sizes'] = self.ico.sizes()
    self.size = self.ico.entry[0]['dim']
    self.load()
  #end _open

  def load (self):
    im = self.ico.get_image(self.size)
    # if tile is PNG, it won't really be loaded yet
    im.load()
    self.im = im.im
    self.mode = im.mode
    self.size = im.size
  #end load
#end class Win32IconImageFile


def _accept (prefix):
  """
  Quick file test helper for Image.open()
  """
  return prefix[:4] == _MAGIC
#end _accept


# register our decoder with PIL
PIL.Image.register_open(Win32IconImageFile.format, Win32IconImageFile, _accept)
PIL.Image.register_extension(Win32IconImageFile.format, ".ico")
