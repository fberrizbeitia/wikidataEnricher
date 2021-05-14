import requests
import json
import io
import os

def extractEntity(uri):
  parts = uri.split('entity/')
  return(parts[1])

def getWikidataLabels(uri):
  
  entity = extractEntity(uri)
  jsonUri = 'https://www.wikidata.org/wiki/Special:EntityData/'+entity+'.json'
  response = requests.get(jsonUri)
  wdJson = response.json()

  labels = wdJson.get('entities').get(entity).get('labels')

  return labels


def getConcepts(text):
  url = "https://api.dbpedia-spotlight.org/en/candidates?text="+text+"&confidence=0.95"
  headers = {
    'accept': 'application/json'
  }
  response = requests.get(url,headers=headers)
  objJson = response.json()
  candidates = objJson.get('annotation').get('surfaceForm')
  conceptsArray = []

  for candidate in candidates:
    concept = {}
    if not candidate is None:
      concept['label'] = candidate.get('resource').get('@label')
      dbpediaURI = 'http://dbpedia.org/resource/' + candidate.get('resource').get('@uri')
      concept['uri'] = dbpediaURI

      #Dereference dbpedia URI and get the wikidata uri on the under the owl#sameas predicate
      dbpediaJsonURI = 'http://dbpedia.org/data/' + candidate.get('resource').get('@uri') + '.json'
      response2 = requests.get(dbpediaJsonURI)
      dbpediaObj = response2.json()
      dbpediaPredicates = dbpediaObj.get(dbpediaURI).get('http://www.w3.org/2002/07/owl#sameAs')

      wikidata = []
      if not dbpediaPredicates is None:
        for value in dbpediaPredicates:
          wikidataPredicate = {}
          strValue = value.get('value')
          if strValue.count('wikidata.org') > 0 :
            wikidataPredicate['uri'] = strValue
            #get the labels from wikidata
            wikidataPredicate['labels'] = getWikidataLabels(strValue)
            wikidata.append(wikidataPredicate)

      concept['translations'] = wikidata
      


    conceptsArray.append(concept)
  
  return(conceptsArray)

#----------------------------------------------------
path = '3-item.json'
target = 'test-result.json'

with open(path,'r',encoding='utf-8') as jsonfile:

  jsonText = jsonfile.read()
  #iterate on the biblio records
  jsonRecords = json.loads(str(jsonText),strict=False)

  result = []
  for record in jsonRecords.get('@graph'):
    concepts = getConcepts(record.get('description'))
    record['concepts'] = concepts
    result.append(record)

  jsonld = {}
  jsonld["@context"] = "http://schema.org"
  jsonld["graph"] = result

  with open(target, "w") as data_file:
    json.dump(jsonld, data_file, ensure_ascii=False)


