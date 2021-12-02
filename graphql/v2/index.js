const { ApolloServer } = require("apollo-server");
const { Neo4jGraphQL } = require("@neo4j/graphql");

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

const { ApolloServerPluginLandingPageGraphQLPlayground } = require("apollo-server-core")

const server = new ApolloServer({
    schema: neoSchema.schema,
    context: ({ req }) => ({ req }),
    plugins: [
        ApolloServerPluginLandingPageGraphQLPlayground(),
    ],
});

server.listen(4000, "0.0.0.0").then(({ url }) => {
    console.log(`@neo4j/graphql API ready at ${url}`);
});
