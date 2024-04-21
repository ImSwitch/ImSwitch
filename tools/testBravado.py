from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient

from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests

# Warnungen für unsichere Anfragen deaktivieren
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


http_client = RequestsClient()
http_client.session.verify = False  # Disable SSL verification

client = SwaggerClient.from_url(
    'https://youseetoo.github.io/imswitch/openapi.json',
    http_client=http_client, 
    config={'validate_swagger_spec': False,
             'use_models': False}
)

pet = client.pet.getPetById(petId=1).response().result