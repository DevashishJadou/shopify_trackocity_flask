from marshmallow import fields, Schema

class FB(Schema):
	id = fields.String()
	complete_name = fields.String()
	email = fields.String()
	phone = fields.String()
	workspace = fields.String()
	# created_at = fields.TimeDelta()