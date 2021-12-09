const { ApolloServer } = require("apollo-server-express");
const { Neo4jGraphQL } = require("@neo4j/graphql");
const express = require("express");
const http = require('http');
const fetch = require('node-fetch');
const {
    ApolloServerPluginLandingPageGraphQLPlayground,
    ApolloServerPluginDrainHttpServer,
    ApolloServerPluginInlineTrace,
} = require("apollo-server-core")

const dotenv = require("dotenv")
dotenv.config()

const { typeDefs, resolvers } = require("./type-definitions");
const driver = require("./driver");

const neoSchema = new Neo4jGraphQL({
    typeDefs,
    resolvers,
    driver,
    config: {
        jwt: {
            jwksEndpoint: "https://dev-f0ejox1i.auth0.com/.well-known/jwks.json",
            rolesPath: "https://data.academic.osisoft.com/roles",
            noVerify: false,
        }
    }
});

const graphql_path = "/graphql2"
const base_url = "https://dat-b.osisoft.com";
const token_url = `${base_url}/identity/connect/token`;
const ocs_hub_url = `${base_url}/api/v1/Tenants/65292b6c-ec16-414a-b583-ce7ae04046d4/namespaces`;

async function getToken(url) {
   const response = await fetch(url, {
      method: 'POST',
      body: new URLSearchParams({
         'client_id': process.env.OCS_CLIENT_ID || 'none',
         'client_secret': process.env.OCS_CLIENT_SECRET || 'none',
         'grant_type': 'client_credentials',
      })
   });
   // console.log(`gt: ${await response.json()}`);
   return response.json();
}

async function startApolloServer() {
    const app = express()
    const httpServer = http.createServer(app);

    console.log("get OCS token...");
    let ocs_token = await getToken(token_url);
    console.log(`ocs-token: ${ocs_token["access_token"]}`);

    const server = new ApolloServer({
        schema: neoSchema.schema,
        // context: ({req}) => ({req}),
        context: ({req}) => (Object.assign(req, {
            ocs_token: ocs_token["access_token"],
            ocs_url: ocs_hub_url
        })),
        plugins: [
            ApolloServerPluginLandingPageGraphQLPlayground(),
            ApolloServerPluginDrainHttpServer({httpServer}),
            ApolloServerPluginInlineTrace,
        ],
    });

    await server.start();

    // Mount Apollo middleware here.
    server.applyMiddleware({app, path: graphql_path});
    await new Promise(resolve => httpServer.listen({port: 4000, host: "0.0.0.0"}, resolve));
    console.log(`@neo4j/graphql API ready at http://0.0.0.0:4000${graphql_path}`);
    return {server, app};
}

startApolloServer().then();

