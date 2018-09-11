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

from xbrl_generator import AbstractXBRLInstance, Fact
import datetime
import calendar

# TODO validate that the unit names we pass in are actually valid

class AbstractSolarXBRLInstance(AbstractXBRLInstance):
    """
    Subclass of AbstractXBRLInstance that specifies a few more solar-specific
    values such as namespace, taxonomy, and dimension-domain map. Concrete
    solar document classes should inherit from this one.
    """

    def __init__(self, entity_name = "Unspecified"):
        taxonomy = "https://raw.githubusercontent.com/xbrlus/solar/v1.2/core/solar_2018-03-31_r01.xsd"
        super( AbstractSolarXBRLInstance, self).__init__(
            taxonomy,
            extra_ns={"xmlns:solar": "http://xbrl.us/Solar/v1.2/2018-03-31/solar"},
            entity_name=entity_name)

    def getTypedDimensionDomains(self):
        # This needs to get passed into every new Hypercube that is instantiated
        return {
            "SolarSubArrayIdentifierAxis": "SolarSubArrayIdentifierDomain",
            "SiteIdentifierAxis": "SiteIdentifierDomain",
            "ProductIdentifierAxis": "ProductIdentifierDomain",
            "PVSystemIdentifierAxis": "PVSystemIdentifierDomain"
            }

    def getNamespacePrefix(self):
        return "solar"


class SystemInstallationSheet(AbstractSolarXBRLInstance):
    """
    A document type containing metadata for one or more systems, each
    system located at a site and comprising one or more arrays.
    """

    def __init__(self, unit_map, concept_map, entity_name="A Company"):
        super(SystemInstallationSheet, self).__init__(entity_name)
        self.systems = {} # keyed by system id
        self.arrays = {}
        self.inverters = {}
        self.sites = {}
        self.required_units = []
        self.unit_map = unit_map
        self.concept_map = concept_map

    def lookUpUnit(self, concept):
        # TODO move this to base class, i think
        unit = self.unit_map.get(concept, None)
        if unit is None:
            return None
        if not unit in self.required_units:
            self.required_units.append(unit)
        return unit

    def convertNames(self, facts):
        renamed_facts = {}
        for key in facts:
            if not key in self.concept_map:
                raise Exception("No mapping for fact name {}".format(key))
            ob_name = self.concept_map[key]
            renamed_facts[ob_name] = facts[key]
        return renamed_facts


    def addSystem(self, systemid, facts):
        # facts must be a dictionary where key is (unqualified) solar
        # schema concept name, value is value.
        self.systems[systemid] = self.convertNames(facts)

    def addArray(self, systemid, facts):
        if not systemid in self.arrays:
            self.arrays[systemid] = []
        self.arrays[systemid].append(self.convertNames(facts))

    def addInverter(self, systemid, facts):
        if not systemid in self.inverters:
            self.inverters[systemid] = []
        self.inverters[systemid].append(self.convertNames(facts))

    def addSite(self, systemid, facts):
        for key in facts:
            if not key in self.concept_map:
                raise Exception("System got unknown fact name {}".format(key))
        self.sites[systemid] = self.convertNames(facts)

    def get_required_units(self):
        return self.required_units

    def get_facts(self):
        facts = []
        report_generation_date = datetime.date.today() # Used for Instant duration

        # there's both Azimuth and OrientationAzimuth??
        # note: should have number of modules in array times module nameplate capacity?
        # "??": "SolarArrayNumberOfPanelsInArray"
        # "??": "TrackerStyle"
        # "TypeOfDevice" which is enumerated: "ModuleMember", "InverterMember", "TransformerMember", etc.

        # There's a SiteIdentifier line item in PVSystemTable,
        # is that how we connect a site to a system?
        # (what's DeviceListing table? how's that different from ProductIdentifierTable?)

        for system_identifier, systemData in self.systems.items():
            if system_identifier in self.arrays:
                for array_num, array_data in enumerate( self.arrays[system_identifier]):
                    # Array tilt and azimuth go in the SolarArrayTable:
                    arrayContext = self.getContext(
                        "SolarArrayTable",
                        instant = report_generation_date,
                        extra_dimensions={
                            "PVSystemIdentifierAxis": system_identifier,
                            "SolarSubArrayIdentifierAxis": array_num,
                            "EquipmentTypeAxis": "ModuleMember"
                    })
                    # Array make, model, and capacity go in ProductIdentifierTable:
                    productContext = self.getContext(
                        "ProductIdentifierTable",
                        extra_dimensions={
                            "PVSystemIdentifierAxis": system_identifier,
                            # TODO: come up with a better product ID here
                            "ProductIdentifierAxis": "array_product_%d" % array_num,
                            "TestConditionAxis": "StandardTestConditionMember"
                        })

                    for fieldName in array_data:
                        if fieldName in ["OrientationTilt", "OrientationAzimuth"]:
                            context = arrayContext
                        else:
                            context = productContext
                        facts.append(Fact(fieldName,
                                        context,
                                        self.lookUpUnit(fieldName),
                                        array_data[fieldName]))
                        # could also add a fact that "TypeOfDevice" = "ModuleMember"
            else:
                print "Warning: No array data for {}".format(system_identifier)

            # Inverter make, model, and capacity go in ProductIdentifierTable:
            if system_identifier in self.inverters:
                for inv_num, inverter_data in enumerate(self.inverters[system_identifier]):
                    inverterContext = self.getContext(
                        "ProductIdentifierTable",
                        extra_dimensions={
                            "PVSystemIdentifierAxis": system_identifier,
                            # TODO: come up with a better product ID here
                            "ProductIdentifierAxis": "inverter_product_%d" % inv_num,
                            "TestConditionAxis": "StandardTestConditionMember"
                        })

                    for fieldName in inverter_data:
                        facts.append(Fact(fieldName,
                                        inverterContext,
                                        self.lookUpUnit(fieldName),
                                        inverter_data[fieldName]))
                    # could also add a fact that "TypeOfDevice" = "InverterMember"
            else:
                print "Warning: No inverter data for {}".format(system_identifier)

            # Latitude and Longitude go in the SiteIdentifierTable:
            siteId = "site for {}".format(system_identifier)
            siteData = self.sites[system_identifier]
            siteContext = self.getContext(
                "SiteIdentifierTable",
                extra_dimensions={
                    "SiteIdentifierAxis": siteId
                })
            for fieldName in siteData:
                facts.append(Fact(fieldName,
                                  siteContext,
                                  self.lookUpUnit(fieldName),
                                  siteData[fieldName]))

            # The link between the SiteIdentifierTable and the PVSystemTable is the the SiteIdentifierAxis (on the site table) and the SiteIdentifer (as a line item in the pv system table). The value of the SiteIdentifierAxis will be the same as the value of the SiteIdentifier fact. This link is not obvious. I was just speaking to Campbell about it. He is adding an "identification" relationship that will make this easier to see. You are correct, that you put the site identifier value in the SiteIdentifery line item.

            # Installer and COD go in the PVSystemTable:
            systemContext = self.getContext(
                "PVSystemTable",
                extra_dimensions={
                    "PVSystemIdentifierAxis": system_identifier
                    # do i need EstimationPeriodStartDateAxis?
                })
            # make a fact connecting the system to the site:
            facts.append(Fact("SiteIdentifier",
                              systemContext,
                              None,
                              siteId))
            for fieldName in systemData:
                facts.append(Fact(fieldName,
                                  systemContext,
                                  self.lookUpUnit(fieldName),
                                  systemData[fieldName]))

        return facts



