# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0-alpha.1] - 2025-10-04

### Added
- Initial alpha release
- Email-based passwordless authentication
- BIP-39 mnemonic verification codes
- Multi-language support (9 languages)
- JWT token authentication
- In-memory storage implementation
- Redis storage for verification codes
- Rate limiting and attempt tracking
- Configurable via environment variables
- FastAPI router with ready-to-use endpoints
- Comprehensive test suite

### Coming Soon
- PostgreSQL user storage implementation
- More documentation and examples
- Additional storage backends

### Known Limitations
- User storage currently only supports in-memory (custom implementations can be used via interfaces)
