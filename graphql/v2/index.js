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
const bodyParser = require('body-parser')

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


async function startApolloServer() {
    const app = express()
    const httpServer = http.createServer(app);

    const server = new ApolloServer({
        schema: neoSchema.schema,
        context: ({req}) => ({req}),
        plugins: [
            ApolloServerPluginLandingPageGraphQLPlayground(),
            ApolloServerPluginDrainHttpServer({httpServer}),
            ApolloServerPluginInlineTrace,
        ],
    });

    await server.start();

    // Mount Apollo middleware here.
    server.applyMiddleware({app, path: graphql_path});
    app.use(bodyParser.json({limit: '50mb'}));
    await new Promise(resolve => httpServer.listen({port: 4000, host: "0.0.0.0"}, resolve));
    console.log(`@neo4j/graphql API ready at http://0.0.0.0:4000${graphql_path}`);
    return {server, app};
}

startApolloServer().then();

