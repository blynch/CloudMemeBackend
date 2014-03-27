"""CloudMeme Backend API provides functionality for a mobile meme browser + generator

Provides a backend for the mobile meme generator application. Makes use of Endpoints
and MongoDB on Compute Engine.
"""

import endpoints
from google.appengine.api import users
import logging
import os
from PIL import Image
from protorpc import messages
from protorpc import message_types
from protorpc import remote

# Cloud Image Build
from cloudmeme_image import CloudMemeImage

# Cloud Storage Import
from cloudmeme_storage import CloudMemeStorage

BUCKET = '/<EDIT: BUCKET>'

# Mongo import
from pymongo import MongoClient

MONGO_CONNECT = 'mongodb://<USER>:<PASSWORD>@<HOST>:27017/cloudmeme'

client = MongoClient(MONGO_CONNECT)
mongoDBConnection = client.cloudmeme
package = 'CloudMeme'

WEB_CLIENT_ID = '<EDIT: WEB CLIENT ID FROM THE CLOUD CONSOLE>'
ANDROID_CLIENT_ID = '<EDIT: ANDROID CLIENT ID FROM THE CLOUD CONSOLE>'
ANDROID_AUDIENCE = WEB_CLIENT_ID


class Meme(messages.Message):
    """Meme stores the image url and text."""
    image_url = messages.StringField(1)
    text = messages.StringField(2)
    id = messages.StringField(3)
    user = messages.StringField(4)
    votes = messages.IntegerField(5)

class MemeCollection(messages.Message):
    """Collection of Memes."""
    items = messages.MessageField(Meme, 1, repeated=True)


class Template(messages.Message):
    """Starter template for creating memes."""
    url = messages.StringField(1)

class TemplateCollection(messages.Message):
    """Collection of starter templates."""
    items = messages.MessageField(Template, 1, repeated=True)

STORED_MEMES = MemeCollection(items=[
    Meme(image_url='http://storage.googleapis.com/cloudmemebucket/meme-10328715.jpg',
         text='Good Guy Urs Uses actual numbers'),
    Meme(image_url='http://storage.googleapis.com/cloudmemebucket/meme-10328715.jpg',
         text='Good Guy Urs Uses actual numbers'),
])


@endpoints.api(name='cloudmeme', version='v1',
               description='Meme API',
               allowed_client_ids=[WEB_CLIENT_ID, ANDROID_CLIENT_ID,
                                   endpoints.API_EXPLORER_CLIENT_ID],
               audiences=[ANDROID_AUDIENCE],
               scopes=[endpoints.EMAIL_SCOPE])
class CloudMemeApi(remote.Service):
    """CloudMeme API v1."""

    """EndPoint Definitions"""



    CREATE_METHOD_RESOURCE = endpoints.ResourceContainer(
            Meme)

    @endpoints.method(CREATE_METHOD_RESOURCE, Meme,
                      path='cloudmeme', http_method='POST',
                      name='memes.create')

    def memes_create(self, request):
      current_user = endpoints.get_current_user()
      if current_user is None:
        raise endpoints.UnauthorizedException('Invalid token.')

      imageUrl = request.image_url
      text = request.text

      # Create the Meme
      meme = CloudMemeImage()
      mergedImage = meme.render_meme(imageUrl, 'impact', text,
                                     '', '')

      # Upload to Cloud Storage
      cloudMemeStorage = CloudMemeStorage()
      url = cloudMemeStorage.uploadFile(BUCKET, mergedImage)


      # Mongo: Create the meme meta data
      db = self.getMongo()
      meme = {"url": url,
              "text": text,
              "user": current_user.nickname(),
              "votes": 0}
      memes = db.memes
      memes.insert(meme)

      return Meme(image_url=url, text=text)


    @endpoints.method(message_types.VoidMessage, MemeCollection,
                      path='cloudmeme', http_method='GET',
                      name='memes.list')
    def memes_list(self, unused_request):
      # Mongo: Retrieve the meta data for stored memes
      # Mongo: Retrieve the meta data for stored memes
      db = self.getMongo()
      memes = []
      for memeEntry in db.memes.find().sort([( '_id', -1 )]):
        # Check for the existence of votes
        memeVotes = 0
        if 'votes' in memeEntry:
          memeVotes = memeEntry['votes']
        meme = Meme(text=memeEntry['text'],
                    image_url=memeEntry['url'],
                    id=unicode(memeEntry['_id']),
                    votes=int(memeVotes))
        memes.append(meme)

      return MemeCollection(items=memes)



    STORED_TEMPLATES = TemplateCollection(items=[
        Template(url='http://storage.googleapis.com/cloudmemetemplates/template-urs.jpg'),
    ])


    @endpoints.method(message_types.VoidMessage, TemplateCollection,
                      path='cloudmeme/templates', http_method='GET',
                      name='memes.list_templates')
    def templates_list(self, unused_request):
      return self.STORED_TEMPLATES


    """Utility Functions"""

    """Get the mongo client already created"""
    def getMongo(self):
      return mongoDBConnection

    """Check for production"""
    def runningInProduction(self):
      return (os.environ['SERVER_SOFTWARE'].find('Development') != 0)

APPLICATION = endpoints.api_server([CloudMemeApi])
