
const { ApolloError } = require('apollo-server-errors');
const { gql } = require('graphql-tag');
const fetch = require('node-fetch');

const base_url = "https://dat-b.osisoft.com";
const token_url = `${base_url}/identity/connect/token`;
const ocs_url = `${base_url}/api/v1/Tenants/65292b6c-ec16-414a-b583-ce7ae04046d4/namespaces`;

let ocs_jwt = {};
let ocs_jwt_exp = 1;

async function getOCSToken(url) {
   const response = await fetch(url, {
      method: 'POST',
      body: new URLSearchParams({
         'client_id': process.env.OCS_CLIENT_ID || 'none',
         'client_secret': process.env.OCS_CLIENT_SECRET || 'none',
         'grant_type': 'client_credentials',
      })
   });
   console.log("@got fresh OCS token")
   return response.json();
}

async function getToken() {
   let delta = ocs_jwt_exp - Date.now()
   // console.log(`delta: ${delta}`)
    if (delta <= 5*60*1000) {
        ocs_jwt = await getOCSToken(token_url);
        ocs_jwt_exp = Date.now() + 1000*ocs_jwt["expires_in"]
    }
    return ocs_jwt["access_token"]
}

function checkDataviewId(id) {
   if (id === undefined) {
      console.log("@@error: dataview_id not defined (add id field)")
      throw new ApolloError('Add id field to query', 'NO_DATAVIEW_ID');
   }
}

async function customGraphQLError(url, reply) {
   let body = await reply.text();
   console.log(`reply-msg: ${body}`);
   return new ApolloError(`  ${reply.status}:${reply.statusText}.  URL ${String(url)}  OperationId ${reply.headers.get("Operation-Id")}`,
       reply.status,
       {
          reason: reply.statusText,
          message: body,
          headers: reply.headers.raw()
       });
}

async function get_data_view(kind, _source, _args, _context) {
   let url;
   let dv_id_extra;

   checkDataviewId(_source.id);

   if (_args.nextPage) {
      url = new URL(`${_args.nextPage}`);
   } else {
      let params = {
         startIndex: _args.startIndex,
         endIndex: _args.endIndex
      };
      if (kind === "stored") {
         // params["form"] = "tableh";
         dv_id_extra = "_narrow";
      } else {  // "interpolated"
         params["form"] = "csvh";
         params["interval"] = _args.interpolation;
         dv_id_extra = "";
      }
      if (_args.count) {
         params["count"] = _args.count;
      }
      url = new URL(`${ocs_url}/${_args.namespace}/dataviews/${_source.id}${dv_id_extra}/data/${kind}`);
      url.search = new URLSearchParams(params).toString();
   }
   console.log(`url: ${String(url)}`);

   let ocs_token = await getToken();
   let reply = await fetch(url, {
      headers: {
         'Authorization': `Bearer ${ocs_token}`
      }
   });
   console.log(`status: ${reply.status}`);

   if (reply.status === 200) {
      let s = reply.headers.get('link');
      let links = {};
      let re = /<(\S+)>; rel="(\S+)"/g;
      let m;
      do {
         m = re.exec(s);
         if (m) {
            links[m[2]] = m[1];
         }
      } while (m);

      let result;
      if (kind === "stored") {
         result = reply.json()
      } else {
         result = reply.text()
      }
      return {
         nextPage: links["next"],
         data: result,
         firstPage: links["first"]
      }
   } else {
      return await customGraphQLError(url, reply);
   }
}

async function get_data_items(_source, _args, _context) {

   checkDataviewId(_source.id);

   let params = {
      count: "1000",
      cache: "refresh",
   };
   const url = new URL(`${ocs_url}/${_args.namespace}/dataviews/${_source.id}/Resolved/DataItems/${_args.queryId}`);
   url.search = new URLSearchParams(params).toString();

   let ocs_token = await getToken();
   let reply = await fetch(url, {
      headers: {
         'Authorization': `Bearer ${ocs_token}`
      }
   });
   console.log(`status: ${reply.status}`);

   if (reply.status === 200) {
      return reply.json();
   } else {
      let body = await reply.text();
      console.log(`reply-msg: ${body}`);
      return new ApolloError(`  ${reply.status}:${reply.statusText}.  URL ${String(url)}  OperationId ${reply.headers.get("Operation-Id")}`,
          reply.status,
          {
             reason: reply.statusText,
             message: body,
             headers: reply.headers.raw()
          });
   }
}

const resolvers = {
   DataView: {
      stored: async (_source, _args, _context) => await get_data_view("stored", _source, _args, _context),
      interpolated: async (_source, _args, _context) => await get_data_view("interpolated", _source, _args, _context),
      resolvedDataItems: async (_source, _args, _context) => await get_data_items(_source, _args, _context),
   }
};

const typeDefs = gql`

scalar JSON
scalar JSONObject

interface AuthReadOnly @auth(rules: [{operations: [READ], isAuthenticated: true }]) 
   @exclude(operations: [CREATE, UPDATE, DELETE]) {
   id: ID!
}

"""
Database == Hub dataset 
"""

type Database implements AuthReadOnly {
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
 
# extend type Database
#  @auth(rules: [{ operations: [READ], isAuthenticated: true }])

  # @exclude(operations: [CREATE, UPDATE, DELETE])  

"""
AF elements from source PI
"""
type Element implements AuthReadOnly {
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

type StoredResult {
   nextPage: String
   data: JSONObject
   firstPage: String
}

type InterpolatedResult {
   nextPage: String
   data: String
   firstPage: String
}

"""
Asset-centric data view representation
Reference: https://academichub.blob.core.windows.net/hub/Hub_Dataset_Onboarding_Part_1.html
"""
type DataView implements AuthReadOnly {
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
        namespace: String!
        startIndex: String!
        endIndex: String!
        nextPage: String
        count: Int
    ): StoredResult @ignore 
   "interpolated asset stream values"
    interpolated(
        namespace: String!
        startIndex: String!
        endIndex: String!
        interpolation: String!
        nextPage: String
        count: Int
    ): InterpolatedResult @ignore 
   resolvedDataItems(
        namespace: String!
        queryId: String!
   ): JSONObject @ignore 
}
`;

module.exports = { typeDefs, resolvers };
