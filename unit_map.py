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


# Map of orange-button concept name to the name of the unit to use with that
# concept. In the future maybe this can be extracted automatically from the
# taxonomy XML instead of listed explicitly.

UNIT_MAP = {"OrientationTilt": "degrees",
            "OrientationAzimuth": "degrees",
            "ModuleNameplateCapacity": "kW",
            "InverterOutputRatedPowerAC": "kW",
            "SiteLatitudeAtSystemEntrance": "degrees",
            "SiteLongitudeAtSystemEntrance": "degrees",
            "DesignAttributePVDCCapacity": "kW",
            "DesignAttributePVACCapacity": "kW",
            "OrientationTilt": "degrees",
            "OrientationAzimuth": "degrees",
            "EquipmentTypeNumber": "pure"}
