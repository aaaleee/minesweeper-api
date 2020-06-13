from marshmallow import Schema, fields

class UserRegistration(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, min=8)
