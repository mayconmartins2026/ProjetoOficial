// Endereço que mostra na tela pagamento
query endereco verb=GET {
  api_group = "Custom"
  auth = "user"

  input {
  }

  stack {
    db.get ENDERECO {
      field_name = "cliente_id"
      field_value = $auth.id
    } as $ENDERECO1
  }

  response = $ENDERECO1
  guid = "8t_VfACwc0TlIl-6JmrT2kHXJm8"
}