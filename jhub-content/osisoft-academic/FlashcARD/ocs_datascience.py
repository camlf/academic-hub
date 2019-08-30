
import requests

class OCSClient:
    def __init__(self, apiversion, tenant, url, clientId, clientSecret):
        self._resource_url = url
        self._tenant_id = tenant
        self._api_version = apiversion
        self._client_id = clientId
        self._client_secret = clientSecret
        
    def authorization_headers(self):
        # Request a fresh authorization bearer token 
        discovery = requests.get(self._resource_url + '/identity/.well-known/openid-configuration', headers={'Accept': 'application/json'})
        if discovery.status_code < 200 or discovery.status_code >= 300:
            raise Exception(f'Failed to get access token endpoint from discovery URL: {discovery.status_code}: {discovery.text}')
        token_endpoint = discovery.json()['token_endpoint']
        authorization = requests.post(token_endpoint, data={'client_id': self._client_id, 
                                                            'client_secret': self._client_secret, 
                                                            'grant_type': 'client_credentials' })
        headers = {
            'Authorization': 'bearer %s' % authorization.json()['access_token'],
            'Content-type': 'application/json',
            'Accept': 'text/plain', 
            'Request-Timeout': '60000' 
        }
        return headers
    
    def namespace_url(self, namespace):
        return self._resource_url + f'/api/{self._api_version}/Tenants/{self._tenant_id}/Namespaces/{namespace}' 
    