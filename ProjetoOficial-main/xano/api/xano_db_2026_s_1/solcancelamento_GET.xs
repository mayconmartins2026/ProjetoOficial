// Query all SOLCANCELAMENTO records
query solcancelamento verb=GET {
  api_group = "XANO_DB_2026_S1"

  input {
  }

  stack {
    db.query SOLCANCELAMENTO {
      return = {type: "list"}
    } as $solcancelamento
  }

  response = $solcancelamento
  guid = "-Ai-T8fGEt4B12D3dZ_kzzSLLD4"
}