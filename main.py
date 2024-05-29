import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef, XSD
from rdflib.plugins.sparql import prepareQuery

# Read the CSV file into a DataFrame
df = pd.read_csv('top_10000_1960-now.csv')

# Define namespaces
ex = Namespace("https://open.spotify.com/")
ns = Namespace("http://example.com/ontology#")

# Create an RDF graph
g = Graph()

from rdflib import URIRef

# Define a function to modify URIs
# Define a function to modify URIs
# Define a function to modify URIs
def modify_uri(uri):
    # Check if the value is NaN
    if pd.isna(uri):
        # Return a default value or handle it as you prefer
        return "unknown"
    else:
        # Split the URI string by comma and take the first URI
        first_uri = uri.split(',')[0]
        # Apply modifications to the first URI
        modified_uri = first_uri.replace("spotify:", "").replace(":", "/")
        # Return the modified URI
        return modified_uri



# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    # Create modified URIs for track, artist, and album
    modified_track_uri = URIRef(ex + modify_uri(row['Track URI']))
    modified_artist_uri = URIRef(ex + modify_uri(row['Artist URI(s)']))
    modified_album_uri = URIRef(ex + modify_uri(row['Album URI']))

    # Add triples for track, artist, and album using modified URIs
    g.add((modified_track_uri, RDF.type, ns.Track))
    g.add((modified_track_uri, ns.trackName, Literal(row['Track Name'])))
    g.add((modified_track_uri, ns.artist, modified_artist_uri))
    g.add((modified_track_uri, ns.album, modified_album_uri))
    g.add((modified_track_uri, ns.diskNumber, Literal(row['Disc Number'], datatype=XSD.integer)))
    g.add((modified_track_uri, ns.trackNumber, Literal(row['Track Number'], datatype=XSD.integer)))
    g.add((modified_track_uri, ns.copyright, Literal(row['Copyrights'])))

    g.add((modified_artist_uri, RDF.type, ns.Artist))
    g.add((modified_artist_uri, ns.artistName, Literal(row['Artist Name(s)'])))

    g.add((modified_album_uri, RDF.type, ns.Album))
    g.add((modified_album_uri, ns.albumName, Literal(row['Album Name'])))
    g.add((modified_album_uri, ns.albumArtist, URIRef(ex + modify_uri(row['Album Artist URI(s)']))))
    g.add((modified_album_uri, ns.albumArtistName, Literal(row['Album Artist Name(s)'])))


# Serialize the graph (optional)
print(g.serialize(format='turtle'))

# SPARQL query to retrieve AlbumArtistName for "Illuminate (Deluxe)"
query = prepareQuery(
    """
    SELECT ?albumArtistName
    WHERE {
      ?album rdf:type ns:Album .
      ?album ns:albumName "Illuminate (Deluxe)" .
      ?album ns:albumArtistName ?albumArtistName .
    }
    """,
    initNs={"rdf": RDF, "ns": ns}
)

# Execute the SPARQL query
for row in g.query(query):
    print(row)


