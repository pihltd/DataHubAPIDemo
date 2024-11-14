#import requests
#import os
import CRDCStuff as crdc
import DHQueries as dq

#url, apitoken = crdc.dhAPICreds('stage')
#res = crdc.dhApiQuery(url, apitoken, dq.org_query)
#print(res)
#teststring = "This is # Test\t\n\r!@#$%^&*()"
#print(crdc.cleanString(teststring, True))

#testyamlfile = r'C:\Users\pihltd\Documents\github\CRDCLib\test\yamltestfile.yml'
#print(testyamlfile)
#print(crdc.readYAML(testyamlfile))

crdc_creds = crdc.dhAPICreds('stage')
res = crdc.dhApiQuery(crdc_creds['url'],crdc_creds['token'], dq.org_query)
print(list(res.keys()))