"""
    Monkey patch ReferenceField to support reordering.
    
    ReferenceField uses external ReferenceStorage engine to store references.
    Unfortunately reference engine has not been designed for reference shuffling.
    
    We need to clear references on every save and readd them in the order we want to have.

"""
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.config import REFERENCE_CATALOG

from types import ListType, TupleType, ClassType, FileType
from types import StringType, UnicodeType, BooleanType

from Products.Archetypes.Field import ReferenceField, ObjectField

STRING_TYPES = [StringType, UnicodeType]
    
def set(self, instance, value, **kwargs):
    """Mutator.

    ``value`` is a either a list of UIDs or one UID string, or a
    list of objects or one object to which I will add a reference
    to. None and [] are equal.

    >>> for node in range(3):
    ...     _ = self.folder.invokeFactory('Refnode', 'n%s' % node)

    Use set with a list of objects:

    >>> nodes = self.folder.n0, self.folder.n1, self.folder.n2
    >>> nodes[0].setLinks(nodes[1:])
    >>> nodes[0].getLinks()
    [<Refnode...>, <Refnode...>]

    Use it with None or () to delete references:

    >>> nodes[0].setLinks(None)
    >>> nodes[0].getLinks()
    []

    Use a list of UIDs to set:
    
    >>> nodes[0].setLinks([n.UID() for n in nodes[1:]])
    >>> nodes[0].getLinks()
    [<Refnode...>, <Refnode...>]
    >>> nodes[0].setLinks(())
    >>> nodes[0].getLinks()
    []

    Setting multiple values for a non multivalued field will fail:
    
    >>> nodes[1].setLink(nodes)
    Traceback (most recent call last):
    ...
    ValueError: Multiple values ...

    Keyword arguments may be passed directly to addReference(),
    thereby creating properties on the reference objects:
    
    >>> nodes[1].setLink(nodes[0].UID(), foo='bar', spam=1)
    >>> ref = nodes[1].getReferenceImpl()[0]
    >>> ref.foo, ref.spam
    ('bar', 1)

    Empty BTreeFolders work as values (#1212048):

    >>> _ = self.folder.invokeFactory('SimpleBTreeFolder', 'btf')
    >>> nodes[2].setLink(self.folder.btf)
    >>> nodes[2].getLink()
    <SimpleBTreeFolder...>
    """
    tool = getToolByName(instance, REFERENCE_CATALOG)
    targetUIDs = [ref.targetUID for ref in
                  tool.getReferences(instance, self.relationship)]

    if value is None:
        value = ()

    if not isinstance(value, (ListType, TupleType)):
        value = value,
    elif not self.multiValued and len(value) > 1:
        raise ValueError, \
              "Multiple values given for single valued field %r" % self

    #convert objects to uids if necessary
    uids = []
    for v in value:
        if type(v) in STRING_TYPES:
            uids.append(v)
        else:
            uids.append(v.UID())
            
    add = [v for v in uids if v and v not in targetUIDs]
    sub = [t for t in targetUIDs if t not in uids]

    # tweak keyword arguments for addReference
    addRef_kw = kwargs.copy()
    addRef_kw.setdefault('referenceClass', self.referenceClass)
    if addRef_kw.has_key('schema'): del addRef_kw['schema']

    #
    # MONKEY: Alway delete all references 
    # and recreate them to keep the order
    # 


    for uid in targetUIDs:
        tool.deleteReference(instance, uid, self.relationship)

    for uid in uids:
        __traceback_info__ = (instance, uid, value, targetUIDs)
        # throws IndexError if uid is invalid
        if uid != "":
            # Don't know what's the deal with the empty string
            tool.addReference(instance, uid, self.relationship, **addRef_kw)


    if self.callStorageOnSet:
        #if this option is set the reference fields's values get written
        #to the storage even if the reference field never use the storage
        #e.g. if i want to store the reference UIDs into an SQL field
        ObjectField.set(self, instance, self.getRaw(instance), **kwargs)


ReferenceField.set = set