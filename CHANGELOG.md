# Changelog

## 0.1.1
- Request validation for params and JSON bodies.
- Request body JSON sniffing without content type.
- Response validation improvements (status-class selection, empty-body handling).
- Error grouping with fix hints.
- Demo mode limits and simple license check.
- HTML report demo banner and license status output.
- CLI: `--license-status`, `--license-json`, and `--report` default name.
- Performance: validator and schema caching.
- Packaging: PyInstaller improvements and bundled docs.

## 0.1.0
- Initial MVP release.
- OpenAPI JSON/YAML parsing with local `$ref` resolution.
- Traffic ingestion for HAR, curl logs, and normalized JSON.
- Response validation with JSON schema matching and status-class support.
- HTML report output.
- PyInstaller packaging support.
