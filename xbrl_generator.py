# Copyright 2018 kWh Analytics

# Licensed under the Apache License, Version 2.0 (the "License");
# pyou may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import xml.etree.ElementTree
from xml.etree.ElementTree import Element, SubElement
import datetime
import json

class Context(object):
    """
    Represents a single XBRL Context, with entity, period (instant or duration)
    and extra custom dimensions depending on which Hypercube (table) it belongs
    to.
    """
    def __init__(self, cube, entity, duration=None, instant=None, extra_dimensions={}):
        # If neither is provided (both are None) then treat duration as Forever.
        # If duration is provided it should be a tuple of (start date, end date)

        self.hypercube = cube
        # LONGTERM TODO: Is there ever such a thing as a context without
        # a hypercube?
        self.id_scheme = "http://xbrl.org/entity/identification/scheme" #???
        self.duration = None
        self.instant = None

        if duration is not None and instant is not None:
            raise Exception("Context should have duration OR instant, not both")
        elif duration is None and instant is None:
            self.duration = "forever"
        elif duration is not None:
            if len(duration) != 2:
                raise Exception("If duration provided it must be tuple of (start,end)")
            self.duration = duration
        elif instant is not None:
            self.instant = instant

        self.entity_name = entity
        self.extra_dimensions = extra_dimensions

    def is_equal(self, entity, duration=None, instant=None, extra_dimensions={}):
        # True if my values are equal to the given values. Used to prevent us
        # from creating redundant duplicate contexts when we already have one
        # with the right values.
        if entity != self.entity_name:
            return False
        if len(extra_dimensions) != len(self.extra_dimensions):
            return False
        for dimension in extra_dimensions:
            if extra_dimensions[dimension] != self.extra_dimensions[dimension]:
                return False
        if duration is None and instant is None:
            if self.duration != "forever":
                return False
        elif duration is not None:
            if len(duration) != 2:
                raise Exception("If duration provided it must be tuple of (start,end)")
            if duration[0] != self.duration[0]:
                return False
            if duration[1] != self.duration[1]:
                return False
        elif instant is not None:
            if instant != self.instant:
                return False
        return True

    def set_id(self, new_id):
        self._id = new_id

    def get_id(self):
        return self._id

    def qualify(self, string):
        """
        Returns the given string prefixed with my namespace
        """
        namespace = self.hypercube.getNamespace()
        return "{}:{}".format(namespace, string)

    def toXML(self):
        # if neither prod_month nor instant is provided, then period will
        # be "forever"
        context = Element("context", attrib={"id": self.get_id()})
        entity = SubElement(context, "entity")
        identifier = SubElement(entity, "identifier",
                                attrib={"scheme": self.id_scheme})
        identifier.text = self.entity_name

        # Period (instant or duration):
        period = SubElement(context, "period")

        if self.duration == "forever":
            forever = SubElement(period, "forever")
        elif self.duration is not None:
            startDate = SubElement(period, "startDate")
            startDate.text = self.duration[0].strftime("%Y-%m-%d")
            endDate = SubElement(period, "endDate")
            endDate.text = self.duration[1].strftime("%Y-%m-%d")
        elif self.instant is not None:
            instant_elem = SubElement(period, "instant")
            instant_elem.text = self.instant.strftime("%Y-%m-%d")


        # Extra dimensions:
        if len(self.extra_dimensions) > 0:
            segmentElem = SubElement(entity, "segment")

        for dimension in self.extra_dimensions.keys():
            # First figure out if dimension is typed or untyped:

            if self.hypercube.isTypedDimension(dimension):
            #if dimension in self.typedDimensionDomains:
                typedMember = SubElement(
                    segmentElem, "xbrldi:typedMember",
                    attrib = {"dimension": self.qualify(dimension)})
                domainElem = self.qualify(self.hypercube.getDomain(dimension))
                #domainElem = self.qualify( self.typedDimensionDomains[dimension] )
                domain = SubElement(typedMember, domainElem)
                domain.text = str(self.extra_dimensions[dimension])

            else:
                # if it's not one of the above, then it's an explicit dimension:
                explicit = SubElement(segmentElem, "xbrldi:explicitMember", attrib={
                    "dimension": self.qualify(dimension)
                    })
                explicit.text = self.qualify(str(self.extra_dimensions[dimension]))
        return context

    def toJSON(self):
        """
        Returns context's entity, period, and extra dimensions as JSON dictionary
        object.
        """
        aspects = {"xbrl:entity": self.entity_name}
        if self.duration == "forever":
            aspects["xbrl:period"] = "forever" # TODO is this right syntax???
        elif self.duration is not None:
            aspects["xbrl:periodStart"] = self.duration[0].strftime("%Y-%m-%d")
            aspects["xbrl:periodEnd"] = self.duration[1].strftime("%Y-%m-%d")
        elif self.instant is not None:
            aspects["xbrl:instant"] = self.instant.strftime("%Y-%m-%d")
            # TODO is this the right syntax???

        for dimension in self.extra_dimensions.keys():
            # TODO is there a difference in how typed axes vs explicit axes
            # are represented in JSON?
            if self.hypercube.isTypedDimension(dimension):
            #if dimension in self.typedDimensionDomains:
                value_str = self.extra_dimensions[dimension]
            else:
                value_str = self.qualify( self.extra_dimensions[dimension] )
            aspects[self.qualify(dimension)] = value_str

        return aspects


