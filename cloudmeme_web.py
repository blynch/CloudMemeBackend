'''CloudMeme Web provides functionality for a the web front end of the meme generator.'''

from bson.objectid import ObjectId
from cloudmeme_api import CloudMemeApi
import logging
import pymongo
import random
import urllib
import uuid
import webapp2


class VoteHandler(webapp2.RequestHandler):

  def get(self, meme_id):

    '''Vote on a meme with a random user id. Purely for load testing.'''
    userIdString = str(uuid.uuid4())
    userIdString = userIdString.replace('-', '')

    cloudMemeApi = CloudMemeApi()
    db = cloudMemeApi.getMongo()

    logging.info('meme id: ' + meme_id)

    vote = {'user': userIdString,
            'meme_id': meme_id }

    votes = db.votes
    votes.insert(vote)

    memes = db.memes
    memes.update( { '_id': ObjectId(meme_id) },
                  { '$inc': { 'votes': 1 } } )

    self.response.write('Logged your vote.  Thanks!')


class MemeCreateHandler(webapp2.RequestHandler):

  def get(self):
    url = 'https://storage.googleapis.com/cloudmemebucket/meme-a14f4eef04044767b5b8760656b4d0b8.png'
    text = 'Yo Dog'

#    randomNum = random.randrange(0,100);
#    if(randomNum < 5):
#      logging.info('raising exception')
#      raise Exception('invalid', 'number')

    # Mongo: Create the meme meta data
    cloudMemeApi = CloudMemeApi()
    db = cloudMemeApi.getMongo()
    meme = {"url": url,
            "text": text,
            "user": "current user",
            "votes": 0}
    memes = db.memes
    memes.insert(meme)

    self.response.write('Created the meme')


app = webapp2.WSGIApplication([
    ('/vote/(.*)', VoteHandler),
    ('/create', MemeCreateHandler)
])
