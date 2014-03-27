"""Storage class for Cloud Meme Service"""

from cloudstorage import api_utils, cloudstorage_api
import logging
import StringIO
import uuid

CLOUD_STORAGE_URL = 'https://storage.googleapis.com'

class CloudMemeStorage:

  def uploadFile(self, bucket, memeImage):

    # Upload to Cloud Storage
    uniqueIdString = str(uuid.uuid4())
    uniqueIdString = uniqueIdString.replace('-', '')

    filename = bucket + '/meme-' + uniqueIdString + '.png'
    url = CLOUD_STORAGE_URL + filename

    write_retry_params = api_utils.RetryParams(backoff_factor=1.1)
    cloud_file = cloudstorage_api.open(filename,
                                       'w',
                                       content_type='image/png',
                                       options={'x-goog-acl': 'public-read'},
                                       retry_params=write_retry_params)
    output = StringIO.StringIO()
    memeImage.save(output, format="PNG")
    contents = output.getvalue()
    output.close()

    try:
      cloud_file.write(contents)
      cloud_file.close()
    except Exception, e:
      logging.error(e)
      return Meme(image_url="", text="")

    logging.info('wrote: ' + filename)

    return url
