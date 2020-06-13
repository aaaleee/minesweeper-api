from marshmallow import Schema, fields

class CellAction(Schema):
    row = fields.Int(required=True)
    column = fields.Int(required=True)
