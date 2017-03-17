from UtilString import *
from UtilTime import *


class ARAuditTrail:
    entry_id = None
    to_value = None
    from_value = None
    audit_create_date = None
    attribute_label = None
    product_release = None
    product_family = None

    def __init__(self,entry_id,to_value,from_value,audit_create_date,attribute_label,product_release,product_family):
        self.entry_id = entry_id
        self.to_value = to_value
        self.from_value = from_value
        self.audit_create_date = audit_create_date
        self.attribute_label = attribute_label
        self.product_release = product_release
        self.product_family = product_family


def generate_audit_trail_obj(auditTrail):
    strer = StringHelper()
    timer = TimeHelper()
    for k,v in auditTrail[1].iteritems():
        if k == 536870921:
            entry_id = strer.str_exclude_pre_zero(v)
        elif k == 536870917:
            to_value = v
        elif k == 536870916:
            from_value = v
        elif k == 536870929:
            audit_create_date = timer.mtime_to_local_date(v)
        elif k == 536870925:
            attribute_label = v
        elif k == 536870940:
            product_release = v
        elif k == 536871628:
            product_family = v
    return ARAuditTrail(entry_id,to_value,from_value,audit_create_date,attribute_label,product_release,product_family)


def filter_by_realse(objlist, release):
    res = list()
    for o in objlist:
        if o.product_release == release:
            res.append(o)
    return res



