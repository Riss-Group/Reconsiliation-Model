import operator as py_operator

from odoo import _, api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"
    _order = "sequence, code, id"

    @api.depends("bom_line_ids.bom_id", "product_id", "product_tmpl_id")
    def _compute_parent_bom_ids(self):
        for bom in self:
            parent_bom_line_ids = self.env["mrp.bom.line"]._bom_line_find(
                product_tmpl=bom.product_id.product_tmpl_id or bom.product_tmpl_id,
                product=bom.product_id,
            )
            if parent_bom_line_ids:
                bom.parent_bom_ids = parent_bom_line_ids.bom_id
                bom.has_parent = True
            else:
                bom.parent_bom_ids = False
                bom.has_parent = False

    @api.depends("bom_line_ids.bom_id", "bom_line_ids.product_id")
    def _compute_child_bom_ids(self):
        for bom in self:
            bom_line_ids = bom.bom_line_ids
            bom.child_bom_ids = bom_line_ids.child_bom_id

    child_bom_ids = fields.One2many("mrp.bom", "child_m2m_bom", compute="_compute_child_bom_ids", store=True,
                                    readonly=False)
    child_m2m_bom = fields.Many2one("mrp.bom")
    parent_bom_ids = fields.One2many("mrp.bom", compute="_compute_parent_bom_ids")


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    has_bom = fields.Boolean(
        string="Has sub BoM",
        compute="_compute_child_bom_id",
    )
    child_bom_id = fields.Many2one(
        'mrp.bom', 'Sub BoM', compute='_compute_child_bom_id1')

    @api.depends('product_id', 'bom_id')
    def _compute_child_bom_id1(self):
        print('------_compute_child_bom_id1-------')
        products = self.product_id
        bom_by_product = self.env['mrp.bom']._bom_find(products)
        bom = []
        original_bom = False
        for line in self:
            original_bom = line.bom_id
            if not line.product_id:
                line.child_bom_id = False
            else:
                line.child_bom_id = bom_by_product.get(line.product_id, False)
                res_bom = bom_by_product.get(line.product_id, False)

                if res_bom:
                    bom.append(res_bom.id)
        if bom:
            original_bom.child_bom_ids = [(6, 0, bom)]

    @api.depends("product_id", "bom_id")
    def _compute_child_bom_id(self):
        res = super()._compute_child_bom_id()
        for line in self:
            line.has_bom = bool(line.child_bom_id)
        return res
