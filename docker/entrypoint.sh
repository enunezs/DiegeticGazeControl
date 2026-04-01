#!/bin/bash
# Set the umask so new files are group-writable
umask 0002
# Run the main command
exec "$@"