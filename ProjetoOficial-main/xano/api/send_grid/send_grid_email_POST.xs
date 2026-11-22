query SendGrid_Email verb=POST {
  api_group = "SendGrid"

  input {
    // Identificação do remetente
    text from filters=trim
  
    // identificação do destinatário
    text to filters=trim
  
    // Assunto do email
    text subject filters=trim
  
    // Conteúdo do email
    text content filters=trim
  }

  stack {
    db.get tokens {
      field_name = "plataforma"
      field_value = "SendGrid"
    } as $tokens1
  
    api.request {
      url = "https://api.sendgrid.com/v3/mail/send"
      method = "POST"
      params = {
        personalizations: [{"to": [ {"email": $input.to}]}]
        from            : {"email": $input.from}
        subject         : $input.subject
        content         : [{"type": "text/plain", "value": $input.content}]
      }
    
      headers = [$tokens1.token, "Content-Type: application/json"]
    } as $api1
  }

  response = {status: `$var.api1.response.status`}
  guid = "EoVM56gn-7edFdscmN8olnMl8w8"
}