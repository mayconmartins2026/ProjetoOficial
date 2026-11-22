function sendgrid_basic_send {
  input {
    email to_email? filters=trim|lower
    text subject? filters=trim
    text body? filters=trim
  }

  stack {
  }

  response = null
  guid = "q0_HmA9nW2L3eAhMvrsUxR1qZWs"
}