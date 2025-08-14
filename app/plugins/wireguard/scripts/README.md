# Scripts

### wg_to_firewallo
gets data from wg-portal DB (SQLite) and prepare rules inside firewallo file (must be `/etc/firewallo/filter/vpns2lan`)
it replaces the content between `# autowg start` and `# autowg stop`
to do:
- if user has permission to reach firewall also open traffic from vpns2fw (admin)


### wg_restart_service
check if wg-portal DB is younger (get the modify date) campared to wg-quick, if so restart wg-quick
to do:
- firewallo rule reload
