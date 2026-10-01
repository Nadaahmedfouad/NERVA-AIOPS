# Mocks

<!--
WHY THIS FOLDER EXISTS
======================
Mocks let members work IN PARALLEL.

Example:
M4 needs RCAResult but M3 is not ready.

M4 reads:
mock_rca_response.json

Later the mock provider is replaced with the real M3 endpoint.

RULE:
Mocks must match the real canonical schema.

NOTE ABOUT .jsonc FILES
-----------------------
The `.json` files are machine-readable and should stay valid JSON.
JSON does not officially support comments.

Therefore this educational repo contains matching `.jsonc` files where comments explain each field.
Use `.json` in the application/tests.
Read `.jsonc` while learning.
-->
