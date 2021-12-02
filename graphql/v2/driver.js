const neo4j = require("neo4j-driver");

const driver = neo4j.driver("bolt://neo4jcore00.westus.cloudapp.azure.com:7687", neo4j.auth.basic("piuser", "piuser"));

module.exports = driver;