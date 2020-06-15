from marshmallow import Schema, fields

class GameSettings(Schema):
    rows = fields.Int(required=True)
    columns = fields.Int(required=True)
    mines = fields.Int(required=True)
