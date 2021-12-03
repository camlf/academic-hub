const { ApolloServer } = require("apollo-server-express");
const { Neo4jGraphQL } = require("@neo4j/graphql");
const express = require("express");
const http = require('http');

const driver = require("./driver");
const typeDefs = require("./type-definitions");

const neoSchema = new Neo4jGraphQL({
    typeDefs,
    driver,
    config: {
        jwt: {
            jwksEndpoint: "https://dev-f0ejox1i.auth0.com/.well-known/jwks.json",
            rolesPath: "https://data.academic.osisoft.com/roles",
            noVerify: false,
        }
    }
});

const { ApolloServerPluginLandingPageGraphQLPlayground, ApolloServerPluginDrainHttpServer} = require("apollo-server-core")

const path = "/graphql2"

async function startApolloServer() {
    const app = express()
    const httpServer = http.createServer(app);
    const server = new ApolloServer({
        schema: neoSchema.schema,
        context: ({req}) => ({req}),
        plugins: [
            ApolloServerPluginLandingPageGraphQLPlayground(),
            ApolloServerPluginDrainHttpServer({httpServer})
        ],
    });

    await server.start();

    // Mount Apollo middleware here.
    server.applyMiddleware({app, path: path});
    await new Promise(resolve => httpServer.listen({port: 4000, host: "0.0.0.0"}, resolve));
    console.log(`@neo4j/graphql API ready at http://0.0.0.0:4000${path}`);
    return {server, app};
}

startApolloServer().then();

// server.applyMiddleware(app, "graphql2")
// server.listen({port: 4000, host: "0.0.0.0"}).then(({ url }) => {
//    console.log(`@neo4j/graphql API ready at ${url}`);
// });
