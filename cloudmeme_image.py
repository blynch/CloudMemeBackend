"""Meme generator class for building the final meme image"""

import collections
import cStringIO
import logging
import os
import urllib


from PIL import Image, ImageDraw, ImageFilter, ImageFont

from google.appengine.ext import ndb

class CloudMemeImage:

  TOP = "top"
  MIDDLE = "middle"
  BOTTOM = "bottom"
  LEFT = "left"
  RIGHT = "right"
  DEFAULT_FONT = "impact.ttf"
  DEFAULT_FONT_SIZE = 48
  DEFAULT_TEXT_COLOR = "#FFF"
  DEFAULT_BORDER_COLOR = "#000"
  DEFAULT_BORDER_WIDTH = 2
  MEME_FONTS = collections.OrderedDict([
    ('impact', 'impact.ttf'),
    ('mikachan', 'mikachan.ttf'),
    ('FreeSerif', 'FreeSerif.ttf'),
  ])
  FONT_DIR = 'fonts'


  def render_meme(self, source_image_url, meme_font,  upper_text, middle_text, lower_text):
      """Renders an image with given HTTP parameters.

      Returns:
          A rendered Image object.
      """
      try:
        file = cStringIO.StringIO(urllib.urlopen(source_image_url).read())
        image = Image.open(file)
      except Exception, e:
        logging.error(e)
        return False

      font_file = os.path.join(self.FONT_DIR,
                               self.MEME_FONTS.get(meme_font,
                                                   self.DEFAULT_FONT))
      upper_text_align = self.MIDDLE
      middle_text_align = self.MIDDLE
      lower_text_align = self.MIDDLE
      if upper_text:
          self.draw_text(image, self.TOP, upper_text_align, upper_text,
                         font_file=font_file)
      if middle_text:
          self.draw_text(image, self.MIDDLE, middle_text_align, middle_text,
                         font_file=font_file)
      if lower_text:
          self.draw_text(image, self.BOTTOM, lower_text_align, lower_text,
                         font_file=font_file)

      return image


  def get_points_for_hemming(self, src, border_width=1):
      """Returns a list of points described below.

      Args:
          src: (x, y) tuple indicating the source point.
          border_width: a width of the border line.

      Returns:
          List of points described as * in the following figure.

          when border=1:
          ***
          *@*
          ***

          when border=2:
          * * *

          * @ *

          * * *
      """
      x, y = src
      return [
          (x - border_width, y - border_width), (x, y - border_width),
          (x + border_width, y - border_width), (x - border_width, y),
          (x + border_width, y), (x - border_width, y + border_width),
          (x, y + border_width), (x + border_width, y + border_width),
      ]


  def draw_text(self, target, vertical_position, horizontal_position, text,
                font_file=DEFAULT_FONT, font_size=DEFAULT_FONT_SIZE,
                color=DEFAULT_TEXT_COLOR,
                border_width=DEFAULT_BORDER_WIDTH,
                border_color=DEFAULT_BORDER_COLOR):
      """Draws a text at a given position in a given image.

      Args:
          target: a target image object.
          vertical_position: either of TOP|MIDDLE|BOTTOM
          horizontal_position: either of LEFT|MIDDLE|RIGHT
          text: text to draw
          font_file: font filename for drawing the text
          font_size: font size
          color: text color
          border_width: border width of the text
          border_color: border color of the text
      """
      # determine the original text size
      font = ImageFont.truetype(font_file, font_size)
      image = Image.new("RGBA", (1, 1))
      draw = ImageDraw.Draw(image)
      text_width, text_height = draw.textsize(text, font=font)
      del draw

      # draw text with border
      bordered_text_width = text_width + 2 * border_width
      bordered_text_height = text_height + 2 * border_width
      image = Image.new('RGBA', (bordered_text_width, bordered_text_height))
      draw = ImageDraw.Draw(image)
      for pos in self.get_points_for_hemming((border_width, border_width),
                                        border_width):
          draw.text(pos, text, font=font, fill=border_color)
      draw.text((border_width, border_width), text, font=font, fill=color)
      del draw

      # obtain bounding boxes for 2 images for later use
      bbox = target.getbbox()
      text_bbox = image.getbbox()

      # scale only if the text exceeds the width of the target image
      if bbox[2] < text_bbox[2]:
          scale = float(bbox[2]) / text_bbox[2]
          image = image.resize((int(text_bbox[2] * scale),
                                int(text_bbox[3] * scale)), Image.ANTIALIAS)
          text_bbox = image.getbbox()
      else:
          image = image.filter(ImageFilter.SMOOTH)

      # determine the paste position
      if vertical_position == self.TOP:
          pos_y = 0
      elif vertical_position == self.MIDDLE:
          pos_y = int(bbox[3] / 2 - text_bbox[3] / 2)
      elif vertical_position == self.BOTTOM:
          pos_y = bbox[3] - text_bbox[3]
      else:
          raise RuntimeError('Invalid vertical_position: {}'
                           .format(vertical_position))
      if horizontal_position == self.LEFT:
          pos_x = 0
      elif horizontal_position == self.MIDDLE:
          pos_x = int(bbox[2] / 2 - text_bbox[2] / 2)
      elif horizontal_position == self.RIGHT:
          pos_x = bbox[2] - text_bbox[2]
      else:
          raise RuntimeError('Invalid horizontal_position: {}'
                             .format(horizontal_position))

      target.paste(image , (pos_x, pos_y), image)

