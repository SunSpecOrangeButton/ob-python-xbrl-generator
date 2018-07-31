import unittest
import datetime
import shutil
import urllib2
import os.path

from lxml import etree

from solar_document_types import SystemInstallationSheet
from solar_document_types import MonthlyOperatingReport

from orange_config import VALIDATION_TARGET_DIR, VALIDATION_API_URL
from unit_map import UNIT_MAP
from example_concept_map import EXAMPLE_CONCEPT_MAP


def pipe_to_arelle_server(xml_filename):
    # copy the file to the ixbrl directory
    shutil.copy2(xml_filename, os.path.join(VALIDATION_TARGET_DIR, "ixbrl"))

    # GET request to localhost:8080 where Arelle container is running:
    validation_url = "%s%s" % (VALIDATION_API_URL, xml_filename)
    result = urllib2.urlopen(validation_url)
    lines = result.readlines()
    tree = etree.fromstring( "\n".join(lines[1:]) ) # Skip blank line at beginning

    # Get text from all table cells:
    table_rows = [x.text for x in tree.iterdescendants() if 'td' in x.tag]
    table_rows = [x.strip("\n") for x in table_rows]
    return table_rows



class InstallationXBRLTest(unittest.TestCase):
    def setUp(self):
        self.temp_file = "test_output_installation.xml"

    def tearDown(self):
        pass

    def test_is_valid_xml(self):
        mySheet = SystemInstallationSheet(UNIT_MAP, EXAMPLE_CONCEPT_MAP)
        mySheet.addSystem(1, {"installer": "These guys I know",
                              "COD": "2018-01-21"})
        mySheet.addSite(1, {"latitude": 42, "longitude": -170})
        mySheet.addArray(1, {"tilt": 20, "azimuth": 180,
                             "capacity_dc_kw": 4.5,
                             "panel_manufacturer": "Hanwha",
                             "panel_model": "ROYGBIV"})
        mySheet.addArray(1, {"tilt": 20, "azimuth": 180,
                             "capacity_dc_kw": 5.5,
                             "panel_manufacturer": "Kyocera",
                             "panel_model": "MST3K"})
        mySheet.addInverter(1, {"capacity_ac_kw": 8.0,
                                "inverter_manufacturer": "Enphase",
                                "inverter_model": "THX1138"})
        mySheet.toXML(self.temp_file)

        table_rows = pipe_to_arelle_server(self.temp_file)
        for row in table_rows:
            print row




class MonthlyOperatingReportXBRLTest(unittest.TestCase):
    def setUp(self):
        self.temp_file = "test_output_report.xml"

    def tearDown(self):
        pass

    def test_is_valid_xml(self):
        myReport = MonthlyOperatingReport()
        myReport.addData("sys1", datetime.date(2018, 1, 1), 1000, 1000)
        myReport.addData("sys1", datetime.date(2018, 2, 1), 1000, 1000)
        myReport.addData("sys2", datetime.date(2018, 1, 1), 1000, 1000)
        myReport.addData("sys2", datetime.date(2018, 2, 1), 1000, 1000)

        myReport.toXML(self.temp_file)

        table_rows = pipe_to_arelle_server(self.temp_file)
        for row in table_rows:
            print row



if __name__ == '__main__':
    unittest.main()
