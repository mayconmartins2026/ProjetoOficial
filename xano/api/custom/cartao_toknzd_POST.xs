query cartaoToknzd verb=POST {
  api_group = "Custom"

  input {
    text cliente_id? filters=trim
    text token? filters=trim
    text codigoClienteAssas? filters=trim
  }

  stack {
  }

  response = null
  guid = "d9HBJ7YtzfhsTrEZpg_t1Uf8U90"
}