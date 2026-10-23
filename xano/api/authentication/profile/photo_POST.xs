// Upload and save the authenticated user's public profile photo.
query "profile/photo" verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    file? img_perfil
  }

  stack {
    storage.create_image {
      value    = $input.img_perfil
      access   = "public"
      filename = $input.img_perfil.name
    } as $profile_image

    db.edit user {
      field_name = "id"
      field_value = $auth.id
      data = {
        img_perfil: $profile_image
      }
      output = ["id", "name", "img_perfil"]
    } as $user
  }

  response = $user
  guid = "h1Q9dGBIEHkAMrH2zYno2FySFtE"
}