class Hypercube(object):
    """
    Abstractly represents an XBRL Hypercube (fancy name for a table)
    Will internally generate and save the contexts needed for the facts.
    Can turn itself into a list of XML Context tags for export.
    """
    def __init__(self, namespace, tableName, entity, typedDimensionDomains):
        # typedDimensionDomains is a dictionary mapping dimension names
        # to domain names for every dimension that is typed.
        self.namespace = namespace
        self.tableName = tableName
        self.entity = entity
        self.contexts = []
        self.typedDimensionDomains = typedDimensionDomains

    def get_context(self, duration=None, instant=None, extra_dimensions={}):
        # If we already made a context for this, return its ID.
        # Otherwise, create a context, store it, and return new context ID.
        for context in self.contexts:
            # It's not strictly necessary to compare entities right now because
            # all contexts in the same cube will necessarily have the same
            # entity, however in the future this may not be true(?)
            if context.is_equal(self.entity, duration, instant, extra_dimensions):
                return context
        new_context = Context(self, self.entity, duration, instant, extra_dimensions)
        # For the ID, just use "HypercubeName_serialNumber":
        new_id = "%s_%d" % (self.tableName, len(self.contexts))
        new_context.set_id(new_id)
        self.contexts.append(new_context)
        return new_context

    def toXML(self):
        return [context.toXML() for context in self.contexts]

    def getNamespace(self):
        return self.namespace

    def isTypedDimension(self, dimensionName):
        return (dimensionName in self.typedDimensionDomains)

    def getDomain(self, dimensionName):
        return self.typedDimensionDomains[dimensionName]


class Fact(object):
    """
    Represents an XBRL Fact, linked to a context, that can be exported
    as either XML or JSON.
    """
    def __init__(self, concept, context, units, value, decimals=2):
        """
        Concept is the field name - it must match the schema definition.
        Context is a reference to this fact's parent Context object.
        Units is a string naming the unit, for example "kWh"
        Value is a string, integer, or float
        Decimals is used only for float types, it is the number of
        digits 
        """
        # in case of xml the context ID will be rendered in the fact tag.
        # in case of json the contexts' attributes will be copied to the
        # fact's aspects.
        self.concept = concept
        self.value = value
        self.context = context
        self.units = units
        self.decimals = decimals

    def qualify(self, string):
        """
        Returns the given string prefixed with my context's namespace
        """
        return self.context.qualify(string)

    def toXML(self):
        """
        Return the Fact as an XML element.
        """
        attribs = {"contextRef": self.context.get_id()}
        if self.units is not None:
            attribs["unitRef"] = self.units
            if self.units == "pure" or self.units == "degrees":
                attribs["decimals"] = "0"
            else:
                attribs["decimals"] = str(self.decimals)
        elem = Element(self.qualify(self.concept), attrib=attribs)
        if self.units == "pure":
            elem.text = "%d" % self.value
        else:
            elem.text = str(self.value)
        return elem


    def toJSON(self):
        """
        Return the Fact as a JSON dictionary object
        """
        aspects = self.context.toJSON()
        aspects["xbrl:concept"] = self.qualify( self.concept )
        if self.units is not None:
            aspects["xbrl:unit"] = self.units

        if isinstance( self.value, datetime.datetime):
            value_str = self.value.strftime("%Y-%m-%d")
        else:
            value_str = str(self.value)
        return { "aspects": aspects,
                 "value": value_str}


