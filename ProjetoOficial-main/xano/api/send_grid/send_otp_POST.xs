query send_otp verb=POST {
  api_group = "SendGrid"

  input {
    text name? filters=trim
    email email? filters=trim|lower
  }

  stack {
    db.get user {
      field_name = "email"
      field_value = $input.email
    } as $user1
  
    conditional {
      if ($user1 == null) {
        db.add user {
          data = {name: $input.name, email: $input.email}
        } as $user1
      }
    }
  
    security.random_number {
      min = 100000
      max = 999999
    } as $otp_gerado
  
    db.edit user {
      field_name = "id"
      field_value = $user1.id
      data = {
        name          : $input.name
        email         : $input.email
        otp_code      : $otp_gerado
        otp_expires_at: now|add_secs_to_timestamp:600
      }
    } as $user1
  
    function.run sendgrid_basic_send {
      input = {
        to_email: $input.email
        subject : "\"Código de Verificação - Sabor Local\""
        body    : `"Olá! Seu código de verificação é: " + otp_gerado.`|to_text
      }
    } as $func1
  }

  response = $user1
  guid = "ddcvkc55fcGg7cNk6M1aWEleuNk"
}