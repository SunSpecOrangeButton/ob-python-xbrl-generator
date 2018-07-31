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

# key is what the field is called by the user; value is what it's called in OB
EXAMPLE_CONCEPT_MAP = {"latitude": "SiteLatitudeAtSystemEntrance",
                       "longitude": "SiteLongitudeAtSystemEntrance",
                       "azimuth": "OrientationAzimuth",
                       "tilt": "OrientationTilt",
                       "panel_manufacturer": "ProductManufacturer",
                       "panel_model": "Model",
                       "capacity_dc_kw": "ModuleNameplateCapacity",
                       "capacity_ac_kw": "InverterOutputRatedPowerAC",
                       "inverter_manufacturer": "ProductManufacturer",
                       "inverter_model": "Model", # can i use this for both?
                       "installer": "SystemInstallerCompany",
                       "COD": "SystemCommercialOperationsDate"}
