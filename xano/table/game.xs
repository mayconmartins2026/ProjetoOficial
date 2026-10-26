// Stores the game identity and display details received from RAWG.
table game {
  auth = false

  schema {
    int id
    timestamp created_at?=now {
      visibility = "private"
    }

    int external_api_id
    text title filters=trim|min:1
    text cover_url?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "external_api_id", op: "asc"}]}
  ]
}
