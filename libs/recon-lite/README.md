# ReCoN Lite Core

Dependency-light Request-Confirmation Network core.

This package contains the reusable graph, executor, activation, logging, tracing,
and small example pieces that are intended to be copied into the standalone
`recon-lite` repository. Domain projects such as Hector/chess should depend on
this package rather than adding domain-specific imports to it.
