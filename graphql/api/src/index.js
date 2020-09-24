import { typeDefs } from './graphql-schema'
import { ApolloServer } from 'apollo-server-express'
import express from 'express'
import neo4j from 'neo4j-driver'
import { makeAugmentedSchema } from 'neo4j-graphql-js'
import dotenv from 'dotenv'
import { initializeDatabase } from './initialize'

// set environment variables from .env
dotenv.config()

const app = express()

/*
 * Create an executable GraphQL schema object from GraphQL type definitions
 * including autogenerated queries and mutations.
 * Optionally a config object can be included to specify which types to include
 * in generated queries and/or mutations. Read more in the docs:
 * https://grandstack.io/docs/neo4j-graphql-js-api.html#makeaugmentedschemaoptions-graphqlschema
 */

const schema = makeAugmentedSchema({
  typeDefs,
  config: {
    mutation: process.env.GRAPHQL_MUTATION || false
  },
//  config: {
//    query: {
//      exclude: ['RatingCount'],
//    },
//    mutation: {
//      exclude: ['RatingCount'],
//   },
})

/*
 * Create a Neo4j driver instance to connect to the database
 * using credentials specified as environment variables
 * with fallback to defaults
 */
const driver = neo4j.driver(
  process.env.NEO4J_URI || 'bolt://localhost:7687',
  neo4j.auth.basic(
    process.env.NEO4J_USER || 'neo4j',
    process.env.NEO4J_PASSWORD || 'neo4j'
  ),
  {
    encrypted: process.env.NEO4J_ENCRYPTED ? 'ENCRYPTION_ON' : 'ENCRYPTION_OFF',
  }
)

/*
 * Perform any database initialization steps such as
 * creating constraints or ensuring indexes are online
 *
 */
const init = async (driver) => {
  await initializeDatabase(driver)
}

/*
 * We catch any errors that occur during initialization
 * to handle cases where we still want the API to start
 * regardless, such as running with a read only user.
 * In this case, ensure that any desired initialization steps
 * have occurred
 */

init(driver)

/*
 * Create a new ApolloServer instance, serving the GraphQL schema
 * created using makeAugmentedSchema above and injecting the Neo4j driver
 * instance into the context object so it is available in the
 * generated resolvers to connect to the database.
 */
const server = new ApolloServer({
  context: { driver, neo4jDatabase: process.env.NEO4J_DATABASE },
  schema: schema,
  introspection: true,
  playground: true,
  engine: {
    apiKey: process.env.APOLLO_KEY || "none",
    graphVariant: process.env.APOLLO_GRAPH_VARIANT || "production"
  }
})

// Specify host, port and path for GraphQL endpoint
const port = process.env.GRAPHQL_SERVER_PORT || 4000
const path = process.env.GRAPHQL_SERVER_PATH || '/graphql'
const host = process.env.GRAPHQL_SERVER_HOST || '0.0.0.0'

/*
 * Optionally, apply Express middleware for authentication, etc
 * This also also allows us to specify a path for the GraphQL endpoint
 */
server.applyMiddleware({ app, path })

app.listen({ host, port, path }, () => {
  console.log(`GraphQL server ready at http://${host}:${port}${path}`)
})


