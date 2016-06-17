# Contributing to ursula-monitoring

## collectd_plugins:

These are not currently in development or supported.  Your Mileage may Vary

## sensu_modules:

All checks ( but not metrics ) should have a configurable criticality ( `--criticality warning|critical` ) which drives the exit code of the alert to match sensu's expected exit code.   See existing checks for examples.

All metrics should at the very least contain a configurable scheme ( `--scheme blah.here.com` ) to help the user keep their graphite clean.
