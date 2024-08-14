from odoo import fields, models, api, _


class Student(models.Model):
    _inherit = "hostel.student"

    cabin_id = fields.Many2one("hostel.cabin", string="Cabin",
                               help="Select cabin")


class HostelRoomCopy(models.Model):
    _name = "hostel.cabin"
    _inherit = ["hostel.room", "base.archive"]
    _description = "Hostel Cabin Information"

    hostel_amenities_ids = fields.Many2many("hostel.amenities",
                                            "hostel_cabin_amenities_rel", "cabin_id", "amenitiy_id",
                                            string="Amenities", domain="[('active', '=', True)]",
                                            help="Select hostel cabin amenities")

    student_ids = fields.One2many("hostel.student", "cabin_id",
                                  string="Students", help="Enter students")