class AbstractXBRLInstance(object):
    """
    Abstract base class for all XBRL instances. Subclass this to create an
    instance document for a specific reporting purpose. Can export itself
    as either XML or JSON.
    """
    def __init__(self, taxonomy, extra_ns={}, entity_name = "Unspecified"):

        # Note that these namespace URLs do not necessarily resolve to
        # documents -- they may give 404s if you try to load them. They
        # are really just being used as globally unique IDs that happen
        # to have URL syntax.
        self.namespaces = {
            "xmlns": "http://www.xbrl.org/2003/instance",
            "xmlns:link": "http://www.xbrl.org/2003/linkbase",
            "xmlns:xlink": "http://www.w3.org/1999/xlink",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:units": "http://www.xbrl.org/2009/utr",
            "xmlns:xbrldi": "http://xbrl.org/2006/xbrldi"
        }
        self.namespaces.update(extra_ns)
        self.entity_name = entity_name
        # LONGTERM TODO currently assuming any instance file only ever has one
        # entity in it; this might not be true in the long run.

        # Link to where the taxonomy lives on the web, so that a validator
        # can follow the link to get the data needed for validation:
        self.taxonomy = taxonomy

        self.hypercubes = {} # key will be table name, value will be
        # instance of Hypercube class

    def getContext(self, tableName, duration=None, instant=None,
                     extra_dimensions={}):
        """
        Returns the Context object with the given attributes that is
        part of the given table. Creates the context if it doesn't exist
        yet.
        """
        # Find the hypercube matching the table name, or create one if it
        # doesn't exist yet:
        if tableName in self.hypercubes:
            cube = self.hypercubes[tableName]
        else:
            domainMap = self.getTypedDimensionDomains()
            ns = self.getNamespacePrefix()
            cube = Hypercube(ns, tableName, self.entity_name, domainMap)
            self.hypercubes[tableName] = cube
        # ask the matching hypercube for the right context:
        return cube.get_context(duration, instant, extra_dimensions)

    def makeUnitTag(self, unit_id):
        """
        Return a unit tag (physics units such as kw, kwh, etc). Facts can
        reference this unit tag.
        """
        # See http://www.xbrl.org/utr/utr.xml
        unit = Element("unit", attrib={"id": unit_id})
        measure = SubElement(unit, "measure")
        measure.text = "units:{}".format(unit_id)
        # because http://www.xbrl.org/2009/utr is included as xmlns:units

        return unit

    def getTypedDimensionDomains(self):
        """
        Return a dictionary mapping names of dimensions to names of their
        domains for all *typed* dimensions that we plan on using. Override
        me in a subclass to define the typed dimensions you need.
        """
        return {}

    def get_required_units(self):
        """
        Return a list of unit names required by the instance
        document. Override me in subclass to define your needs.
        """
        return []

    def get_facts(self):
        """
        Return a list of element tags, one for each fact. Override me
        in subclass to create your instance document.
        """
        return []

    def toXMLTag(self):
        # The root element:
        xbrl = Element("xbrl", attrib = self.namespaces)

        # Add "link:schemaRef" for the taxonomy that goes with this document:
        link = SubElement(xbrl, "link:schemaRef",
                          attrib = {"xlink:href": self.taxonomy,
                                    "xlink:type": "simple"})

        # Generate facts first (even though they'll go last in the document)
        # because creating the facts will create the needed contexts as a
        # side-effect.
        facts = self.get_facts()

        # Add a context tag for each context we want to reference:
        for hypercube in self.hypercubes.values():
            tags = hypercube.toXML()
            for tag in tags:
                xbrl.append(tag)

        for unit in self.get_required_units():
            # Add a unit tag defining each unit we want to reference:
            xbrl.append(self.makeUnitTag(unit))

        for fact in self.get_facts():
            xbrl.append( fact.toXML() )

        return xbrl

    def toXML(self, filename):
        """
        Exports XBRL as XML to the given filename.
        """
        xbrl = self.toXMLTag()
        tree = xml.etree.ElementTree.ElementTree(xbrl)
        # Apparently every XML file should start with this, which ElementTree
        # doesn't do:
        # <?xml version="1.0" encoding="utf-8"?>
        tree.write(filename)

    def toXMLString(self):
        """
        Returns XBRL as an XML string
        """
        xbrl = self.toXMLTag()
        return xml.etree.ElementTree.tostring(xbrl).decode()


    def toJSON(self, filename):
        """
        Exports XBRL as JSON to the given filename.
        """

        outfile = open(filename, "w")
        outfile.write(self.toJSONString())
        outfile.close()

    def toJSONString(self):
        """
        Returns XBRL as a JSON string
        """
        masterJsonObj = {
            "documentType": "http://www.xbrl.org/WGWD/YYYY-MM-DD/xbrl-json",
            "prefixes": self.namespaces,
            "dtsReferences": [],
            "facts": []
            }

        masterJsonObj["dtsReferences"].append({
            "type": "schema",
            "href": self.taxonomy
        })

        facts = self.get_facts()

        for fact in facts:
            masterJsonObj["facts"].append( fact.toJSON() )
        return json.dumps(masterJsonObj)
