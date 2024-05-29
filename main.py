import pandas as pd
import requests
from rdflib import Graph, Namespace, RDF, Literal, URIRef, XSD
from rdflib.namespace import DC
from rdflib.plugins.sparql import prepareQuery

# Load the ontology graph
g = Graph()
url = "https://raw.githubusercontent.com/motools/musicontology/master/rdf/musicontology.rdfs"

try:
    response = requests.get(url)
    g.parse(data=response.text, format="xml")
    print("Graph loaded successfully!")
except Exception as e:
    print("Error loading the RDF graph:", e)

print("Number of triples in the graph:", len(g))

# Print a sample of the graph to verify
for s, p, o in list(g)[:10]:  # Print only the first 10 triples
    print(s, p, o)

# Read the CSV file into a DataFrame
df = pd.read_csv('top_10000_1960-now.csv')

# Define namespaces
ex = Namespace("https://open.spotify.com/")
mo = Namespace("http://purl.org/ontology/mo/")  # Music Ontology

# Bind namespaces to the graph
g.bind("ex", ex)
g.bind("mo", mo)

# Define a function to modify URIs
def modify_uri(uri):
    if pd.isna(uri):
        return "unknown"
    else:
        first_uri = uri.split(',')[0]
        modified_uri = first_uri.replace("spotify:", "").replace(":", "/")
        return modified_uri

# Iterate over each row in CSV
for index, row in df.iterrows():
    # Create modified URIs for track, artist, and album
    modified_track_uri = URIRef(ex + modify_uri(row['Track URI']))
    modified_artist_uri = URIRef(ex + modify_uri(row['Artist URI(s)']))
    modified_album_uri = URIRef(ex + modify_uri(row['Album URI']))
    modified_album_artist_uri = URIRef(ex + modify_uri(row['Album Artist URI(s)']))

    # Add triples for track using modified URIs
    g.add((modified_track_uri, RDF.type, mo.Track))
    g.add((modified_track_uri, mo.track_number, Literal(row['Track Number'], datatype=XSD.integer)))
    g.add((modified_track_uri, mo.trackName, Literal(row['Track Name'])))
    g.add((modified_track_uri, mo.performer, modified_artist_uri))
    g.add((modified_track_uri, mo.record, modified_album_uri))
    g.add((modified_track_uri, mo.diskNumber, Literal(row['Disc Number'], datatype=XSD.integer)))
    g.add((modified_track_uri, mo.rights, Literal(row['Copyrights'])))
    g.add((modified_track_uri, ex.loudness, Literal(row['Loudness'], datatype=XSD.float)))
    g.add((modified_track_uri, ex.speechiness, Literal(row['Speechiness'], datatype=XSD.float)))
    g.add((modified_track_uri, ex.acousticness, Literal(row['Acousticness'], datatype=XSD.float)))
    g.add((modified_track_uri, ex.instrumentalness, Literal(row['Instrumentalness'], datatype=XSD.float)))
    g.add((modified_track_uri, ex.energy, Literal(row['Energy'], datatype=XSD.float)))
    g.add((modified_track_uri, ex.danceability, Literal(row['Danceability'], datatype=XSD.float)))
    g.add((modified_track_uri, ex.liveness, Literal(row['Liveness'], datatype=XSD.float)))

    # Add triples for artist using modified URIs
    g.add((modified_artist_uri, RDF.type, mo.MusicArtist))
    g.add((modified_artist_uri, mo.name, Literal(row['Artist Name(s)'])))

    # Add triples for album using modified URIs
    g.add((modified_album_uri, RDF.type, mo.Release))
    g.add((modified_album_uri, mo.title, Literal(row['Album Name'])))
    g.add((modified_album_uri, mo.performer, modified_album_artist_uri))
    g.add((modified_album_uri, mo.name, Literal(row['Album Artist Name(s)'])))


# Save the updated graph to a file (optional)
g.serialize(destination="updated_musicontology.rdf", format="xml")

print("Data added to the RDF graph successfully!")

# SPARQL query to retrieve AlbumArtistName for "First Of All"
query = prepareQuery(
    """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX mo: <http://purl.org/ontology/mo/>

    SELECT ?albumArtistName
    WHERE {
      ?album rdf:type mo:Release .
      ?album mo:title "First Of All" .
      ?album mo:performer ?albumArtist .
      ?albumArtist mo:name ?albumArtistName .
    }
    """,
    initNs={"rdf": RDF, "mo": mo}
)

# Execute the SPARQL query
print("The artist: ")
for row in g.query(query):
    album_artist_name = row.albumArtistName  # Access the albumArtistName from the result row
    print(album_artist_name)

# SPARQL query to retrieve track names from the "First Of All" album
query = prepareQuery(
    """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX mo: <http://purl.org/ontology/mo/>

    SELECT ?trackName
    WHERE {
      ?track rdf:type mo:Track .
      ?track mo:trackName ?trackName .
      ?track mo:record ?album .
      ?album mo:title "First Of All" .
    }
    """,
    initNs={"rdf": RDF, "mo": mo}
)

print("The tracks: ")
# Execute the SPARQL query
for row in g.query(query):
    track_name = row.trackName  # Access the trackName from the result row
    print(track_name)

# SPARQL query to retrieve the name of the artists of the first 5 most lively tracks
query = prepareQuery(
    """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX mo: <http://purl.org/ontology/mo/>
    PREFIX ex: <https://open.spotify.com/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT ?artistName ?trackName ?liveness
    WHERE {
      ?track rdf:type mo:Track .
      ?track mo:trackName ?trackName .
      ?track ex:liveness ?liveness .
      ?track mo:performer ?artist .
      ?artist mo:name ?artistName .
    }
    ORDER BY DESC(xsd:float(?liveness))
    LIMIT 3
    """,
    initNs={"rdf": RDF, "mo": mo, "ex": ex, "xsd": XSD}
)

# Execute the SPARQL query
print("The first 3 most lively tracks and their artists: ")
for row in g.query(query):
    artist_name = row.artistName
    track_name = row.trackName
    liveness = row.liveness
    print(f"Artist: {artist_name}, Track: {track_name}, Liveness: {liveness}")
