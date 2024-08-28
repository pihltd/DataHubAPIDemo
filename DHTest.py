import requests
import os

def apiQuery(query):
    #headers = {"Authorization" : f"Bearer {token}", "accept" : "application/json"}
    token = os.environ['DEV2API']
    headers = {"Authorization": f"Bearer {token}"}
    url = 'https://hub-dev2.datacommons.cancer.gov/api/graphql'
    print(headers)
    try:
        #result = requests.post(url, headers = headers, data = query)
        result = requests.post(url = url, headers = headers, json={"query": query})
        if result.status_code == 200:
            return result.json()
        else:
            #return(f"Error: {result.status_code}")
            print(f"Error: {result.status_code}")
            print(type(result))
            print(result.request)
            print(result.encoding)
            print(result.text)
            return result.content
    except requests.exceptions.HTTPError as e:
        return(f"HTTP Error: {e}")
    
query = """
{
  listSubmissions{
      submissions{
          studyID
        }
    }
}
"""
res = apiQuery(query)
print(res)