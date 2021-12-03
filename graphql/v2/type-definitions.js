
const { ApolloError } = require('apollo-server-errors');
const { gql } = require("apollo-server");
const fetch = require('node-fetch');


const base_url = "https://dat-b.osisoft.com/api/v1/Tenants/65292b6c-ec16-414a-b583-ce7ae04046d4/namespaces";

const resolvers = {
   DataView: {
      stored: async (source, args) => {
         console.log(source);
         console.log(`args: ${args}`);
         console.log(args);

         if (source.id === undefined) {
            console.log("@@error: dataview_id not defined (add id field)")
            throw new ApolloError('Add id field to query', 'NO_DATAVIEW_ID'); // , myCustomExtensions);
         }

         if (args.nextPage) {
            var url = new URL(args.nextPage);
         } else {
            var url = new URL(`${base_url}/${args.namespace}/dataviews/${source.id}_narrow/data/stored`);

            let params = {
               startIndex: args.startIndex,
               endIndex: args.endIndex,
               form: "tableh",
            };

            if (args.count) {
               params["count"] = args.count;
            }

            url.search = new URLSearchParams(params).toString();
         }
         console.log(`url: ${String(url)}`);

         var reply = await fetch(url, {
            headers: {
               'Authorization': `Bearer ${args.token}`
            }
         });
         console.log(`status: ${reply.status}`);
         // || ${(0, _stringify.default)(reply.headers.raw())}`);

         if (reply.status == 200) {
            // console.log(`headers: ${reply.headers.get('link')}`);
            var s = reply.headers.get('link');
            var links = {};
            var re = /<(\S+)>; rel=\"(\S+)\"/g;
            var m;

            do {
               m = re.exec(s);
               if (m) {
                  // console.log(m[1], m[2])
                  links[m[2]] = m[1];
               }
            } while (m);

            return [links["next"], reply.text(), links["first"]];
         } else {
            return new ApolloError(`  ${reply.status}:${reply.statusText}.  URL ${String(url)}  OperationId ${reply.headers.get("Operation-Id")}`, reply.status,
                {
                   reason: reply.statusText,
                   headers: reply.headers.raw()
                });
         }
         // return ["0,1,2,3", "first-url", "next-url"];
      }
   }
};

const typeDefs = gql`
# """
# An object with a Globally Unique ID
# """
# interface Node {
#   # The ID of the object.
#   id: ID!
# }

extend type Database
  @auth(rules: [{ operations: [READ], isAuthenticated: true }])
  @exclude(operations: [CREATE, UPDATE, DELETE])  

"""
Database == Hub dataset 
"""
type Database {
   "pseudo-PI WebID"
   id: ID!
   "OCS metadata for dataset id"
   asset_db: String!
   "short description of the dataset"
   description: String
   "nice name - unused"
   display_name: String
   "for reference information"
   informationURL: String
   "dataset name"
   name: String!
   "OCS namespace for dataset streams"
   namespace: String
   "standard status are: production, onboarding"
   status: String
   "convention: last dataset update date"
   version: String
   "start and end time for dataset"
   timeRange: String 
   "top AF elements/assets"
   has_element: [Element] @relationship(type: "HAS_ELEMENT", direction: OUT)
   "all assets (elements) with data views are linked here"
   asset_with_dv: [Element] @relationship(type: "ASSET_WITH_DV", direction: OUT)
    
   # "source PI server node"
   # servers: [Server] @relation(name: "HAS_DATABASE", direction: "IN")
   # "extracted AF template - unused"
   # af_template: String!
   "all assets (elements) with no children element"
   leaf_elements: [Element]! @cypher (statement: "MATCH (this)-[:HAS_ELEMENT*]->(e:Element) WHERE NOT ((e)-[:HAS_ELEMENT]->()) RETURN DISTINCT e ORDER BY e.name")
}
 
#extend type Database
#  @auth(rules: [{ operations: [READ], roles: ["hub:readd"] }])

# extend type Database @auth(rules: [{ isAuthenticated: true }])
# extend type Database @auth(rules: [{ allowUnauthenticated: true }])

"""
AF elements from source PI
"""
type Element @exclude(operations: [CREATE, UPDATE, DELETE]) {
   # "(internal database use)"
   # _id: Long!
   "asset identifier - from AF => OCS metadata"
   asset_id: String
   "extracted AF template"
   af_template: String!
   "OCS metadata for dataset id"
   asset_db: String!
   "Web ID"
   id: ID!
   "element name from AF"
   name: String!
   "element description from AF"
   description: String
   "list of static attributes for element"
   static_attributes: [String]
   "serialized dictionary built from static_attributes"
   asset_metadata: String
   "latitude (if present, otherwise null)"
   latitude: Float
   "longitude (if present, otherwise null)"
   longitude: Float
   "compound field with lat/long"
   location: Point
   "child AF elements"
   has_element: [Element] @relationship(type: "HAS_ELEMENT", direction: OUT)
   # "dynamic attributes (PIPoint) of element"
   # has_dynamic: [PIPoint] @relation(name: "HAS_DYNAMIC", direction: "OUT")
   # "static attributes (configuration data) of element"
   # has_attribute: [Attribute] @relation(name: "HAS_ATTRIBUTE", direction: "OUT")
   "data view object representation"
   has_dataview: [DataView] @relationship(type: "HAS_DATAVIEW", direction: OUT)
   # "if element has at least one data view, this link exists"
   databases: [Database] @relationship(type: "ASSET_WITH_DV", direction: IN)
   "parent element(s)"
   has_parent: [Element] @relationship(type: "HAS_ELEMENT", direction: IN)
}
   
"""
Asset-centric data view representation
Reference: https://academichub.blob.core.windows.net/hub/Hub_Dataset_Onboarding_Part_1.html
"""
type DataView @exclude(operations: [CREATE, UPDATE, DELETE]) {
   # "(internal database use)"
   # _id: Long!
   "data view identifier"
   id: ID!
   "OCS metadata for dataset identifier"
   asset_db: String!
   "all assets referenced by the data view"
   asset_id: [String]!
   "list of columns headers"
   columns: String!
   "short data view description"
   description: String
   "short name for the data view"
   name: String!
   "indicates this data view has been mapped on OCS"
   ocs_sync: Boolean!
   "associated OCS tag"
   ocs_tag: String!
   "to come"
   ocs_column_key: String
   # "streams associated to the data view"
   # has_stream: [PIPoint] @relation(name: "HAS_STREAM", direction: "OUT")
   "assets this data views is associated with"
   elements: [Element] @relationship(type: "HAS_DATAVIEW", direction: IN)
    "stored asset stream values"
    stored(
        token: String! 
        namespace: String!
        startIndex: String!
        endIndex: String!
        nextPage: String
        count: Int
    ): [String]! @ignore 
}
`;

module.exports = { typeDefs, resolvers };
