
from Products.CMFCore.utils import getToolByName

def ATReferenceAdapter(context, field):
    relationship = field.relationship
    uid_catalog = getToolByName(context, 'uid_catalog')
    uids = context.request.form.get(field.getName(), list())
    objs = list()
    if type(uids) not in (list, tuple):
        uids = [uids]
    for uid in uids:
        if not uid:
            continue
        res = uid_catalog(UID=uid)
        if res:
            objs.append(res[0].getObject())
    if not objs:
        objs = [item.getTargetObject()
                for item in context.getReferenceImpl(relationship)]
    return objs

def ATBackReferenceAdapter(context, field):
    relationship = field.relationship
    return [item.getTargetObject()
            for item in context.getBackReferenceImpl(relationship)]

def PloneRelationsAdapter(context, field):
    relationship = field.relationship
    from plone.app.relations.interfaces import IRelationshipSource
    return IRelationshipSource(context).getTargets(relation=relationship)


def PloneRelationsRevAdapter(context, field):
    relationship = field.relationship
    from plone.app.relations.interfaces import IRelationshipTarget
    return IRelationshipTarget(context).getSources(relation=relationship)

