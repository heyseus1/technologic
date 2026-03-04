#!/usr/bin/python

import requests
import os   
import json
import jwt
from jwt.algorithms import has_crypto
import datetime


if not jwt.algorithms.has_crypto:
    print("No crypto support for JWT, please install the cryptography dependency")

if has_crypto:
    from jwt.algorithms import RSAAlgorithm


class okta_jwk_authentication():
    def okta_token(self):
        client_id = os.environ["OKTA_JWT_CLIENT_ID"]
        OktaDomain = "zoom.okta.com"

        # We get a JWK from Okta in the following form
        # This can also be taken as a PEM, although we don't
        # This is a secret normally it'd be stored in Confidant as a JSON string

        x = open('jwk.json')
        private_jwk = json.load(x)
        #print(private_jwk)
        serialized_jwk = json.dumps(private_jwk)
        #print(serialized_jwk)
        priv_rsakey = RSAAlgorithm.from_jwk(serialized_jwk)

        # iss and sub are the client_id provi   d for your API service
        # aud is the authorization server
        # exp, max time is one hour, per Okta requirements.
        
        our_jwt = jwt.encode(
            payload={
                "aud": f"https://{OktaDomain}/oauth2/v1/token",
                "iss": client_id,
                "sub": client_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            },
            key=priv_rsakey,
            algorithm="RS256",
        )
        #print(our_jwt)
        # Note, you must request the scopes needed to make the API calls you need
        # in this example we request okta.users.read()
        payload = {
            "grant_type": "client_credentials",
            "scope": "okta.users.read",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": our_jwt,
            "client_id": client_id,
        }
        #print(data)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        resp = requests.post(
            f"https://{OktaDomain}/oauth2/v1/token", headers=headers, data=payload
        )
        # If you don't get a 200, you should receive a JSON encoded error
        # {"error":"invalid_client","error_description":"The client_assertion token has an expiration too far into the future."}
        if resp.status_code == 200:
            access_token = resp.json()["access_token"]
            #print(access_token)
            return access_token 
        else:
            print(resp.text)

if __name__ == "__main__":
    okta_jwk_authentication().okta_token()