class MonthlyOperatingReport(AbstractSolarXBRLInstance):
    """
    A very simple example document type which lists monthly
    energy production (actualkwh) versus energy expectation
    (expectedkwh) for one or more systems for one or more months.
    """
    # TODO use "100825 - Documents - Monthly Operating Report" ?
    def __init__(self, entity_name="A Company"):
        super(MonthlyOperatingReport, self).__init__(entity_name)
        self._data = []

    def addData(self, system_name, prod_month, actualkwh, expectedkwh):
        self._data.append({"system_name": system_name,
                           "prod_month": prod_month,
                           "actualkwh": actualkwh,
                           "expectedkwh": expectedkwh})

    def get_required_units(self):
        return ["kWh"]

    def get_facts(self):
        # Add an actual and an expected fact for each system-month:
        facts = []
        for record in self._data:
            system_name = record["system_name"]
            prod_month = record["prod_month"]
            start_of_month = datetime.date(year=prod_month.year,
                                           month=prod_month.month,
                                           day = 1)
            lastday = calendar.monthrange(prod_month.year, prod_month.month)[1]
            end_of_month = datetime.date(year=prod_month.year,
                                         month=prod_month.month,
                                         day = lastday)
            duration = (start_of_month, end_of_month)

            context = self.getContext(
                "SystemProductionTable",
                duration=(start_of_month, end_of_month),
                extra_dimensions = {
                    "PVSystemIdentifierAxis": system_name,
                    # TODO might need a PeriodAxis too?
                }
            )

            facts.append(Fact("MeasuredEnergy",
                              context,
                              "kWh",
                              record["actualkwh"]))
            facts.append(Fact("PredictedEnergyAtTheRevenueMeterDuration",
                              context,
                              "kWh",
                              record["expectedkwh"]))
        return facts

