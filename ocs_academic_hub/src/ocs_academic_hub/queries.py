

# Database alias to match previous file format
q_datasets = """
query datasets($status: String) {
  Database: databases(
    where: { OR: [{ status: "production" }, { status: $status }] }
    options: { sort: [{ name: ASC }] }
  ) {
    name
    asset_db
    description
    informationURL
    status
    namespace
    version
    id
    asset_with_dv(options: { sort: [{ name: ASC }] }) {
      name
      asset_id
      description
      asset_metadata
      has_dataview(
        where: { ocs_sync: true }
        options: { sort: [{ name: ASC }] }
      ) {
        name
        description
        id
        asset_id
        columns
        ocs_column_key
      }
    }
  }
}
"""

q_stored = """
query stored(
  $id: ID
  $namespace: String!
  $startIndex: String!
  $endIndex: String!
  $nextPage: String
  $count: Int
) {
  dataview: dataViews(where: { id: $id }) {
    id
    data: stored(
      namespace: $namespace
      startIndex: $startIndex
      endIndex: $endIndex
      nextPage: $nextPage 
      count: $count
    ) {
      nextPage
      data
      firstPage
    }
  }
}
"""

q_interpolated = """
query interpolated(
  $id: ID
  $namespace: String!
  $startIndex: String!
  $endIndex: String!
  $interpolation: String!
  $nextPage: String
  $count: Int
) {
  dataview: dataViews(where: { id: $id }) {
    id
    data: interpolated(
      namespace: $namespace
      startIndex: $startIndex
      endIndex: $endIndex
      interpolation: $interpolation
      nextPage: $nextPage
      count: $count
    ) {
      nextPage
      data
      firstPage
    }
  }
}
"""
q_resolved = """
query resolvedDataItems($id: ID, $namespace: String!, $queryId: String!) {
  dataview: dataViews(where: { id: $id }) {
    id
    resolvedDataItems(namespace: $namespace, queryId: $queryId)
  }
}
"""

q_streams = """
query getStreams($namespace: ID!, $query: String, $skip: Int, $count: Int) {
    namespaces(where: { id: $namespace }) {
      id
      streams: getStreams(query: $query, skip: $skip, count: $count)
  }
}
"""

q_stream = """
query getStream($namespace: ID!, $stream_id: String!) {
    namespaces(where: { id: $namespace }) {
      id
      stream: getStream(stream_id: $stream_id)
      metadata(stream_id: $stream_id)
      tags(stream_id: $stream_id)
  }
}
"""

q_stream_data = """
query getWindowValues(
  $namespace: ID!
  $stream_id: String!
  $start: String!
  $end: String!
) {
  namespaces(where: { id: $namespace }) {
    id
    data: getWindowValues(stream_id: $stream_id, start: $start, end: $end)
  }
}
"""

q_stream_interpolated = """
query getInterpolatedValues(
  $namespace: ID!
  $stream_id: String!
  $start: String!
  $end: String!
  $count: Int!
) {
  namespaces(where: { id: $namespace }) {
    id
    data: getInterpolatedValues(stream_id: $stream_id, start: $start, end: $end, count: $count)
  }
}
"""

q_stream_ends = """
query getFirstLastValues(
  $namespace: ID!
  $stream_id: String!
) {
  namespaces(where: { id: $namespace }) {
    id
    first: getFirstValue(stream_id: $stream_id)
    last: getLastValue(stream_id: $stream_id)
  }
}
"""

q_endpoint_check = """
query { 
  databases(where: {name: "Wind_Farms"}) {
    name
  }
}
"""