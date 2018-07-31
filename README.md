# ob-python-xbrl-generator

This code is released under an Apache 2 license. See LICENSE.

Contact jonathan.xia@kwhanalytics.com with questions.

What's in this repo: `xbrl_generator.py` is a module that generates XBRL documents (XML or JSON
format). It is taxonomy-agnostic.

`solar_document_types.py ` is a higher-level module that subclasses `xbrl_generator` to generate specifically Orange Button solar taxonomy documents. Specific document formats are to be defined by subclassing `AbstractSolarXBRLInstance`.

So far, two example document formats are included:
* System install document (i.e. metadata)
* Monthly operating report (i.e. production)

I am hoping that the community can collaborate on creating a library of useful document format subclasses.

## Install Arelle validation server (docker container):

1. Install Docker:
https://www.docker.com/products/docker#/mac
https://www.docker.com/products/docker#/linux
https://www.docker.com/products/docker#/windows

2. `git clone https://github.com/seocahill/xbrl-validation-pipeline`


## Install dependencies and configure:

1. Make a virtual environment
2. `pip install -r requirements.txt`
3. `cp orange_config_template.py orange_config.py`
4. edit `orange_config.py` and set `VALIDATION_TARGET_DIR` to be the path to your local git checkout of `xbrl-validation-pipeline` (above). This is so that the tests know where to find the Arelle validation server.

## Run tests:

1. In one terminal window, `cd xbrl-validation-pipeline` and then run `docker-compose up`

2. In a second terminal window, cd to this directory and run `python test.py`

The docker container must be running, because the test suite pipes documents to it for validation. Also, you must have an active internet connection so that the validator can resolve URLs to orange button schema and taxonomy documents hosted online by xbrl.us, sunspec.org, etc.

## Example usage:

Try the following python snippet:

```
from solar_document_types import MonthlyOperatingReport
import datetime
report = MonthlyOperatingReport(entity_name = "My Awesome Solar Company")
report.addData( "12345", datetime.date.today(), 299, 300 )
report.addData( "54321", datetime.date.today(), 168, 250 )
report.toXMLString()
report.toJSONString()
```

## Reference documents:
https://sunspec.org/wp-content/uploads/2017/10/OrangeButtonTaxonomyGuide4.pdf
https://yeti1.corefiling.com/yeti/resources/yeti-gwt/Yeti.jsp#tax~(id~103*v~146)!con~(id~904236)!net~(a~1653*l~451)!lang~(code~en-us)!path~(g~28464*p~0)!rg~(rg~22*p~11)
https://xbrl.us/xbrl-taxonomy/2018-solar/
https://en.wikipedia.org/wiki/XBRL
http://frux.wikispaces.com/file/view/Chapter-14-UnderstandingAndUsingXBRLDimensions.pdf
http://www.xbrl.org/specification/dimensions/rec-2012-01-25/dimensions-rec-2006-09-18+corrected-errata-2012-01-25-clean.html
